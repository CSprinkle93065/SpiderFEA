"""
test_geometry.py
Geometry derivation and validation tests for SpiderFEA.
Ensures exact formula transcription fidelity per §4.4.
"""

import numpy as np
import pytest

from src.api import (
    create_design,
    recalculate_profile,
    validate_geometry,
    update_geometry_parameter,
    get_default_values,
)


# ---------------------------------------------------------------------------
# Default geometry verification
# ---------------------------------------------------------------------------

def test_default_values_match_definition():
    """Default SpiderDesign values must match §4.3 exactly."""
    d = get_default_values()
    assert d.D_inner_spider == 75.0
    assert d.L_inner_bond == 2.5
    assert d.D_outer_landing_ID == 110.0
    assert d.D_outer_landing_OD == 122.0
    assert d.h_inner == 7.0
    assert d.h_outer == 10.0
    assert d.t == 0.75
    assert d.theta_deg == 30.0
    assert d.n_peaks == 7


# ---------------------------------------------------------------------------
# Profile recalculation
# ---------------------------------------------------------------------------

def test_recalculate_profile_with_defaults():
    """Recalculating profile with default inputs yields a non-degenerate polygon."""
    d = create_design()
    d = recalculate_profile(d)
    assert len(d.profile_r) == len(d.profile_z)
    assert len(d.profile_r) > 4


def test_profile_has_no_degenerate_edges():
    """Profile polygon must not contain consecutive duplicate points (zero-length edges)."""
    d = create_design()
    d = recalculate_profile(d)
    assert len(d.profile_r) == len(d.profile_z)
    for i in range(len(d.profile_r) - 1):
        r1, z1 = d.profile_r[i], d.profile_z[i]
        r2, z2 = d.profile_r[i + 1], d.profile_z[i + 1]
        assert not (abs(r1 - r2) < 1e-12 and abs(z1 - z2) < 1e-12), \
            f"Degenerate edge at index {i}: ({r1}, {z1}) == ({r2}, {z2})"


def test_recalculate_profile_reference_tolerance():
    """Default inputs must match reference spider_profile.py outputs to 1e-9."""
    d = create_design()
    d = recalculate_profile(d)
    # Reference values computed from exact formulas in §4.4:
    theta = np.radians(30.0)
    R_inner_spider = 75.0 / 2.0
    R_inner_corr = R_inner_spider + 2.5 * np.cos(theta)
    z_inner_cone = -2.5 * np.sin(theta)

    assert d.R_inner_spider == pytest.approx(R_inner_spider, abs=1e-9)
    assert d.R_inner_corr == pytest.approx(R_inner_corr, abs=1e-9)
    assert d.z_inner_cone == pytest.approx(z_inner_cone, abs=1e-9)


# ---------------------------------------------------------------------------
# Geometry parameter updates
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "field_name,value",
    [
        ("D_inner_spider", 80.0),
        ("L_inner_bond", 3.0),
        ("D_outer_landing_ID", 115.0),
        ("D_outer_landing_OD", 125.0),
        ("h_inner", 8.0),
        ("h_outer", 12.0),
        ("t", 1.0),
    ],
)
def test_update_geometry_parameter_updates_field(field_name, value):
    d = create_design()
    d = update_geometry_parameter(d, field_name, value)
    assert getattr(d, field_name) == value
    assert len(d.profile_r) > 0
    assert len(d.profile_z) > 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "mutation,expected_msg_fragment",
    [
        (lambda d: setattr(d, "D_outer_landing_OD", d.D_outer_landing_ID - 1), "OD"),
        (lambda d: setattr(d, "D_outer_landing_ID", d.D_inner_spider - 1), "ID"),
        (lambda d: setattr(d, "h_inner", -1.0), "h_inner"),
        (lambda d: setattr(d, "h_outer", -1.0), "h_outer"),
        (lambda d: setattr(d, "t", 0.0), "thickness"),
    ],
)
def test_validate_geometry_detects_invalid(mutation, expected_msg_fragment):
    d = create_design()
    mutation(d)
    valid, msg = validate_geometry(d)
    assert valid is False
    assert isinstance(msg, str) and len(msg) > 0


def test_validate_geometry_n_peaks_must_be_odd():
    d = create_design()
    d.n_peaks = 8
    valid, msg = validate_geometry(d)
    assert valid is False


def test_validate_geometry_accepts_valid_custom_inputs():
    d = create_design()
    d = update_geometry_parameter(d, "D_inner_spider", 60.0)
    d = update_geometry_parameter(d, "h_inner", 5.0)
    valid, msg = validate_geometry(d)
    assert valid is True
    assert msg == ""
