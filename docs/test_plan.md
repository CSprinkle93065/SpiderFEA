# Test Plan: SpiderFEA

**Version:** 0.1.0  
**Workflow ID:** wvc_20260529_061307  
**Date:** 2026-05-29  
**Status:** FINAL  

---

## Scope

This test plan covers all 20 User Actions and every UI element described in `definition.md`. It is organized into three categories:

1. **API Unit Tests** — Direct function tests for all 28 exported API functions in `src/api.py`.
2. **UI Construction Tests** — Verify that `MainWindow` and all dialogs instantiate, and that every described widget exists in the hierarchy.
3. **UI Interaction Tests** — Every `QPushButton`, `QAction` (menu item), and `QTabWidget` tab has a corresponding interaction test using `QTest.mouseClick()` or `.trigger()`.

External dependencies (`ElmerSolver`, `ElmerGrid`, `Gmsh`) are mocked in unit tests. The materials database is mocked or served from a test copy.

---

## 1. API Unit Tests

### 1.1 Design Lifecycle

#### TC-API-001: `create_design`

| Field | Value |
|-------|-------|
| **API Call** | `api.create_design(name="TestSpider")` |
| **Expected Result** | Returns a `SpiderDesign` instance with all default values from §4.3 and `name="TestSpider"`. |
| **Pass Criterion** | `assert design.D_inner_spider == 75.0 and design.material_name == "Phenolic-Treated Cloth"` |

| Field | Value |
|-------|-------|
| **API Call** | `api.create_design()` |
| **Expected Result** | Returns a `SpiderDesign` with default name ` "" `. |
| **Pass Criterion** | `assert design.name == ""` |

---

#### TC-API-002: `save_design`

| Field | Value |
|-------|-------|
| **Preconditions** | Database initialized via `init_database()` with a temporary path. |
| **API Call** | `api.save_design(design)` |
| **Expected Result** | Returns an integer design ID > 0. Design JSON stored in `designs` table. |
| **Pass Criterion** | `assert design_id > 0 and isinstance(design_id, int)` |

---

#### TC-API-003: `load_design`

| Field | Value |
|-------|-------|
| **Preconditions** | A design has been saved and its ID is known. |
| **API Call** | `api.load_design(design_id)` |
| **Expected Result** | Returns a `SpiderDesign` with matching input parameters. `simulation_complete` is `False`. |
| **Pass Criterion** | `assert loaded.D_inner_spider == original.D_inner_spider and loaded.simulation_complete is False` |

---

#### TC-API-004: `list_designs`

| Field | Value |
|-------|-------|
| **Preconditions** | At least one design saved. |
| **API Call** | `api.list_designs()` |
| **Expected Result** | Returns a list of dicts, each with keys `id`, `name`, `updated_at`. |
| **Pass Criterion** | `assert len(designs) >= 1 and all("id" in d and "name" in d for d in designs)` |

---

#### TC-API-005: `delete_design`

| Field | Value |
|-------|-------|
| **Preconditions** | A design has been saved and its ID is known. |
| **API Call** | `api.delete_design(design_id)` |
| **Expected Result** | Design removed from database. |
| **Pass Criterion** | `api.delete_design(design_id); assert design_id not in [d["id"] for d in api.list_designs()]` |

| Field | Value |
|-------|-------|
| **API Call** | `api.delete_design(99999)` |
| **Expected Result** | Raises `ValueError`. |
| **Pass Criterion** | `with pytest.raises(ValueError): api.delete_design(99999)` |

---

#### TC-API-006: `clone_design`

| Field | Value |
|-------|-------|
| **Preconditions** | A design has been saved. |
| **API Call** | `api.clone_design(design_id, new_name="Clone")` |
| **Expected Result** | Returns a new `SpiderDesign` with identical geometry/material/mesh values and `name="Clone"`. Not persisted. |
| **Pass Criterion** | `assert clone.name == "Clone" and clone.D_inner_spider == original.D_inner_spider and clone is not original` |

---

### 1.2 Geometry

#### TC-API-007: `update_geometry_parameter`

| Field | Value |
|-------|-------|
| **API Call** | `api.update_geometry_parameter(design, "D_inner_spider", 80.0)` |
| **Expected Result** | `design.D_inner_spider == 80.0` and profile recalculated. |
| **Pass Criterion** | `assert updated.D_inner_spider == 80.0 and len(updated.profile_r) > 0` |

| Field | Value |
|-------|-------|
| **API Call** | `api.update_geometry_parameter(design, "invalid_field", 1.0)` |
| **Expected Result** | Raises `AttributeError` or `ValueError`. |
| **Pass Criterion** | `with pytest.raises((AttributeError, ValueError)): api.update_geometry_parameter(design, "invalid_field", 1.0)` |

---

#### TC-API-008: `recalculate_profile`

