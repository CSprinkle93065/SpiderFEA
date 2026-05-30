"""
test_mesh.py
Mesh generation and ElmerGrid conversion tests for SpiderFEA.
Gmsh and ElmerGrid are mocked.
"""

from unittest.mock import MagicMock, patch, call

import pytest

from src.api import (
    create_design,
    recalculate_profile,
    generate_mesh,
    convert_mesh_with_elmergrid,
    update_mesh_control,
)


@pytest.fixture
def design_with_profile():
    d = create_design()
    d = recalculate_profile(d)
    return d


# ---------------------------------------------------------------------------
# Mesh generation
# ---------------------------------------------------------------------------

def test_generate_mesh_sets_flag(design_with_profile, monkeypatch):
    mock_gmsh = MagicMock()
    monkeypatch.setattr("src.api.gmsh", mock_gmsh)
    d = generate_mesh(design_with_profile)
    assert d.mesh_generated is True


def test_generate_mesh_calls_gmsh_api(design_with_profile, monkeypatch):
    mock_gmsh = MagicMock()
    monkeypatch.setattr("src.api.gmsh", mock_gmsh)
    generate_mesh(design_with_profile)
    assert mock_gmsh.initialize.called or mock_gmsh.model.mesh.generate.called


def test_generate_mesh_without_profile_fails():
    d = create_design()
    # profile_r is empty by default before recalculation
    with pytest.raises((ValueError, RuntimeError)):
        generate_mesh(d)


# ---------------------------------------------------------------------------
# Mesh controls
# ---------------------------------------------------------------------------

def test_update_mesh_control_invalidates_simulation_state(design_with_profile):
    d = design_with_profile
    d.mesh_generated = True
    d.simulation_complete = True
    d = update_mesh_control(d, "global_element_size", 0.25)
    assert d.global_element_size == 0.25
    assert d.mesh_generated is False
    assert d.simulation_complete is False


def test_update_mesh_control_elements_through_thickness(design_with_profile):
    d = update_mesh_control(design_with_profile, "elements_through_thickness", 6)
    assert d.elements_through_thickness == 6
    assert d.mesh_generated is False


# ---------------------------------------------------------------------------
# ElmerGrid conversion
# ---------------------------------------------------------------------------

def test_convert_mesh_with_elmergrid_calls_subprocess(monkeypatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("src.api.subprocess.run", mock_run)
    convert_mesh_with_elmergrid("spider.msh", "mesh/")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert any("ElmerGrid" in str(arg) for arg in args)


def test_convert_mesh_with_elmergrid_raises_on_failure(monkeypatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=1, stderr="error"))
    monkeypatch.setattr("src.api.subprocess.run", mock_run)
    with pytest.raises(RuntimeError):
        convert_mesh_with_elmergrid("spider.msh", "mesh/")


def test_real_mesh_generation_completes():
    """Real Gmsh mesh generation completes with default geometry."""
    try:
        import gmsh
    except ImportError:
        pytest.skip("Gmsh not installed")

    design = create_design()
    design = recalculate_profile(design)

    # Reduce profile resolution for test speed (~2000 -> ~100 points)
    design.profile_r = design.profile_r[::20]
    design.profile_z = design.profile_z[::20]

    generate_mesh(design)

    assert design.mesh_generated is True


def test_gmsh_finalize_on_failure(monkeypatch):
    """gmsh.finalize() is called even when mesh generation fails mid-way."""
    mock_gmsh = MagicMock()
    mock_gmsh.initialize = MagicMock()
    call_count = [0]

    def failing_addPoint(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] > 2:
            raise RuntimeError("Simulated Gmsh failure")
        return call_count[0]

    mock_gmsh.model.geo.addPoint = failing_addPoint
    monkeypatch.setattr("src.api.gmsh", mock_gmsh)

    design = create_design()
    design = recalculate_profile(design)

    with pytest.raises(RuntimeError):
        generate_mesh(design)

    assert mock_gmsh.finalize.called, "gmsh.finalize was not called after failure"
