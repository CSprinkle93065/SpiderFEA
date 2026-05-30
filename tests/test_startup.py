"""
test_startup.py
Import chain, API surface, and MainWindow construction tests for SpiderFEA.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


# ---------------------------------------------------------------------------
# 1. Import chain tests
# ---------------------------------------------------------------------------

def test_api_module_imports():
    """All public symbols from src.api can be imported without error."""
    from src.api import (
        create_design,
        save_design,
        load_design,
        list_designs,
        delete_design,
        clone_design,
        update_geometry_parameter,
        recalculate_profile,
        validate_geometry,
        update_material_property,
        list_available_spider_materials,
        update_mesh_control,
        generate_mesh,
        convert_mesh_with_elmergrid,
        run_simulation,
        generate_elmer_sif,
        parse_simulation_results,
        export_cross_section_png,
        export_force_deflection_csv,
        export_compliance_csv,
        export_results_json,
        export_database,
        import_database,
        init_database,
        set_elmer_solver_path,
        set_elmergrid_path,
        set_working_directory,
        get_default_values,
    )
    assert callable(create_design)
    assert callable(save_design)
    assert callable(load_design)
    assert callable(list_designs)
    assert callable(delete_design)
    assert callable(clone_design)
    assert callable(update_geometry_parameter)
    assert callable(recalculate_profile)
    assert callable(validate_geometry)
    assert callable(update_material_property)
    assert callable(list_available_spider_materials)
    assert callable(update_mesh_control)
    assert callable(generate_mesh)
    assert callable(convert_mesh_with_elmergrid)
    assert callable(run_simulation)
    assert callable(generate_elmer_sif)
    assert callable(parse_simulation_results)
    assert callable(export_cross_section_png)
    assert callable(export_force_deflection_csv)
    assert callable(export_compliance_csv)
    assert callable(export_results_json)
    assert callable(export_database)
    assert callable(import_database)
    assert callable(init_database)
    assert callable(set_elmer_solver_path)
    assert callable(set_elmergrid_path)
    assert callable(set_working_directory)
    assert callable(get_default_values)


def test_spider_design_dataclass_imports():
    """SpiderDesign dataclass is importable."""
    from src.api import SpiderDesign
    assert hasattr(SpiderDesign, "D_inner_spider")
    assert hasattr(SpiderDesign, "profile_r")
    assert hasattr(SpiderDesign, "mesh_generated")
    assert hasattr(SpiderDesign, "simulation_complete")


# ---------------------------------------------------------------------------
# 2. MainWindow construction
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def qt_app():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_main_window_constructs(qt_app):
    """MainWindow instantiates without exception."""
    from src.main_window import MainWindow
    window = MainWindow()
    assert window is not None
    window.close()


def test_main_window_title(qt_app):
    """MainWindow title contains 'SpiderFEA'."""
    from src.main_window import MainWindow
    window = MainWindow()
    assert "SpiderFEA" in window.windowTitle()
    window.close()


def test_api_public_surface():
    """src.api.__all__ symbols must all exist."""
    import src.api
    missing = [name for name in src.api.__all__ if not hasattr(src.api, name)]
    assert not missing, f"src.api is missing: {missing}"


def test_all_buttons_clickable(qt_app):
    """Every QPushButton in MainWindow must accept a click without raising."""
    from unittest.mock import MagicMock
    from PyQt6.QtTest import QTest
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtWidgets import QPushButton, QDialog, QMessageBox, QApplication
    from src.main_window import MainWindow
    import src.api as _api
    import subprocess

    # Prevent actual Gmsh/Elmer from running during button sweep
    orig_gmsh = getattr(_api, 'gmsh', None)
    orig_subprocess_run = subprocess.run
    _api.gmsh = MagicMock()
    subprocess.run = MagicMock(return_value=MagicMock(returncode=0))

    try:
        window = MainWindow()
        buttons = window.findChildren(QPushButton)
        assert buttons, "No QPushButtons found in MainWindow"

        def _dismiss_dialogs():
            for dlg in window.findChildren(QDialog):
                dlg.reject()
            for top in QApplication.topLevelWidgets():
                if isinstance(top, (QDialog, QMessageBox)):
                    top.reject()

        for btn in buttons:
            QTimer.singleShot(200, _dismiss_dialogs)
            QTest.mouseClick(btn, Qt.MouseButton.LeftButton)

        window.close()
    finally:
        _api.gmsh = orig_gmsh
        subprocess.run = orig_subprocess_run