| Field | Value |
|-------|-------|
| **API Call** | `api.recalculate_profile(design)` |
| **Expected Result** | `profile_r` and `profile_z` are non-empty lists of equal length, forming a closed polygon. |
| **Pass Criterion** | `assert len(updated.profile_r) == len(updated.profile_z) > 4 and updated.profile_r[0] == updated.profile_r[-1]` |

---

#### TC-API-009: `validate_geometry`

| Field | Value |
|-------|-------|
| **API Call** | `api.validate_geometry(default_design)` |
| **Expected Result** | `(True, "")` |
| **Pass Criterion** | `assert result == (True, "")` |

| Field | Value |
|-------|-------|
| **API Call** | Set `D_outer_landing_OD < D_outer_landing_ID`, then `validate_geometry(design)` |
| **Expected Result** | `(False, error_message)` |
| **Pass Criterion** | `assert valid is False and isinstance(msg, str) and len(msg) > 0` |

| Field | Value |
|-------|-------|
| **API Call** | Set `h_inner = -1.0`, then `validate_geometry(design)` |
| **Expected Result** | `(False, error_message)` |
| **Pass Criterion** | `assert valid is False` |

---

### 1.3 Material Properties

#### TC-API-010: `update_material_property`

| Field | Value |
|-------|-------|
| **Preconditions** | Mock materials database with at least "Nomex Spider" entry. |
| **API Call** | `api.update_material_property(design, "Nomex Spider")` |
| **Expected Result** | `material_name="Nomex Spider"`, `youngs_modulus=3500.0`, `poissons_ratio=0.30`, `density=720.0`. |
| **Pass Criterion** | `assert updated.material_name == "Nomex Spider" and updated.youngs_modulus == 3500.0` |

| Field | Value |
|-------|-------|
| **API Call** | `api.update_material_property(design, "NonExistentMaterial")` |
| **Expected Result** | Raises `ValueError`. |
| **Pass Criterion** | `with pytest.raises(ValueError): api.update_material_property(design, "NonExistentMaterial")` |

---

#### TC-API-011: `list_available_spider_materials`

| Field | Value |
|-------|-------|
| **API Call** | `api.list_available_spider_materials()` |
| **Expected Result** | Returns a list of dicts with keys `name`, `youngs_modulus`, `poissons_ratio`, `density`, `model_type`. All `model_type == "linear_elastic"`. |
| **Pass Criterion** | `assert len(mats) >= 2 and all(m["model_type"] == "linear_elastic" for m in mats)` |

---

### 1.4 Mesh Controls

#### TC-API-012: `update_mesh_control`

| Field | Value |
|-------|-------|
| **API Call** | `api.update_mesh_control(design, "global_element_size", 0.25)` |
| **Expected Result** | `design.global_element_size == 0.25`, `mesh_generated=False`, `simulation_complete=False`. |
| **Pass Criterion** | `assert updated.global_element_size == 0.25 and updated.mesh_generated is False and updated.simulation_complete is False` |

| Field | Value |
|-------|-------|
| **API Call** | `api.update_mesh_control(design, "invalid_field", 1.0)` |
| **Expected Result** | Raises `AttributeError` or `ValueError`. |
| **Pass Criterion** | `with pytest.raises((AttributeError, ValueError)): api.update_mesh_control(design, "invalid_field", 1.0)` |

---

### 1.5 Mesh Generation

#### TC-API-013: `generate_mesh`

| Field | Value |
|-------|-------|
| **Preconditions** | Valid geometry, Gmsh Python API mocked. |
| **API Call** | `api.generate_mesh(design)` |
| **Expected Result** | Returns updated design with `mesh_generated=True`. Mock Gmsh API called with profile coordinates. |
| **Pass Criterion** | `assert updated.mesh_generated is True` and mock `gmsh.model.mesh.generate` was called. |

---

#### TC-API-014: `convert_mesh_with_elmergrid`

| Field | Value |
|-------|-------|
| **Preconditions** | A `.msh` file exists at a temp path. `ElmerGrid.exe` mocked via `subprocess.run`. |
| **API Call** | `api.convert_mesh_with_elmergrid("spider.msh", "mesh/")` |
| **Expected Result** | `subprocess.run` called with correct arguments. No exception. |
| **Pass Criterion** | `mock_subprocess_run.assert_called_once()` with args containing `ElmerGrid` and `spider.msh`. |

---

### 1.6 Elmer Simulation

#### TC-API-015: `run_simulation`

| Field | Value |
|-------|-------|
| **Preconditions** | `design.mesh_generated=True`. `ElmerSolver.exe` and result parsing mocked. |
| **API Call** | `api.run_simulation(design)` |
| **Expected Result** | Returns updated design with `simulation_complete=True`, populated result arrays, `max_von_mises_stress > 0`, `max_strain > 0`. |
| **Pass Criterion** | `assert updated.simulation_complete is True and updated.max_von_mises_stress > 0 and len(updated.force_deflection_data) > 0` |

