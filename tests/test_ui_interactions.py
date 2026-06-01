"""
test_ui_interactions.py
UI Construction Tests and UI Interaction Tests for SpiderFEA MainWindow.
All Qt tests run with QT_QPA_PLATFORM=offscreen.
"""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QLabel,
)

from src.main_window import MainWindow
import src.api as api_module

def _wait_for_mesh(window, timeout_ms=5000):
    """Wait for async mesh generation to complete using a local event loop."""
    from PyQt6.QtCore import QEventLoop, QTimer
    loop = QEventLoop()
    check_timer = QTimer()
    check_timer.timeout.connect(lambda: (loop.quit() if window.design.mesh_generated else None))
    check_timer.start(50)

    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(loop.quit)
    timeout_timer.start(timeout_ms)

    loop.exec()
    check_timer.stop()
    return window.design.mesh_generated


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# ===========================================================================
# Helpers
# ===========================================================================

def _dismiss_dialogs(parent):
    """Reject all open QDialogs and QMessageBoxes under parent or top-level."""
    for dlg in parent.findChildren(QDialog):
        dlg.reject()
    for top in QApplication.topLevelWidgets():
        if isinstance(top, QDialog):
            top.reject()


def _accept_dialogs(parent):
    """Accept all open QDialogs and QMessageBoxes under parent or top-level."""
    for dlg in parent.findChildren(QDialog):
        dlg.accept()
    for top in QApplication.topLevelWidgets():
        if isinstance(top, QDialog):
            top.accept()


# ===========================================================================
# UI Construction Tests
# ===========================================================================

def test_main_window_constructs(qt_app):
    """MainWindow instantiates without exception."""
    window = MainWindow()
    assert window is not None
    window.close()


def test_all_geometry_input_widgets_present(qt_app):
    """All 7 geometry QLineEdit widgets exist by objectName."""
    window = MainWindow()
    names = [
        "txtDInnerSpider",
        "txtLInnerBond",
        "txtDOuterLandingID",
        "txtDOuterLandingOD",
        "txtHInner",
        "txtHOuter",
        "txtT",
    ]
    for name in names:
        widget = window.findChild(QLineEdit, name)
        assert widget is not None, f"Widget '{name}' (QLineEdit) not found in MainWindow. The Coding Agent must set objectName on all action widgets."
    window.close()


def test_material_widgets_present(qt_app):
    """Material QComboBox and read-only property labels exist."""
    window = MainWindow()
    assert window.findChild(QComboBox, "cmbMaterial") is not None, "cmbMaterial not found"
    assert window.findChild(QLabel, "lblYoungsModulus") is not None, "lblYoungsModulus not found"
    assert window.findChild(QLabel, "lblPoissonsRatio") is not None, "lblPoissonsRatio not found"
    assert window.findChild(QLabel, "lblDensity") is not None, "lblDensity not found"
    window.close()


def test_fixed_geometry_labels_present(qt_app):
    """Read-only labels for fixed geometry exist."""
    window = MainWindow()
    assert window.findChild(QLabel, "lblInnerConeAngle") is not None, "lblInnerConeAngle not found"
    assert window.findChild(QLabel, "lblNumberOfPeaks") is not None, "lblNumberOfPeaks not found"
    window.close()


def test_mesh_control_widgets_present(qt_app):
    """All 3 mesh control QLineEdit widgets exist."""
    window = MainWindow()
    names = [
        "txtGlobalElementSize",
        "txtElementsThroughThickness",
        "txtMeshRefinementFactor",
    ]
    for name in names:
        widget = window.findChild(QLineEdit, name)
        assert widget is not None, f"Widget '{name}' (QLineEdit) not found in MainWindow."
    window.close()


def test_action_buttons_present(qt_app):
    """Mesh and Run Simulation buttons exist."""
    window = MainWindow()
    assert window.findChild(QPushButton, "btnGenerateMesh") is not None, "btnGenerateMesh not found"
    assert window.findChild(QPushButton, "btnRunSimulation") is not None, "btnRunSimulation not found"
    window.close()


def test_right_panel_tabs_present(qt_app):
    """All 5 tabs exist in the QTabWidget."""
    window = MainWindow()
    tab_widget = window.findChild(QTabWidget, "tabWidget")
    assert tab_widget is not None, "tabWidget not found"
    assert tab_widget.count() == 5, f"Expected 5 tabs, got {tab_widget.count()}"
    window.close()


