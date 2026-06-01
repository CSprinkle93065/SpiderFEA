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
    generate_mesh_with_timeout,
    convert_mesh_with_elmergrid,
    update_mesh_control,
)


@pytest.fixture
def design_with_profile():
    d = create_design()
    d.t = 0.1
    d.h_inner = 5.0
    d.h_outer = 5.0
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


def test_generate_mesh_initializes_gmsh_with_empty_list(design_with_profile, monkeypatch):
    """Bug fix: gmsh.initialize([]) prevents Gmsh from parsing parent's sys.argv."""
    mock_gmsh = MagicMock()
    monkeypatch.setattr("src.api.gmsh", mock_gmsh)
    generate_mesh(design_with_profile)
    mock_gmsh.initialize.assert_called_once_with([])


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
    """Real Gmsh mesh generation completes with safe geometry parameters."""
    try:
        import gmsh
    except ImportError:
        pytest.skip("Gmsh not installed")

    from src.geometry import check_spider_geometry_valid, is_simple_polygon
    from pathlib import Path
    import tempfile

    design = create_design()
    design.t = 0.1
    design.h_inner = 5.0
    design.h_outer = 5.0
    design = recalculate_profile(design)

    # Pre-flight check must pass
    valid, msg = check_spider_geometry_valid(design)
    assert valid, msg

    # Polygon must be simple
    is_simple, n_x = is_simple_polygon(design.profile_r, design.profile_z)
    assert is_simple, f"Self-intersections: {n_x}"

    # Mesh must complete within timeout
    design = generate_mesh_with_timeout(design, timeout_sec=30)

    assert design.mesh_generated is True

    # Mesh output must exist and be non-empty
    work_dir = Path(design.working_directory) if design.working_directory else Path(tempfile.gettempdir()) / "spiderfea"
    msh_path = work_dir / "spider.msh"
    assert msh_path.exists()
    assert msh_path.stat().st_size > 0


def test_generate_mesh_with_timeout_rejects_bad_geometry():
    """generate_mesh_with_timeout raises ValueError for self-intersecting polygons."""
    design = create_design()
    design.t = 0.75
    design.h_inner = 7.0
    design.h_outer = 10.0
    design = recalculate_profile(design)
    with pytest.raises(ValueError):
        generate_mesh_with_timeout(design, timeout_sec=5)


def test_generate_mesh_rejects_self_intersecting_polygon(monkeypatch):
    """generate_mesh raises ValueError when polygon self-intersects."""
    mock_gmsh = MagicMock()
    monkeypatch.setattr("src.api.gmsh", mock_gmsh)
    design = create_design()
    design.t = 0.75
    design.h_inner = 7.0
    design.h_outer = 10.0
    design = recalculate_profile(design)
    with pytest.raises(ValueError, match="self-intersection"):
        generate_mesh(design)


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
    design.t = 0.1
    design.h_inner = 5.0
    design.h_outer = 5.0
    design = recalculate_profile(design)

    with pytest.raises(RuntimeError):
        generate_mesh(design)

    assert mock_gmsh.finalize.called, "gmsh.finalize was not called after failure"


def test_generate_mesh_with_timeout_raises_when_worker_exits_without_result(design_with_profile, monkeypatch):
    """Bug fix: result_queue.get(timeout=5) must raise RuntimeError when child exits without result."""
    import queue

    mock_queue = MagicMock()
    mock_queue.get.side_effect = queue.Empty()

    mock_process = MagicMock()
    mock_process.is_alive.return_value = False
    mock_process.exitcode = 0

    mock_ctx = MagicMock()
    mock_ctx.Queue.return_value = mock_queue
    mock_ctx.Process.return_value = mock_process

    monkeypatch.setattr("multiprocessing.get_context", lambda name: mock_ctx)
    # Ensure gmsh is not None so we enter the multiprocessing path
    monkeypatch.setattr("src.api.gmsh", MagicMock())

    with pytest.raises(RuntimeError, match="Mesh generation worker did not return a result"):
        generate_mesh_with_timeout(design_with_profile, timeout_sec=30)