| Field | Value |
|-------|-------|
| **Preconditions** | `design.mesh_generated=False`. |
| **API Call** | `api.run_simulation(design)` |
| **Expected Result** | Raises `RuntimeError`. |
| **Pass Criterion** | `with pytest.raises(RuntimeError): api.run_simulation(design)` |

---

#### TC-API-016: `generate_elmer_sif`

| Field | Value |
|-------|-------|
| **Preconditions** | Valid design with material properties set. Temp directory exists. |
| **API Call** | `api.generate_elmer_sif(design, tmpdir)` |
| **Expected Result** | Returns path to `.sif` file. File exists and contains "Solid Mechanics" and "Axisymmetric". |
| **Pass Criterion** | `assert os.path.isfile(sif_path) and "Solid Mechanics" in open(sif_path).read()` |

---

#### TC-API-017: `parse_simulation_results`

| Field | Value |
|-------|-------|
| **Preconditions** | Mock VTU/EP files present in temp directory. |
| **API Call** | `api.parse_simulation_results(tmpdir)` |
| **Expected Result** | Returns dict with keys `force_deflection_data`, `compliance_data`, `max_von_mises_stress`, `max_strain`, `strain_field_data`, `stress_field_data`. |
| **Pass Criterion** | `assert all(k in result for k in expected_keys) and result["max_von_mises_stress"] > 0` |

---

### 1.7 Export

#### TC-API-018: `export_cross_section_png`

| Field | Value |
|-------|-------|
| **Preconditions** | Valid design with recalculated profile. Temp file path. |
| **API Call** | `api.export_cross_section_png(design, tmp_png_path, show_mesh=False)` |
| **Expected Result** | PNG file created at `tmp_png_path` with size > 0 bytes. |
| **Pass Criterion** | `assert os.path.isfile(tmp_png_path) and os.path.getsize(tmp_png_path) > 0` |

---

#### TC-API-019: `export_force_deflection_csv`

| Field | Value |
|-------|-------|
| **Preconditions** | Design with `force_deflection_data` populated. |
| **API Call** | `api.export_force_deflection_csv(design, tmp_csv_path)` |
| **Expected Result** | CSV file with headers `displacement_mm`, `force_N`, `direction`. |
| **Pass Criterion** | `assert "displacement_mm,force_N,direction" in open(tmp_csv_path).readline()` |

---

#### TC-API-020: `export_compliance_csv`

| Field | Value |
|-------|-------|
| **Preconditions** | Design with `compliance_data` populated. |
| **API Call** | `api.export_compliance_csv(design, tmp_csv_path)` |
| **Expected Result** | CSV file with headers `displacement_mm`, `compliance_mm_per_N`, `direction`. |
| **Pass Criterion** | `assert "displacement_mm,compliance_mm_per_N,direction" in open(tmp_csv_path).readline()` |

---

#### TC-API-021: `export_results_json`

| Field | Value |
|-------|-------|
| **Preconditions** | Design with simulation results populated. |
| **API Call** | `api.export_results_json(design, tmp_json_path)` |
| **Expected Result** | Valid JSON file containing `input_parameters`, `max_von_mises_stress`, `max_strain`. |
| **Pass Criterion** | `assert json.load(open(tmp_json_path))["max_von_mises_stress"] == design.max_von_mises_stress` |

---

### 1.8 Database Backup / Restore

#### TC-API-022: `export_database`

| Field | Value |
|-------|-------|
| **Preconditions** | Database initialized with at least one design. |
| **API Call** | `api.export_database(tmp_backup_path)` |
| **Expected Result** | Backup file exists and is a valid SQLite database. |
| **Pass Criterion** | `assert os.path.isfile(tmp_backup_path) and os.path.getsize(tmp_backup_path) > 0` |

---

#### TC-API-023: `import_database`

| Field | Value |
|-------|-------|
| **Preconditions** | A backup file exists with known designs. |
| **API Call** | `api.import_database(backup_path, merge=False)` |
| **Expected Result** | Current database replaced; designs from backup are listable. |
| **Pass Criterion** | `assert len(api.list_designs()) == expected_count` |

| Field | Value |
|-------|-------|
| **API Call** | `api.import_database(backup_path, merge=True)` |
| **Expected Result** | Backup designs merged; no duplicates by name. |
| **Pass Criterion** | `assert len(api.list_designs()) == original_count + new_count - duplicates` |

---

### 1.9 Utility

#### TC-API-024: `init_database`

| Field | Value |
|-------|-------|
| **API Call** | `api.init_database(tmp_db_path)` |
| **Expected Result** | `designs` and `settings` tables created. |
| **Pass Criterion** | `assert sqlite3.connect(tmp_db_path).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("designs",), ("settings",)]` |