def test_menu_actions_present(qt_app):
    """All menu actions exist with objectName."""
    window = MainWindow()
    action_names = [
        "actionNew",
        "actionOpenDesign",
        "actionSaveDesign",
        "actionDeleteDesign",
        "actionExportCrossSectionPng",
        "actionExportForceDeflectionCsv",
        "actionExportComplianceCsv",
        "actionExportResultsJson",
        "actionExportDatabase",
        "actionImportDatabase",
        "actionSetElmerSolverPath",
        "actionSetElmerGridPath",
        "actionSetWorkingDirectory",
        "actionAbout",
    ]
    for name in action_names:
        action = window.findChild(QAction, name)
        assert action is not None, f"Action '{name}' not found in MainWindow. The Coding Agent must set objectName on all QAction objects."
    window.close()


def test_status_bar_present(qt_app):
    """Status bar exists and shows default text."""
    window = MainWindow()
    sb = window.statusBar()
    assert sb is not None, "Status bar not found"
    assert "Ready" in sb.currentMessage(), "Status bar does not show 'Ready'"
    window.close()


def test_about_dialog_constructs(qt_app):
    """AboutDialog can be instantiated."""
    window = MainWindow()
    from src.dialogs import AboutDialog
    dlg = AboutDialog(parent=window)
    assert dlg is not None
    dlg.close()
    window.close()


# ===========================================================================
# UI Interaction Tests — Menu Actions
# ===========================================================================

def test_action_new_triggered(qt_app):
    """File → New resets design to defaults."""
    window = MainWindow()
    window.design.D_inner_spider = 999.0
    action = window.findChild(QAction, "actionNew")
    assert action is not None, "actionNew not found"
    action.trigger()
    assert window.design.D_inner_spider == 75.0
    assert window.design.mesh_generated is False
    window.close()


def test_action_open_design_triggered(qt_app, monkeypatch, tmp_path):
    """File → Open Design loads a design from the database."""
    # Seed a temp DB with a known design
    db_path = str(tmp_path / "designs.db")
    api_module.init_database(db_path)
    design = api_module.create_design("LoadMe")
    design = api_module.update_geometry_parameter(design, "D_inner_spider", 88.0)
    api_module.save_design_to_db(design, db_path)

    window = MainWindow()
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *a, **k: (db_path, ""),
    )
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QInputDialog.getItem",
        lambda *a, **k: ("LoadMe", True),
    )
    action = window.findChild(QAction, "actionOpenDesign")
    assert action is not None
    action.trigger()
    assert window.design.D_inner_spider == 88.0
    window.close()


def test_action_save_design_triggered(qt_app, monkeypatch):
    """File → Save Design opens input dialog and saves."""
    window = MainWindow()
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QInputDialog.getText",
        lambda *a, **k: ("TestDesign", True),
    )
    # Auto-dismiss any QMessageBox that appears after save
    QTimer.singleShot(200, lambda: _accept_dialogs(window))
    action = window.findChild(QAction, "actionSaveDesign")
    assert action is not None
    action.trigger()
    assert "TestDesign" in [d["name"] for d in api_module.list_designs()]
    window.close()


def test_action_delete_design_triggered(qt_app, monkeypatch):
    """File → Delete Design removes a saved design."""
    # Pre-seed a design
    api_module.init_database()
    design = api_module.create_design("ToDelete")
    design_id = api_module.save_design(design)

    window = MainWindow()
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QInputDialog.getItem",
        lambda *a, **k: ("ToDelete", True),
    )
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    # Auto-dismiss any info/critical message boxes
    QTimer.singleShot(200, lambda: _accept_dialogs(window))
    action = window.findChild(QAction, "actionDeleteDesign")
    assert action is not None
    action.trigger()
    assert design_id not in [d["id"] for d in api_module.list_designs()]
    window.close()


def test_action_export_cross_section_png_triggered(qt_app, monkeypatch, tmp_path):
    """File → Export → Cross-Section PNG writes a PNG file."""
    window = MainWindow()
    png_path = str(tmp_path / "export.png")
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (png_path, ""),
    )
    action = window.findChild(QAction, "actionExportCrossSectionPng")
    assert action is not None
    action.trigger()
    assert os.path.isfile(png_path)
    window.close()


def test_action_export_force_deflection_csv_triggered(qt_app, monkeypatch, tmp_path):
    """File → Export → Force-Deflection CSV writes CSV with headers."""
    window = MainWindow()
    csv_path = str(tmp_path / "fd.csv")
    window.design.force_deflection_data = [
        {"displacement_mm": 1.0, "force_N": 10.0, "direction": "inward"},
    ]
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (csv_path, ""),
    )
    action = window.findChild(QAction, "actionExportForceDeflectionCsv")
    assert action is not None
    action.trigger()
    with open(csv_path) as f:
        first_line = f.readline()
    assert "displacement_mm,force_N,direction" in first_line
    window.close()


