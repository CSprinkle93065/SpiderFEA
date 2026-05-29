"""
test_simulation.py
Elmer simulation, SIF generation, and result parsing tests.
ElmerSolver is mocked; no external executable is required.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.api import (
    create_design,
    recalculate_profile,
    generate_elmer_sif,
    parse_simulation_results,
    run_simulation,
    update_material_property,
    update_mesh_control,
)


@pytest.fixture
def design_ready_for_simulation():
    d = create_design()
    d = recalculate_profile(d)
    d.mesh_generated = True
    d.simulation_complete = False
    d.youngs_modulus = 5000.0
    d.poissons_ratio = 0.35
    d.density = 1200.0
    return d


# ---------------------------------------------------------------------------
# SIF generation
# ---------------------------------------------------------------------------

def test_generate_elmer_sif_creates_file(design_ready_for_simulation, tmp_path):
    sif_path = generate_elmer_sif(design_ready_for_simulation, str(tmp_path))
    assert Path(sif_path).is_file()


def test_generate_elmer_sif_contains_solver_keyword(design_ready_for_simulation, tmp_path):
    sif_path = generate_elmer_sif(design_ready_for_simulation, str(tmp_path))
    content = Path(sif_path).read_text()
    assert "Solid Mechanics" in content


def test_generate_elmer_sif_contains_axisymmetric(design_ready_for_simulation, tmp_path):
    sif_path = generate_elmer_sif(design_ready_for_simulation, str(tmp_path))
    content = Path(sif_path).read_text()
    assert "Axisymmetric" in content or "Coordinate System = Axi Symmetric" in content


def test_generate_elmer_sif_contains_material_properties(design_ready_for_simulation, tmp_path):
    sif_path = generate_elmer_sif(design_ready_for_simulation, str(tmp_path))
    content = Path(sif_path).read_text()
    assert str(design_ready_for_simulation.youngs_modulus) in content or "Young" in content


# ---------------------------------------------------------------------------
# Result parsing
# ---------------------------------------------------------------------------

def test_parse_simulation_results_returns_all_keys(tmp_path):
    result = parse_simulation_results(str(tmp_path))
    required_keys = [
        "force_deflection_data",
        "compliance_data",
        "max_von_mises_stress",
        "max_strain",
        "strain_field_data",
        "stress_field_data",
    ]
    for key in required_keys:
        assert key in result


def test_parse_simulation_results_force_deflection_is_list_of_dicts(tmp_path):
    result = parse_simulation_results(str(tmp_path))
    fd = result.get("force_deflection_data", [])
    assert isinstance(fd, list)
    if len(fd) > 0:
        assert isinstance(fd[0], dict)
        assert "displacement_mm" in fd[0]
        assert "force_N" in fd[0]
        assert "direction" in fd[0]


def test_parse_simulation_results_compliance_is_list_of_dicts(tmp_path):
    result = parse_simulation_results(str(tmp_path))
    comp = result.get("compliance_data", [])
    assert isinstance(comp, list)
    if len(comp) > 0:
        assert isinstance(comp[0], dict)
        assert "displacement_mm" in comp[0]
        assert "compliance_mm_per_N" in comp[0]
        assert "direction" in comp[0]


# ---------------------------------------------------------------------------
# Full simulation run (mocked)
# ---------------------------------------------------------------------------

def test_run_simulation_without_mesh_raises():
    d = create_design()
    d.mesh_generated = False
    with pytest.raises(RuntimeError):
        run_simulation(d)


def test_run_simulation_mocked_success(design_ready_for_simulation, monkeypatch):
    mock_subprocess = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("src.api.subprocess.run", mock_subprocess)
    monkeypatch.setattr(
        "src.api.parse_simulation_results",
        lambda directory: {
            "force_deflection_data": [
                {"displacement_mm": 0.0, "force_N": 0.0, "direction": "inward"},
                {"displacement_mm": 1.0, "force_N": 5.0, "direction": "inward"},
                {"displacement_mm": 2.0, "force_N": 12.0, "direction": "inward"},
            ],
            "compliance_data": [
                {"displacement_mm": 1.0, "compliance_mm_per_N": 0.2, "direction": "inward"},
            ],
            "max_von_mises_stress": 200.0,
            "max_strain": 0.08,
            "strain_field_data": [(1.0, 0.0, 0.01)],
            "stress_field_data": [(1.0, 0.0, 50.0)],
        },
    )
    d = run_simulation(design_ready_for_simulation)
    assert d.simulation_complete is True
    assert d.max_von_mises_stress == 200.0
    assert d.max_strain == 0.08
    assert len(d.force_deflection_data) == 3


def test_run_simulation_sets_simulation_complete_true(design_ready_for_simulation, monkeypatch):
    mock_subprocess = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("src.api.subprocess.run", mock_subprocess)
    monkeypatch.setattr(
        "src.api.parse_simulation_results",
        lambda directory: {
            "force_deflection_data": [],
            "compliance_data": [],
            "max_von_mises_stress": 0.0,
            "max_strain": 0.0,
            "strain_field_data": [],
            "stress_field_data": [],
        },
    )
    d = run_simulation(design_ready_for_simulation)
    assert d.simulation_complete is True


def test_run_simulation_solver_failure_raises(design_ready_for_simulation, monkeypatch):
    mock_subprocess = MagicMock(return_value=MagicMock(returncode=1, stderr="Solver failed"))
    monkeypatch.setattr("src.api.subprocess.run", mock_subprocess)
    with pytest.raises(RuntimeError):
        run_simulation(design_ready_for_simulation)