---

#### TC-API-025: `set_elmer_solver_path`

| Field | Value |
|-------|-------|
| **API Call** | `api.set_elmer_solver_path("C:\\Elmer\\bin\\ElmerSolver.exe")` |
| **Expected Result** | Path persisted in `settings` table. |
| **Pass Criterion** | `assert api.get_setting("elmer_solver_path") == "C:\\Elmer\\bin\\ElmerSolver.exe"` |

---

#### TC-API-026: `set_elmergrid_path`

| Field | Value |
|-------|-------|
| **API Call** | `api.set_elmergrid_path("C:\\Elmer\\bin\\ElmerGrid.exe")` |
| **Expected Result** | Path persisted in `settings` table. |
| **Pass Criterion** | `assert api.get_setting("elmergrid_path") == "C:\\Elmer\\bin\\ElmerGrid.exe"` |

---

#### TC-API-027: `set_working_directory`

| Field | Value |
|-------|-------|
| **API Call** | `api.set_working_directory("C:\\Work\\SpiderFEA")` |
| **Expected Result** | Path persisted in `settings` table. |
| **Pass Criterion** | `assert api.get_setting("working_directory") == "C:\\Work\\SpiderFEA"` |

---

#### TC-API-028: `get_default_values`

| Field | Value |
|-------|-------|
| **API Call** | `api.get_default_values()` |
| **Expected Result** | Returns `SpiderDesign` with exact defaults from §4.3. |
| **Pass Criterion** | `assert defaults.D_inner_spider == 75.0 and defaults.L_inner_bond == 2.5 and defaults.h_outer == 10.0` |

---

## 2. UI Construction Tests

All tests run with `QT_QPA_PLATFORM=offscreen`.

### UTC-001: `test_main_window_constructs`

| Field | Value |
|-------|-------|
| **Description** | `MainWindow()` completes `__init__` without raising. |
| **Steps** | 1. `window = MainWindow()` 2. `assert window is not None` 3. `window.close()` |
| **Pass Criterion** | `assert window is not None` |

---

### UTC-002: `test_all_geometry_input_widgets_present`

| Field | Value |
|-------|-------|
| **Description** | All 7 geometry `QLineEdit` widgets exist with correct `objectName`. |
| **Steps** | 1. `window = MainWindow()` 2. Find each widget via `findChild(QLineEdit, name)` 3. Assert all found. |
| **Pass Criterion** | `assert window.findChild(QLineEdit, "txtDInnerSpider") is not None` (and 6 more) |

**Widget checklist:**
- `txtDInnerSpider`
- `txtLInnerBond`
- `txtDOuterLandingID`
- `txtDOuterLandingOD`
- `txtHInner`
- `txtHOuter`
- `txtT`

---

### UTC-003: `test_material_widgets_present`

| Field | Value |
|-------|-------|
| **Description** | Material `QComboBox` and read-only property labels exist. |
| **Pass Criterion** | `assert window.findChild(QComboBox, "cmbMaterial") is not None and window.findChild(QLabel, "lblYoungsModulus") is not None` |

---

### UTC-004: `test_fixed_geometry_labels_present`

| Field | Value |
|-------|-------|
| **Description** | Read-only labels for fixed geometry exist. |
| **Pass Criterion** | `assert window.findChild(QLabel, "lblInnerConeAngle") is not None and window.findChild(QLabel, "lblNumberOfPeaks") is not None` |

---

### UTC-005: `test_mesh_control_widgets_present`

| Field | Value |
|-------|-------|
| **Description** | All 3 mesh control `QLineEdit` widgets exist. |
| **Pass Criterion** | `assert window.findChild(QLineEdit, "txtGlobalElementSize") is not None` (and 2 more) |

**Widget checklist:**
- `txtGlobalElementSize`
- `txtElementsThroughThickness`
- `txtMeshRefinementFactor`

---

### UTC-006: `test_action_buttons_present`

| Field | Value |
|-------|-------|
| **Description** | Mesh and Run Simulation buttons exist. |
| **Pass Criterion** | `assert window.findChild(QPushButton, "btnGenerateMesh") is not None and window.findChild(QPushButton, "btnRunSimulation") is not None` |

---

### UTC-007: `test_right_panel_tabs_present`

| Field | Value |
|-------|-------|
| **Description** | All 5 tabs exist in the `QTabWidget`. |
| **Pass Criterion** | `assert tab_widget.count() == 5` and each tab is accessible by index. |

**Tab checklist:**
- Tab 0: Cross-Section
- Tab 1: Strain
- Tab 2: Stress
- Tab 3: Force vs. Deflection
- Tab 4: Compliance

---

### UTC-008: `test_menu_actions_present`