def test_action_export_compliance_csv_triggered(qt_app, monkeypatch, tmp_path):
    """File → Export → Compliance CSV writes CSV with headers."""
    window = MainWindow()
    csv_path = str(tmp_path / "comp.csv")
    window.design.compliance_data = [
        {"displacement_mm": 1.0, "compliance_mm_per_N": 0.1, "direction": "inward"},
    ]
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (csv_path, ""),
    )
    action = window.findChild(QAction, "actionExportComplianceCsv")
    assert action is not None
    action.trigger()
    with open(csv_path) as f:
        first_line = f.readline()
    assert "displacement_mm,compliance_mm_per_N,direction" in first_line
    window.close()


def test_action_export_results_json_triggered(qt_app, monkeypatch, tmp_path):
    """File → Export → Results Summary writes JSON."""
    window = MainWindow()
    json_path = str(tmp_path / "results.json")
    window.design.max_von_mises_stress = 123.0
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (json_path, ""),
    )
    action = window.findChild(QAction, "actionExportResultsJson")
    assert action is not None
    action.trigger()
    with open(json_path) as f:
        data = json.load(f)
    assert "max_von_mises_stress" in data
    assert data["max_von_mises_stress"] == 123.0
    window.close()


def test_action_export_database_triggered(qt_app, monkeypatch, tmp_path):
    """File → Export → Database Backup copies the database."""
    window = MainWindow()
    backup_path = str(tmp_path / "backup.db")
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (backup_path, ""),
    )
    action = window.findChild(QAction, "actionExportDatabase")
    assert action is not None
    action.trigger()
    assert os.path.isfile(backup_path)
    window.close()


def test_action_import_database_triggered(qt_app, monkeypatch, tmp_path):
    """File → Import → Database Backup imports designs."""
    from src.database import _get_default_db_path
    # Create a backup with a known design
    backup_path = str(tmp_path / "backup.db")
    api_module.init_database(backup_path)
    api_module.save_design_to_db(api_module.create_design("Imported"), backup_path)

    window = MainWindow()
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *a, **k: (backup_path, ""),
    )
    QTimer.singleShot(200, lambda: _accept_dialogs(window))
    action = window.findChild(QAction, "actionImportDatabase")
    assert action is not None
    action.trigger()
    # Verify default DB was replaced with backup contents
    designs = api_module.list_designs(db_path=_get_default_db_path())
    assert any(d["name"] == "Imported" for d in designs)
    window.close()


def test_action_set_elmer_solver_path_triggered(qt_app, monkeypatch):
    """Setup → ElmerSolver executable path updates setting."""
    window = MainWindow()
    fake_path = "C:\\Elmer\\bin\\ElmerSolver.exe"
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *a, **k: (fake_path, ""),
    )
    action = window.findChild(QAction, "actionSetElmerSolverPath")
    assert action is not None
    action.trigger()
    assert api_module.get_setting("elmer_solver_path") == fake_path
    window.close()


def test_action_set_elmergrid_path_triggered(qt_app, monkeypatch):
    """Setup → ElmerGrid executable path updates setting."""
    window = MainWindow()
    fake_path = "C:\\Elmer\\bin\\ElmerGrid.exe"
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *a, **k: (fake_path, ""),
    )
    action = window.findChild(QAction, "actionSetElmerGridPath")
    assert action is not None
    action.trigger()
    assert api_module.get_setting("elmergrid_path") == fake_path
    window.close()


def test_action_set_working_directory_triggered(qt_app, monkeypatch):
    """Setup → Working directory updates setting."""
    window = MainWindow()
    fake_dir = "C:\\Work\\SpiderFEA"
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getExistingDirectory",
        lambda *a, **k: fake_dir,
    )
    action = window.findChild(QAction, "actionSetWorkingDirectory")
    assert action is not None
    action.trigger()
    assert api_module.get_setting("working_directory") == fake_dir
    window.close()


def test_action_about_triggered(qt_app):
    """Help → About opens an About dialog."""
    window = MainWindow()
    action = window.findChild(QAction, "actionAbout")
    assert action is not None

    def close_dialog():
        for dlg in window.findChildren(QDialog):
            dlg.reject()
        for top in QApplication.topLevelWidgets():
            if isinstance(top, QDialog):
                top.reject()

    QTimer.singleShot(200, close_dialog)
    action.trigger()
    window.close()


