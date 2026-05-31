"""
SpiderFEA — Geometry Engine

Parametric 2D axisymmetric r-z cross-section of a loudspeaker spider.
All formulas are implemented exactly as specified in SpiderGeomContext.md
and definition.md Section 4.4.
"""

from __future__ import annotations

import numpy as np
import math
from math import cos, sin, radians, sqrt, pi

from src.models import SpiderDesign


def recalculate_profile(design: SpiderDesign) -> SpiderDesign:
    """
    Recompute the full 2D profile polygon from the 7 control inputs.

    Formulas are transcribed character-for-character from the canonical
    specification (definition.md §4.4 and SpiderGeomContext.md).
    """
    # Unpack control parameters
    D_inner_spider = design.D_inner_spider
    L_inner_bond = design.L_inner_bond
    D_outer_landing_ID = design.D_outer_landing_ID
    D_outer_landing_OD = design.D_outer_landing_OD
    h_inner = design.h_inner
    h_outer = design.h_outer
    t = design.t
    theta_deg = design.theta_deg
    n_peaks = design.n_peaks

    theta = radians(theta_deg)

    # Radii from diameters
    R_inner_spider = D_inner_spider / 2.0
    R_outer_landing_ID = D_outer_landing_ID / 2.0
    R_outer_landing_OD = D_outer_landing_OD / 2.0

    # Inner cone
    R_inner_corr = R_inner_spider + L_inner_bond * cos(theta)
    z_inner_cone = -L_inner_bond * sin(theta)

    # Outer extension
    extension = R_outer_landing_OD - R_outer_landing_ID

    # Store derived parameters on design
    design.R_inner_spider = float(R_inner_spider)
    design.R_outer_landing_ID = float(R_outer_landing_ID)
    design.R_outer_landing_OD = float(R_outer_landing_OD)
    design.R_inner_corr = float(R_inner_corr)
    design.z_inner_cone = float(z_inner_cone)
    design.extension = float(extension)

    # Discretization
    n_pts_cone = 100
    n_pts_corr = 800
    n_pts_ext = 100

    # Inner cone centerline
    r_cone = np.linspace(R_inner_spider, R_inner_corr, n_pts_cone)
    z_cone = np.tan(theta) * (r_cone - R_inner_spider) + z_inner_cone

    # Corrugation centerline
    r_corr = np.linspace(R_inner_corr, R_outer_landing_ID, n_pts_corr)
    phase = pi * n_peaks * (r_corr - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
    h = h_inner + (h_outer - h_inner) * (r_corr - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
    z_corr = (h / 2) * np.sin(phase)

    # Outer extension centerline
    r_ext = np.linspace(R_outer_landing_ID, R_outer_landing_OD, n_pts_ext)
    z_ext = np.zeros_like(r_ext)

    # Concatenate centerline
    r_center = np.concatenate([r_cone, r_corr[1:], r_ext[1:]])
    z_center = np.concatenate([z_cone, z_corr[1:], z_ext[1:]])

    # Normal thickness offset
    dr = np.zeros_like(r_center)
    dz = np.zeros_like(z_center)

    # Central differences
    dr[1:-1] = r_center[2:] - r_center[:-2]
    dz[1:-1] = z_center[2:] - z_center[:-2]
    # Endpoints
    dr[0] = r_center[1] - r_center[0]
    dz[0] = z_center[1] - z_center[0]
    dr[-1] = r_center[-1] - r_center[-2]
    dz[-1] = z_center[-1] - z_center[-2]

    # Unit inward normal = (dz, -dr) / len
    length = np.sqrt(dr**2 + dz**2)
    nr_inward = dz / length
    nz_inward = -dr / length

    # Offset surfaces
    half_t = t / 2.0
    r_lower = r_center + half_t * nr_inward
    z_lower = z_center + half_t * nz_inward
    r_upper = r_center - half_t * nr_inward
    z_upper = z_center - half_t * nz_inward

    # Build closed polygon
    profile_r: list[float] = []
    profile_z: list[float] = []
    profile_r.extend(r_lower.tolist())
    profile_z.extend(z_lower.tolist())
    profile_r.extend(r_upper[::-1].tolist())
    profile_z.extend(z_upper[::-1].tolist())

    design.profile_r = profile_r
    design.profile_z = profile_z

    return design


def validate_geometry(design: SpiderDesign) -> tuple[bool, str]:
    """
    Check whether current parameters produce a physically realizable geometry.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    if design.D_outer_landing_OD <= design.D_outer_landing_ID:
        return False, "Outer landing OD must be greater than ID."
    if design.D_outer_landing_ID <= design.D_inner_spider:
        return False, "Outer landing ID must be greater than spider ID."
    if design.h_inner <= 0:
        return False, "h_inner must be positive."
    if design.h_outer <= 0:
        return False, "h_outer must be positive."
    if design.t <= 0:
        return False, "Wall thickness must be positive."
    if design.n_peaks % 2 == 0:
        return False, "Number of peaks must be an odd positive integer."
    if design.n_peaks < 1:
        return False, "Number of peaks must be a positive integer."
    return True, ""


def check_spider_geometry_valid(design: SpiderDesign) -> tuple[bool, str]:
    """
    Returns (True, "") if geometry is expected to produce a simple polygon.
    Returns (False, reason) if parameters will cause self-intersection.
    """
    L = design.R_outer_landing_ID - design.R_inner_corr
    A = max(design.h_inner, design.h_outer) / 2.0
    n = design.n_peaks
    half_t = design.t / 2.0

    R_curve_min = (L ** 2) / (A * math.pi ** 2 * n ** 2)

    ratio = half_t / R_curve_min
    if ratio >= 1.0:
        return False, (
            f"Thickness offset ({half_t:.3f} mm) exceeds minimum corrugation "
            f"radius of curvature ({R_curve_min:.3f} mm). "
            f"Reduce thickness, reduce amplitude, or increase peak count."
        )
    return True, ""


def _segments_intersect(
    r1: float, z1: float, r2: float, z2: float,
    r3: float, z3: float, r4: float, z4: float,
    eps: float = 1e-12,
) -> bool:
    """Return True if segments (r1,z1)-(r2,z2) and (r3,z3)-(r4,z4) intersect."""

    def _ccw(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> float:
        return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)

    def _on_segment(
        ax: float, ay: float, bx: float, by: float, cx: float, cy: float,
    ) -> bool:
        return (
            min(ax, bx) - eps <= cx <= max(ax, bx) + eps
            and min(ay, by) - eps <= cy <= max(ay, by) + eps
        )

    d1 = _ccw(r3, z3, r4, z4, r1, z1)
    d2 = _ccw(r3, z3, r4, z4, r2, z2)
    d3 = _ccw(r1, z1, r2, z2, r3, z3)
    d4 = _ccw(r1, z1, r2, z2, r4, z4)

    if (
        ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps))
        and ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps))
    ):
        return True

    if abs(d1) <= eps and _on_segment(r3, z3, r4, z4, r1, z1):
        return True
    if abs(d2) <= eps and _on_segment(r3, z3, r4, z4, r2, z2):
        return True
    if abs(d3) <= eps and _on_segment(r1, z1, r2, z2, r3, z3):
        return True
    if abs(d4) <= eps and _on_segment(r1, z1, r2, z2, r4, z4):
        return True

    return False


def is_simple_polygon(r: list[float], z: list[float]) -> tuple[bool, int]:
    """
    Returns (True, 0) if polygon has no self-intersections.
    Returns (False, N) if N self-intersections detected.
    """
    n = len(r)
    if n < 4:
        return True, 0

    count = 0
    for i in range(n):
        r1, z1 = r[i], z[i]
        r2, z2 = r[(i + 1) % n], z[(i + 1) % n]
        for j in range(i + 1, n):
            # Skip adjacent segments (sharing an endpoint)
            if j == i + 1:
                continue
            if i == 0 and j == n - 1:
                continue
            r3, z3 = r[j], z[j]
            r4, z4 = r[(j + 1) % n], z[(j + 1) % n]
            if _segments_intersect(r1, z1, r2, z2, r3, z3, r4, z4):
                count += 1

    return count == 0, count