| Field | Value |
|-------|-------|
| **Description** | All menu actions exist with `objectName`. |
| **Pass Criterion** | `assert window.findChild(QAction, "actionNew") is not None` (and all listed below) |

**Action checklist:**
- `actionNew`
- `actionOpenDesign`
- `actionSaveDesign`
- `actionDeleteDesign`
- `actionExportCrossSectionPng`
- `actionExportForceDeflectionCsv`
- `actionExportComplianceCsv`
- `actionExportResultsJson`
- `actionExportDatabase`
- `actionImportDatabase`
- `actionSetElmerSolverPath`
- `actionSetElmerGridPath`
- `actionSetWorkingDirectory`
- `actionAbout`

---

### UTC-009: `test_status_bar_present`

| Field | Value |
|-------|-------|
| **Description** | Status bar exists and shows default text. |
| **Pass Criterion** | `assert window.statusBar() is not None and "Ready" in window.statusBar().currentMessage()` |

---

### UTC-010: `test_about_dialog_constructs`

| Field | Value |
|-------|-------|
| **Description** | `AboutDialog` can be instantiated. |
| **Pass Criterion** | `dlg = AboutDialog(parent=window); assert dlg is not None; dlg.close()` |

---

## 3. UI Interaction Tests

All tests run with `QT_QPA_PLATFORM=offscreen`. Modal dialogs are auto-dismissed via `QTimer.singleShot`.

### 3.1 Menu Actions

#### UIT-001: `test_action_new_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.6 New Design |
| **Steps** | 1. `window = MainWindow()` 2. `action = window.findChild(QAction, "actionNew")` 3. `action.trigger()` |
| **Expected Side Effect** | All geometry inputs reset to defaults, `mesh_generated=False`, `simulation_complete=False`. |
| **Pass Criterion** | `assert window.design.D_inner_spider == 75.0 and window.design.mesh_generated is False` |

---

#### UIT-002: `test_action_open_design_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.8 Load Design |
| **Steps** | 1. Mock `QFileDialog.getOpenFileName` to return a temp DB path. 2. `action = window.findChild(QAction, "actionOpenDesign")` 3. `action.trigger()` |
| **Expected Side Effect** | Design loaded from DB; input fields updated. |
| **Pass Criterion** | `assert window.design.D_inner_spider == loaded_design.D_inner_spider` |

---

#### UIT-003: `test_action_save_design_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.7 Save Design |
| **Steps** | 1. Mock `QInputDialog.getText` to return `"TestDesign"`. 2. `action = window.findChild(QAction, "actionSaveDesign")` 3. `action.trigger()` |
| **Expected Side Effect** | Design saved to SQLite; design list updated. |
| **Pass Criterion** | `assert "TestDesign" in [d["name"] for d in api.list_designs()]` |

---

#### UIT-004: `test_action_delete_design_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.9 Delete Design |
| **Steps** | 1. Pre-seed DB with a design. 2. Mock `QInputDialog.getItem` to select that design name. 3. `actionDeleteDesign.trigger()` |
| **Expected Side Effect** | Design removed from database. |
| **Pass Criterion** | `assert design_id not in [d["id"] for d in api.list_designs()]` |

---

#### UIT-005: `test_action_export_cross_section_png_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.10 Export Cross-Section PNG |
| **Steps** | 1. Mock `QFileDialog.getSaveFileName` to return temp PNG path. 2. `actionExportCrossSectionPng.trigger()` |
| **Expected Side Effect** | PNG file written to selected path. |
| **Pass Criterion** | `assert os.path.isfile(tmp_png_path)` |

---

#### UIT-006: `test_action_export_force_deflection_csv_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.11 Export Force-Deflection CSV |
| **Steps** | 1. Populate design with mock force-deflection data. 2. Mock `QFileDialog.getSaveFileName`. 3. `actionExportForceDeflectionCsv.trigger()` |
| **Expected Side Effect** | CSV file written with correct headers. |
| **Pass Criterion** | `assert "displacement_mm,force_N,direction" in open(tmp_csv).readline()` |

---

#### UIT-007: `test_action_export_compliance_csv_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.12 Export Compliance CSV |
| **Steps** | 1. Populate design with mock compliance data. 2. Mock `QFileDialog.getSaveFileName`. 3. `actionExportComplianceCsv.trigger()` |
| **Expected Side Effect** | CSV file written with correct headers. |
| **Pass Criterion** | `assert "displacement_mm,compliance_mm_per_N,direction" in open(tmp_csv).readline()` |

---

#### UIT-008: `test_action_export_results_json_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.13 Export Results Summary |
| **Steps** | 1. Populate design with mock results. 2. Mock `QFileDialog.getSaveFileName`. 3. `actionExportResultsJson.trigger()` |
| **Expected Side Effect** | JSON file written with `max_von_mises_stress` key. |
| **Pass Criterion** | `assert "max_von_mises_stress" in json.load(open(tmp_json))` |