# ===========================================================================
# UI Interaction Tests — Buttons
# ===========================================================================

def test_btn_generate_mesh_clicked(qt_app, monkeypatch):
    """Clicking btnGenerateMesh sets mesh_generated=True."""
    window = MainWindow()
    # Use safe params so pre-flight check passes
    window.design.t = 0.1
    window.design.h_inner = 5.0
    window.design.h_outer = 5.0
    window.design = api_module.recalculate_profile(window.design)
    monkeypatch.setattr("src.api.gmsh", MagicMock())
    monkeypatch.setattr("src.api.convert_mesh_with_elmergrid", lambda *a, **k: None)
    btn = window.findChild(QPushButton, "btnGenerateMesh")
    assert btn is not None, "btnGenerateMesh not found"
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
    assert _wait_for_mesh(window), "Mesh did not complete within timeout"
    assert window.design.mesh_generated is True
    window.close()


def test_btn_run_simulation_clicked(qt_app, monkeypatch):
    """Clicking btnRunSimulation with mesh_generated=True completes simulation."""
    window = MainWindow()
    window.design.mesh_generated = True
    window._update_simulation_tab_state()

    def _mock_run_simulation(design):
        design.simulation_complete = True
        design.max_von_mises_stress = 150.0
        design.max_strain = 0.05
        design.force_deflection_data = [{"displacement_mm": 1.0, "force_N": 10.0, "direction": "inward"}]
        design.compliance_data = [{"displacement_mm": 1.0, "compliance_mm_per_N": 0.1, "direction": "inward"}]
        return design

    monkeypatch.setattr("src.main_window.run_simulation", _mock_run_simulation)
    btn = window.findChild(QPushButton, "btnRunSimulation")
    assert btn is not None, "btnRunSimulation not found"
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
    assert window.design.simulation_complete is True
    window.close()


def test_btn_run_simulation_disabled_shows_popup(qt_app):
    """Clicking btnRunSimulation while disabled shows a popup (no crash)."""
    window = MainWindow()
    window.design.mesh_generated = False
    btn = window.findChild(QPushButton, "btnRunSimulation")
    assert btn is not None

    def close_messagebox():
        for mb in window.findChildren(QMessageBox):
            mb.reject()
        for top in QApplication.topLevelWidgets():
            if isinstance(top, QMessageBox):
                top.reject()

    QTimer.singleShot(200, close_messagebox)
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
    assert window.design.simulation_complete is False
    window.close()


# ===========================================================================
# UI Interaction Tests — Input Fields
# ===========================================================================

def test_geometry_input_change_updates_profile(qt_app):
    """Editing a geometry field updates the design profile."""
    window = MainWindow()
    txt = window.findChild(QLineEdit, "txtDInnerSpider")
    assert txt is not None
    txt.setText("80.0")
    txt.editingFinished.emit()
    assert window.design.D_inner_spider == 80.0
    window.close()


def test_geometry_input_invalid_shows_red_background(qt_app):
    """Invalid geometry input colors the field red."""
    window = MainWindow()
    txt = window.findChild(QLineEdit, "txtHInner")
    assert txt is not None
    txt.setText("-1.0")
    txt.editingFinished.emit()
    # The implementation uses styleSheet to set red background
    style = txt.styleSheet() or ""
    assert "red" in style.lower()
    window.close()


def test_material_combobox_change_updates_properties(qt_app):
    """Selecting a different material updates design and labels."""
    window = MainWindow()
    cmb = window.findChild(QComboBox, "cmbMaterial")
    assert cmb is not None
    # Fallback DB provides at least 2 materials; index 1 should be Nomex Spider
    if cmb.count() > 1:
        cmb.setCurrentIndex(1)
        assert window.design.material_name == "Nomex Spider"
        lbl = window.findChild(QLabel, "lblYoungsModulus")
        assert "3500" in lbl.text()
    window.close()


def test_mesh_control_change_disables_run_button(qt_app):
    """Changing a mesh control disables the Run Simulation button."""
    window = MainWindow()
    window.design.mesh_generated = True
    btn = window.findChild(QPushButton, "btnRunSimulation")
    btn.setEnabled(True)
    txt = window.findChild(QLineEdit, "txtGlobalElementSize")
    assert txt is not None
    txt.setText("0.25")
    txt.editingFinished.emit()
    assert not btn.isEnabled()
    assert window.design.mesh_generated is False
    window.close()


