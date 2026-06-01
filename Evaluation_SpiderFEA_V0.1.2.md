# SpiderFEA v0.1.2 Geometry Self-Intersection Analysis

**Date:** 2026-05-31  
**Version:** 0.1.2  
**Status:** ISSUE NOT RESOLVED — Implement Option D  

---

## 1. Problem

v0.1.2 correctly detects self-intersections but cannot generate a valid mesh for any tested parameter set. Two distinct failure modes exist:

| Type | Cause | Location | Detection |
|------|-------|----------|-----------|
| **A** | `half_t > R_curve_min` | Corrugation body | `check_spider_geometry_valid()` |
| **B** | C0 centerline + normal offset | Roll-to-landing junctions | `is_simple_polygon()` |

Type A is a physical constraint (thick material cannot follow tight bends). Type B is a geometric artifact: the centerline has slope discontinuities where the cone and extension meet the corrugation. The normal offset produces miter fold-backs on the upper surface and gaps on the lower surface.

**Evidence:**
- Default params (`h=7/10, t=0.75, n=7`): 9 intersections (8 Type A + 1 Type B)
- User params (`h=2/2, OD=130, LID=120`): **2 intersections, both Type B** (inner + outer junction)
- Lower surface gaps at junctions: 0.08–0.18 mm

---

## 2. Recommended Fix: Segment-Wise Offset with Corner Joins (Option D)

Offset the three geometric segments independently, then join with proper corner handling.

### 2.1 Algorithm

```
For each segment (cone, corrugation, extension):
    1. Compute inward offset  (lower surface): centerline + half_t * n_inward
    2. Compute outward offset (upper surface): centerline - half_t * n_inward

At each junction (cone↔corr, corr↔ext):
    Upper surface (outward):
        - Extend offset lines backward from junction
        - Use intersection as corner vertex → trims the miter
    Lower surface (inward):
        - Offset curves diverge at concave corners
        - Cap gap with circular arc of radius = half_t centered at junction
```

### 2.2 Inner Junction Detail

**Centerline:** Cone ends at `(R_inner_corr, 0)`, slope = `tan(30°) = 0.577`. Corrugation starts at same point, slope = `(h_inner/2)·π·n/L_corr`. With user params: slope ≈ 1.08.

**Current failure:**
- Upper: segment `upper_corr[1]→upper_corr[0]` crosses `upper_cone[97]→upper_cone[96]` at `(39.4284, 0.2964)`
- Lower: gap = 0.083 mm between `lower_cone[-1]` and `lower_corr[0]`

**Fix:**
- Upper: Extend `upper_cone` end-segment backward and `upper_corr` start-segment forward. Their intersection becomes the corner vertex. Discard the folded miter triangle.
- Lower: Connect `lower_cone[-1]` to `lower_corr[0]` with a circular arc of radius `half_t = 0.375 mm` centered at `(R_inner_corr, 0)`.

### 2.3 Outer Junction Detail

**Centerline:** Corrugation ends at `(R_outer_landing_ID, 0)`, slope = `-(h_outer/2)·π·n/L_corr`. Extension starts flat (slope = 0). With user params: slope ≈ -1.08.

**Current failure:**
- Upper: horizontal `upper_ext` segment crosses diagonal `upper_corr` segment at `(60.1637, 0.3750)`
- Lower: gap = 0.180 mm

**Fix:** Same pattern as inner junction — miter trim upper, arc-cap lower.

### 2.4 Implementation Sketch

```python
def offset_segment(r_seg, z_seg, half_t):
    """Compute inward and outward offsets for a single segment."""
    dr, dz = central_differences(r_seg, z_seg)
    length = np.sqrt(dr**2 + dz**2)
    nr_inward = dz / length
    nz_inward = -dr / length
    r_lo = r_seg + half_t * nr_inward
    z_lo = z_seg + half_t * nz_inward
    r_up = r_seg - half_t * nr_inward
    z_up = z_seg - half_t * nz_inward
    return (r_lo, z_lo), (r_up, z_up)

def line_intersection(p1, d1, p2, d2):
    """Return intersection of lines p1+t*d1 and p2+s*d2, or None."""
    det = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(det) < 1e-12:
        return None
    dp = p2 - p1
    t = (dp[0]*d2[1] - dp[1]*d2[0]) / det
    return p1 + t * d1

def join_upper_miter(r_up_a, z_up_a, r_up_b, z_up_b):
    """Extend offset lines backward from junction; return intersection vertex."""
    p1 = np.array([r_up_a[-2], z_up_a[-2]])
    d1 = np.array([r_up_a[-1] - r_up_a[-2], z_up_a[-1] - z_up_a[-2]])
    p2 = np.array([r_up_b[1], z_up_b[1]])
    d2 = np.array([r_up_b[0] - r_up_b[1], z_up_b[0] - z_up_b[1]])
    return line_intersection(p1, d1, p2, d2)

def cap_lower_arc(center_r, center_z, p_start, p_end, half_t, n_pts=8):
    """Generate circular arc of radius half_t from p_start to p_end."""
    a1 = math.atan2(p_start[1] - center_z, p_start[0] - center_r)
    a2 = math.atan2(p_end[1] - center_z, p_end[0] - center_r)
    angles = np.linspace(a1, a2, n_pts)
    return center_r + half_t * np.cos(angles), center_z + half_t * np.sin(angles)
```

**Assembly:**
1. Offset cone, corrugation, extension independently
2. Compute `P_up_inner = join_upper_miter(upper_cone, upper_corr)`
3. Compute `P_up_outer = join_upper_miter(upper_corr, upper_ext)`
4. Compute `P_lo_inner = join_lower...` or use arc cap
5. Build polygon: lower_cone → arc_inner → lower_corr → arc_outer → lower_ext → upper_ext → P_up_outer → upper_corr → P_up_inner → upper_cone

### 2.5 Why This Is the Right Approach

- The centerline C0 junctions are **physically correct** for a spider. The fix belongs in the offset algorithm, not the centerline.
- Standard CAD polyline offset uses exactly this method (miter trim + arc cap).
- No external dependencies.
- Type A intersections remain blocked by the existing curvature check.

---

## 3. Critical Observations

### 3.1 Default Parameters Are Unphysical

Default params (`h=7/10, t=0.75, n=7`) have `R_curve_min ≈ 0.127 mm` with `half_t = 0.375 mm`. **No offset method can produce a valid polygon from this centerline.** `check_spider_geometry_valid()` must continue to block these.

### 3.2 User Parameters Are Valid

User params (`h=2/2, OD=130, LID=120, t=0.75`) pass the curvature check. Only Type B junction artifacts prevent meshing. **With Option D, this parameter set should produce a valid mesh.**

### 3.3 Lower Surface Gaps Matter

Even if upper surface crossings are fixed, the lower surface gaps (0.08–0.18 mm) may cause Gmsh meshing artifacts. The arc-cap in Option D closes these gaps explicitly.

---

## 4. Verification Criteria

| Check | Pass Criteria |
|-------|--------------|
| User params mesh | `h=2/2, OD=130, LID=120, t=0.75` → `is_simple_polygon()` = 0 intersections, Gmsh mesh completes |
| Default params blocked | `h=7/10, t=0.75` → `check_spider_geometry_valid()` = False |
| Junction gaps | Lower surface gap at both junctions < 0.01 mm |
| No regression | All existing tests pass; timeout wrapper still functional |