---

#### UIT-009: `test_action_export_database_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.19 Export Database |
| **Steps** | 1. Mock `QFileDialog.getSaveFileName`. 2. `actionExportDatabase.trigger()` |
| **Expected Side Effect** | Backup file created. |
| **Pass Criterion** | `assert os.path.isfile(tmp_backup_path)` |

---

#### UIT-010: `test_action_import_database_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.20 Import Database |
| **Steps** | 1. Create a backup file. 2. Mock `QFileDialog.getOpenFileName`. 3. `actionImportDatabase.trigger()` |
| **Expected Side Effect** | Designs from backup are now listable. |
| **Pass Criterion** | `assert len(api.list_designs()) >= backup_design_count` |

---

#### UIT-011: `test_action_set_elmer_solver_path_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.15 Set ElmerSolver path |
| **Steps** | 1. Mock `QFileDialog.getOpenFileName` to return a fake path. 2. `actionSetElmerSolverPath.trigger()` |
| **Expected Side Effect** | `settings` table updated. |
| **Pass Criterion** | `assert api.get_setting("elmer_solver_path") == fake_path` |

---

#### UIT-012: `test_action_set_elmergrid_path_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.16 Set ElmerGrid path |
| **Steps** | 1. Mock `QFileDialog.getOpenFileName`. 2. `actionSetElmerGridPath.trigger()` |
| **Expected Side Effect** | `settings` table updated. |
| **Pass Criterion** | `assert api.get_setting("elmergrid_path") == fake_path` |

---

#### UIT-013: `test_action_set_working_directory_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.17 Set Working Directory |
| **Steps** | 1. Mock `QFileDialog.getExistingDirectory`. 2. `actionSetWorkingDirectory.trigger()` |
| **Expected Side Effect** | `settings` table updated. |
| **Pass Criterion** | `assert api.get_setting("working_directory") == fake_dir` |

---

#### UIT-014: `test_action_about_triggered`

| Field | Value |
|-------|-------|
| **User Action** | 3.18 View About |
| **Steps** | 1. `actionAbout.trigger()` 2. Auto-dismiss dialog via `QTimer.singleShot(100, dlg.reject)` 3. Assert dialog appeared. |
| **Expected Side Effect** | `AboutDialog` opens and shows version text. |
| **Pass Criterion** | `assert any(isinstance(w, QDialog) and "About" in w.windowTitle() for w in QApplication.topLevelWidgets())` |

---

### 3.2 Buttons

#### UIT-015: `test_btn_generate_mesh_clicked`

| Field | Value |
|-------|-------|
| **User Action** | 3.4 Generate Mesh |
| **Steps** | 1. Mock `gmsh` API. 2. `btn = window.findChild(QPushButton, "btnGenerateMesh")` 3. `QTest.mouseClick(btn, Qt.MouseButton.LeftButton)` |
| **Expected Side Effect** | `design.mesh_generated=True`; `btnRunSimulation` enabled. |
| **Pass Criterion** | `assert window.design.mesh_generated is True and window.findChild(QPushButton, "btnRunSimulation").isEnabled()` |

---

#### UIT-016: `test_btn_run_simulation_clicked`

| Field | Value |
|-------|-------|
| **User Action** | 3.5 Run Simulation |
| **Steps** | 1. Set `design.mesh_generated=True` with mock mesh. 2. Mock `subprocess.run` and result parsing. 3. Click `btnRunSimulation`. |
| **Expected Side Effect** | `design.simulation_complete=True`; result tabs enabled. |
| **Pass Criterion** | `assert window.design.simulation_complete is True and window.tabWidget.isTabEnabled(1)` |

---

#### UIT-017: `test_btn_run_simulation_disabled_shows_popup`

| Field | Value |
|-------|-------|
| **User Action** | 3.5 Run Simulation (pressed while disabled) |
| **Steps** | 1. Ensure `design.mesh_generated=False`. 2. Auto-dismiss any `QMessageBox` via `QTimer.singleShot(100, ...)` 3. Click `btnRunSimulation`. |
| **Expected Side Effect** | Snarky popup displayed; no crash. |
| **Pass Criterion** | `assert window.design.simulation_complete is False` and no unhandled exception. |

---

### 3.3 Input Fields

#### UIT-018: `test_geometry_input_change_updates_profile`

| Field | Value |
|-------|-------|
| **User Action** | 3.1 Change any geometry input parameter |
| **Steps** | 1. `txt = window.findChild(QLineEdit, "txtDInnerSpider")` 2. `txt.setText("80.0")` 3. Emit `editingFinished` or press Tab. |
| **Expected Side Effect** | `design.D_inner_spider == 80.0`; cross-section plot updated. |
| **Pass Criterion** | `assert window.design.D_inner_spider == 80.0` |