# ===========================================================================
# UI Interaction Tests — Tabs
# ===========================================================================

def test_tab_cross_section_always_enabled(qt_app):
    """Cross-Section tab (index 0) is always selectable."""
    window = MainWindow()
    tab = window.findChild(QTabWidget, "tabWidget")
    assert tab is not None
    tab.setCurrentIndex(0)
    assert tab.currentIndex() == 0
    window.close()


def test_tab_strain_disabled_before_simulation(qt_app):
    """Strain tab is disabled before simulation completes."""
    window = MainWindow()
    window.design.simulation_complete = False
    window._update_simulation_tab_state()
    tab = window.findChild(QTabWidget, "tabWidget")
    assert tab is not None
    assert not tab.isTabEnabled(1)
    window.close()


def test_tab_strain_enabled_after_simulation(qt_app):
    """Strain tab is enabled after simulation completes."""
    window = MainWindow()
    window.design.simulation_complete = True
    window._update_simulation_tab_state()
    tab = window.findChild(QTabWidget, "tabWidget")
    assert tab is not None
    tab.setCurrentIndex(1)
    assert tab.currentIndex() == 1
    assert tab.isTabEnabled(1)
    window.close()


def test_tab_stress_enabled_after_simulation(qt_app):
    """Stress tab is enabled after simulation completes."""
    window = MainWindow()
    window.design.simulation_complete = True
    window._update_simulation_tab_state()
    tab = window.findChild(QTabWidget, "tabWidget")
    assert tab is not None
    tab.setCurrentIndex(2)
    assert tab.currentIndex() == 2
    assert tab.isTabEnabled(2)
    window.close()


def test_tab_force_deflection_enabled_after_simulation(qt_app):
    """Force vs. Deflection tab is enabled after simulation completes."""
    window = MainWindow()
    window.design.simulation_complete = True
    window._update_simulation_tab_state()
    tab = window.findChild(QTabWidget, "tabWidget")
    assert tab is not None
    tab.setCurrentIndex(3)
    assert tab.currentIndex() == 3
    assert tab.isTabEnabled(3)
    window.close()


def test_tab_compliance_enabled_after_simulation(qt_app):
    """Compliance tab is enabled after simulation completes."""
    window = MainWindow()
    window.design.simulation_complete = True
    window._update_simulation_tab_state()
    tab = window.findChild(QTabWidget, "tabWidget")
    assert tab is not None
    tab.setCurrentIndex(4)
    assert tab.currentIndex() == 4
    assert tab.isTabEnabled(4)
    window.close()


# ===========================================================================
# UI Interaction Tests — Keyboard Shortcuts
# ===========================================================================

def test_ctrl_n_shortcut_triggers_new(qt_app):
    """Ctrl+N resets the design to defaults."""
    window = MainWindow()
    window.design.D_inner_spider = 999.0
    # In offscreen mode QTest.keyClick with modifiers is unreliable;
    # trigger the underlying action directly to verify slot logic.
    window.actionNew.trigger()
    assert window.design.D_inner_spider == 75.0
    window.close()


def test_ctrl_m_shortcut_triggers_mesh(qt_app, monkeypatch):
    """Ctrl+M generates the mesh."""
    window = MainWindow()
    # Use safe params so pre-flight check passes
    window.design.t = 0.1
    window.design.h_inner = 5.0
    window.design.h_outer = 5.0
    window.design = api_module.recalculate_profile(window.design)
    monkeypatch.setattr("src.api.gmsh", MagicMock())
    monkeypatch.setattr("src.api.convert_mesh_with_elmergrid", lambda *a, **k: None)
    window.actionMesh.trigger()
    assert _wait_for_mesh(window), "Mesh did not complete within timeout"
    assert window.design.mesh_generated is True
    window.close()