---

#### UIT-019: `test_geometry_input_invalid_shows_red_background`

| Field | Value |
|-------|-------|
| **User Action** | 3.1 Change geometry input to invalid value |
| **Steps** | 1. `txt.setText("-1.0")` 2. Emit `editingFinished`. |
| **Expected Side Effect** | Field background turns red; cross-section cleared. |
| **Pass Criterion** | `assert txt.styleSheet() == "background-color: red;"` or equivalent red indicator. |

---

#### UIT-020: `test_material_combobox_change_updates_properties`

| Field | Value |
|-------|-------|
| **User Action** | 3.2 Change material selection |
| **Steps** | 1. `cmb = window.findChild(QComboBox, "cmbMaterial")` 2. Set index to "Nomex Spider". |
| **Expected Side Effect** | `design.material_name="Nomex Spider"`; property labels updated. |
| **Pass Criterion** | `assert window.design.material_name == "Nomex Spider" and "3500" in window.findChild(QLabel, "lblYoungsModulus").text()` |

---

#### UIT-021: `test_mesh_control_change_disables_run_button`

| Field | Value |
|-------|-------|
| **User Action** | 3.3 Change any mesh control |
| **Steps** | 1. Set `mesh_generated=True` and enable Run button. 2. Change mesh control value. 3. Emit `editingFinished`. |
| **Expected Side Effect** | `btnRunSimulation` disabled; `mesh_generated=False`. |
| **Pass Criterion** | `assert not window.findChild(QPushButton, "btnRunSimulation").isEnabled() and window.design.mesh_generated is False` |

---

### 3.4 Tabs

#### UIT-022: `test_tab_cross_section_always_enabled`

| Field | Value |
|-------|-------|
| **User Action** | 3.14 Switch to result tab (Cross-Section) |
| **Steps** | 1. `tab = window.findChild(QTabWidget, "tabWidget")` 2. `tab.setCurrentIndex(0)` |
| **Expected Side Effect** | Tab is active; no crash. |
| **Pass Criterion** | `assert tab.currentIndex() == 0` |

---

#### UIT-023: `test_tab_strain_disabled_before_simulation`

| Field | Value |
|-------|-------|
| **User Action** | 3.14 Switch to result tab (Strain) |
| **Steps** | 1. Ensure `simulation_complete=False`. 2. Attempt to select Strain tab. |
| **Expected Side Effect** | Tab index 1 is not enabled. |
| **Pass Criterion** | `assert not tab.isTabEnabled(1)` |

---

#### UIT-024: `test_tab_strain_enabled_after_simulation`

| Field | Value |
|-------|-------|
| **User Action** | 3.14 Switch to result tab (Strain) |
| **Steps** | 1. Set `simulation_complete=True`. 2. `tab.setCurrentIndex(1)` |
| **Expected Side Effect** | Tab becomes active; strain plot rendered. |
| **Pass Criterion** | `assert tab.currentIndex() == 1 and tab.isTabEnabled(1)` |

---

#### UIT-025: `test_tab_stress_enabled_after_simulation`

| Field | Value |
|-------|-------|
| **User Action** | 3.14 Switch to result tab (Stress) |
| **Steps** | 1. Set `simulation_complete=True`. 2. `tab.setCurrentIndex(2)` |
| **Expected Side Effect** | Tab becomes active. |
| **Pass Criterion** | `assert tab.currentIndex() == 2 and tab.isTabEnabled(2)` |

---

#### UIT-026: `test_tab_force_deflection_enabled_after_simulation`

| Field | Value |
|-------|-------|
| **User Action** | 3.14 Switch to result tab (Force vs. Deflection) |
| **Steps** | 1. Set `simulation_complete=True`. 2. `tab.setCurrentIndex(3)` |
| **Expected Side Effect** | Tab becomes active. |
| **Pass Criterion** | `assert tab.currentIndex() == 3 and tab.isTabEnabled(3)` |

---

#### UIT-027: `test_tab_compliance_enabled_after_simulation`

| Field | Value |
|-------|-------|
| **User Action** | 3.14 Switch to result tab (Compliance) |
| **Steps** | 1. Set `simulation_complete=True`. 2. `tab.setCurrentIndex(4)` |
| **Expected Side Effect** | Tab becomes active. |
| **Pass Criterion** | `assert tab.currentIndex() == 4 and tab.isTabEnabled(4)` |

---

### 3.5 Keyboard Shortcuts

#### UIT-028: `test_ctrl_n_shortcut_triggers_new`

| Field | Value |
|-------|-------|
| **User Action** | Ctrl+N |
| **Steps** | 1. `QTest.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)` |
| **Expected Side Effect** | Design reset to defaults. |
| **Pass Criterion** | `assert window.design.D_inner_spider == 75.0` |

---

#### UIT-029: `test_ctrl_m_shortcut_triggers_mesh`

| Field | Value |
|-------|-------|
| **User Action** | Ctrl+M |
| **Steps** | 1. Mock `gmsh` API. 2. `QTest.keyClick(window, Qt.Key.Key_M, Qt.KeyboardModifier.ControlModifier)` |
| **Expected Side Effect** | `design.mesh_generated=True`. |
| **Pass Criterion** | `assert window.design.mesh_generated is True` |

---

#### UIT-030: `test_ctrl_r_shortcut_triggers_run`

| Field | Value |
|-------|-------|
| **User Action** | Ctrl+R |
| **Steps** | 1. Set `mesh_generated=True`. 2. Mock solver. 3. `QTest.keyClick(window, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)` |
| **Expected Side Effect** | `design.simulation_complete=True`. |
| **Pass Criterion** | `assert window.design.simulation_complete is True` |

---

## Completeness Summary

| Category | Count | Coverage |
|----------|-------|----------|
| API Unit Tests | 28 | 100% of §5 API functions |
| UI Construction Tests | 10 | All widget groups, dialogs, menu actions |
| UI Interaction Tests | 30 | Every button, menu action, tab, and input field |
| **Total Test Cases** | **68** | |

### User Action → Test Mapping

| User Action | Test Case(s) |
|-------------|-------------|
| 3.1 Change geometry input | TC-API-007, UIT-018, UIT-019 |
| 3.2 Change material | TC-API-010, UIT-020 |
| 3.3 Change mesh control | TC-API-012, UIT-021 |
| 3.4 Generate Mesh | TC-API-013, UIT-015, UIT-029 |
| 3.5 Run Simulation | TC-API-015, UIT-016, UIT-017, UIT-030 |
| 3.6 New Design | TC-API-001, UIT-001, UIT-028 |
| 3.7 Save Design | TC-API-002, UIT-003 |
| 3.8 Load Design | TC-API-003, UIT-002 |
| 3.9 Delete Design | TC-API-005, UIT-004 |
| 3.10 Export Cross-Section PNG | TC-API-018, UIT-005 |
| 3.11 Export Force-Deflection CSV | TC-API-019, UIT-006 |
| 3.12 Export Compliance CSV | TC-API-020, UIT-007 |
| 3.13 Export Results Summary | TC-API-021, UIT-008 |
| 3.14 Switch to result tab | UIT-022 through UIT-027 |
| 3.15 Set ElmerSolver path | TC-API-025, UIT-011 |
| 3.16 Set ElmerGrid path | TC-API-026, UIT-012 |
| 3.17 Set Working Directory | TC-API-027, UIT-013 |
| 3.18 View About | UIT-014 |
| 3.19 Export Database | TC-API-022, UIT-009 |
| 3.20 Import Database | TC-API-023, UIT-010 |

### UI Element → Test Mapping

| UI Element | Construction Test | Interaction Test |
|------------|-------------------|------------------|
| Menu: File → New | UTC-008 | UIT-001 |
| Menu: File → Open Design | UTC-008 | UIT-002 |
| Menu: File → Save Design | UTC-008 | UIT-003 |
| Menu: File → Delete Design | UTC-008 | UIT-004 |
| Menu: File → Export → PNG | UTC-008 | UIT-005 |
| Menu: File → Export → CSV (Force) | UTC-008 | UIT-006 |
| Menu: File → Export → CSV (Compliance) | UTC-008 | UIT-007 |
| Menu: File → Export → JSON | UTC-008 | UIT-008 |
| Menu: File → Export → Database | UTC-008 | UIT-009 |
| Menu: File → Import → Database | UTC-008 | UIT-010 |
| Menu: Setup → ElmerSolver path | UTC-008 | UIT-011 |
| Menu: Setup → ElmerGrid path | UTC-008 | UIT-012 |
| Menu: Setup → Working Directory | UTC-008 | UIT-013 |
| Menu: Help → About | UTC-008, UTC-010 | UIT-014 |
| Button: Generate Mesh | UTC-006 | UIT-015, UIT-029 |
| Button: Run Simulation | UTC-006 | UIT-016, UIT-017, UIT-030 |
| Tab: Cross-Section | UTC-007 | UIT-022 |
| Tab: Strain | UTC-007 | UIT-023, UIT-024 |
| Tab: Stress | UTC-007 | UIT-025 |
| Tab: Force vs. Deflection | UTC-007 | UIT-026 |
| Tab: Compliance | UTC-007 | UIT-027 |
| Input: txtDInnerSpider … txtT | UTC-002 | UIT-018, UIT-019 |
| Input: cmbMaterial | UTC-003 | UIT-020 |
| Input: txtGlobalElementSize … txtMeshRefinementFactor | UTC-005 | UIT-021 |

---

*End of Test Plan*