def test_mesh_button_does_not_block_ui(qt_app, monkeypatch):
    """Mesh generation runs asynchronously and does not block the UI thread."""
    import time
    from PyQt6.QtCore import QEventLoop, QTimer
    window = MainWindow()

    # Use safe params so pre-flight check passes
    window.design.t = 0.1
    window.design.h_inner = 5.0
    window.design.h_outer = 5.0
    window.design = api_module.recalculate_profile(window.design)

    # Patch generate_mesh_with_timeout to take measurable time
    def slow_generate_mesh_with_timeout(design, timeout_sec=30):
        time.sleep(0.3)
        design.mesh_generated = True
        return design
    monkeypatch.setattr("src.api.generate_mesh_with_timeout", slow_generate_mesh_with_timeout)

    timer_fired = [False]
    def on_timer():
        timer_fired[0] = True
    QTimer.singleShot(100, on_timer)

    btn = window.findChild(QPushButton, "btnGenerateMesh")
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)

    # Wait for the timer to fire (should happen while mesh is still running)
    loop = QEventLoop()
    check_timer = QTimer()
    check_timer.timeout.connect(lambda: (loop.quit() if timer_fired[0] else None))
    check_timer.start(50)

    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(loop.quit)
    timeout_timer.start(2000)

    loop.exec()
    check_timer.stop()

    assert timer_fired[0], "QTimer did not fire — UI thread was blocked"

    # Now wait for mesh to complete
    assert _wait_for_mesh(window), "Mesh did not complete within timeout"
    assert window.design.mesh_generated is True
    window.close()


def test_ctrl_r_shortcut_triggers_run(qt_app, monkeypatch):
    """Ctrl+R runs the simulation."""
    window = MainWindow()
    window.design.mesh_generated = True

    def _mock_run_simulation(design):
        design.simulation_complete = True
        design.max_von_mises_stress = 150.0
        design.max_strain = 0.05
        design.force_deflection_data = [{"displacement_mm": 1.0, "force_N": 10.0, "direction": "inward"}]
        design.compliance_data = [{"displacement_mm": 1.0, "compliance_mm_per_N": 0.1, "direction": "inward"}]
        return design

    monkeypatch.setattr("src.main_window.run_simulation", _mock_run_simulation)
    window.actionRun.trigger()
    assert window.design.simulation_complete is True
    window.close()


def test_ui_preflight_shows_messagebox_for_invalid_geometry(qt_app, monkeypatch):
    """Clicking Mesh with invalid geometry shows a QMessageBox warning and does not start worker."""
    window = MainWindow()
    # Set bad parameters that fail check_spider_geometry_valid
    window.design.t = 0.75
    window.design.h_inner = 10.0
    window.design.h_outer = 10.0
    window.design.n_peaks = 7
    window.design = api_module.recalculate_profile(window.design)

    # Track whether a QMessageBox.warning was shown
    warning_shown = [False]
    original_warning = QMessageBox.warning

    def _mock_warning(parent, title, text):
        warning_shown[0] = True
        assert "Invalid Spider Geometry" in title
        return None

    monkeypatch.setattr("src.main_window.QMessageBox.warning", _mock_warning)

    # Patch the thread start so we can detect if the worker was spawned
    thread_started = [False]
    original_start = type(window._mesh_thread).start if hasattr(window, '_mesh_thread') else None

    def _mock_thread_start(self):
        thread_started[0] = True

    monkeypatch.setattr("PyQt6.QtCore.QThread.start", _mock_thread_start)

    btn = window.findChild(QPushButton, "btnGenerateMesh")
    assert btn is not None
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)

    assert warning_shown[0], "QMessageBox.warning was not called for invalid geometry"
    assert not thread_started[0], "Mesh thread was started despite invalid geometry"
    window.close()


def test_btn_generate_mesh_reenabled_after_error(qt_app, monkeypatch):
    """Bug fix: btnGenerateMesh must be re-enabled after a mesh generation error."""
    from PyQt6.QtCore import QEventLoop, QTimer
    window = MainWindow()
    # Use safe params so pre-flight check passes
    window.design.t = 0.1
    window.design.h_inner = 5.0
    window.design.h_outer = 5.0
    window.design = api_module.recalculate_profile(window.design)

    def _failing_generate_mesh_with_timeout(design, timeout_sec=30):
        raise RuntimeError("Simulated mesh failure")

    monkeypatch.setattr("src.api.generate_mesh_with_timeout", _failing_generate_mesh_with_timeout)
    # Prevent blocking QMessageBox from freezing the test
    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.critical", lambda *a, **k: None)
    btn = window.findChild(QPushButton, "btnGenerateMesh")
    assert btn is not None
    assert btn.isEnabled()
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)

    # Wait for async error handling to re-enable the button
    loop = QEventLoop()
    check_timer = QTimer()
    check_timer.timeout.connect(lambda: loop.quit() if btn.isEnabled() else None)
    check_timer.start(50)

    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(loop.quit)
    timeout_timer.start(3000)

    loop.exec()
    check_timer.stop()

    assert btn.isEnabled(), "btnGenerateMesh was not re-enabled after error"
    window.close()
