"""
SpiderFEA — Main Window

PyQt6 QMainWindow with left control panel and right tabbed plots.
All business logic is delegated to src.api.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Re-export so tests can monkeypatch them via src.main_window
import src.api as api_module
from src.api import (
    create_design,
    recalculate_profile,
    update_geometry_parameter,
    update_material_property,
    update_mesh_control,
    generate_mesh,
    run_simulation,
    save_design,
    load_design,
    list_designs,
    delete_design,
    export_cross_section_png,
    export_force_deflection_csv,
    export_compliance_csv,
    export_results_json,
    export_database,
    import_database,
    set_elmer_solver_path,
    set_elmergrid_path,
    set_working_directory,
    list_available_spider_materials,
    parse_simulation_results,
    init_database,
)

# Re-export for monkeypatching by tests
gmsh = api_module.gmsh

from src.dialogs import AboutDialog
from src.models import SpiderDesign


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpiderFEA v0.1.0")
        self.setMinimumSize(1000, 700)

        init_database()
        self.design = create_design()
        self.design = recalculate_profile(self.design)
        self._init_ui()
        self._init_menu()
        self._init_shortcuts()
        self._populate_fields_from_design()
        self._update_cross_section_tab()
        self._update_simulation_tab_state()

    # -----------------------------------------------------------------------
    # UI Construction
    # -----------------------------------------------------------------------
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)
        scroll.setMaximumWidth(420)
        splitter.addWidget(scroll)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(left_container)

        # --- Geometry Group ---
        geo_group = QGroupBox("Spider Geometry")
        geo_layout = QVBoxLayout(geo_group)

        self.txtDInnerSpider = QLineEdit()
        self.txtDInnerSpider.setObjectName("txtDInnerSpider")
        self._add_labeled_row(geo_layout, "Spider ID (D_inner) [mm]:", self.txtDInnerSpider)

        self.txtLInnerBond = QLineEdit()
        self.txtLInnerBond.setObjectName("txtLInnerBond")
        self._add_labeled_row(geo_layout, "Inner Bond Length [mm]:", self.txtLInnerBond)

        self.txtDOuterLandingID = QLineEdit()
        self.txtDOuterLandingID.setObjectName("txtDOuterLandingID")
        self._add_labeled_row(geo_layout, "Frame Landing ID [mm]:", self.txtDOuterLandingID)

        self.txtDOuterLandingOD = QLineEdit()
        self.txtDOuterLandingOD.setObjectName("txtDOuterLandingOD")
        self._add_labeled_row(geo_layout, "Spider OD [mm]:", self.txtDOuterLandingOD)

        self.txtHInner = QLineEdit()
        self.txtHInner.setObjectName("txtHInner")
        self._add_labeled_row(geo_layout, "h_inner [mm]:", self.txtHInner)

        self.txtHOuter = QLineEdit()
        self.txtHOuter.setObjectName("txtHOuter")
        self._add_labeled_row(geo_layout, "h_outer [mm]:", self.txtHOuter)

        self.txtT = QLineEdit()
        self.txtT.setObjectName("txtT")
        self._add_labeled_row(geo_layout, "Spider Thickness [mm]:", self.txtT)

        # Fixed geometry labels
        self.lblInnerConeAngle = QLabel("Inner cone angle (θ): 30.0°")
        self.lblInnerConeAngle.setObjectName("lblInnerConeAngle")
        geo_layout.addWidget(self.lblInnerConeAngle)

        self.lblNumberOfPeaks = QLabel("Number of peaks: 7")
        self.lblNumberOfPeaks.setObjectName("lblNumberOfPeaks")
        geo_layout.addWidget(self.lblNumberOfPeaks)

        # Material selection
        mat_layout = QHBoxLayout()
        mat_layout.addWidget(QLabel("Material:"))
        self.cmbMaterial = QComboBox()
        self.cmbMaterial.setObjectName("cmbMaterial")
        mat_layout.addWidget(self.cmbMaterial)
        geo_layout.addLayout(mat_layout)

        self.lblYoungsModulus = QLabel("Young's Modulus: —")
        self.lblYoungsModulus.setObjectName("lblYoungsModulus")
        geo_layout.addWidget(self.lblYoungsModulus)

        self.lblPoissonsRatio = QLabel("Poisson's Ratio: —")
        self.lblPoissonsRatio.setObjectName("lblPoissonsRatio")
        geo_layout.addWidget(self.lblPoissonsRatio)

        self.lblDensity = QLabel("Density: —")
        self.lblDensity.setObjectName("lblDensity")
        geo_layout.addWidget(self.lblDensity)

        left_layout.addWidget(geo_group)

        # --- Mesh Group ---
        mesh_group = QGroupBox("Elmer Mesh")
        mesh_layout = QVBoxLayout(mesh_group)

        self.txtGlobalElementSize = QLineEdit()
        self.txtGlobalElementSize.setObjectName("txtGlobalElementSize")
        self._add_labeled_row(mesh_layout, "Global element size [mm]:", self.txtGlobalElementSize)

        self.txtElementsThroughThickness = QLineEdit()
        self.txtElementsThroughThickness.setObjectName("txtElementsThroughThickness")
        self._add_labeled_row(mesh_layout, "Elements through thickness:", self.txtElementsThroughThickness)

        self.txtMeshRefinementFactor = QLineEdit()
        self.txtMeshRefinementFactor.setObjectName("txtMeshRefinementFactor")
        self._add_labeled_row(mesh_layout, "Mesh refinement factor:", self.txtMeshRefinementFactor)

        self.btnGenerateMesh = QPushButton("Mesh")
        self.btnGenerateMesh.setObjectName("btnGenerateMesh")
        self.btnGenerateMesh.clicked.connect(self._on_generate_mesh)
        mesh_layout.addWidget(self.btnGenerateMesh)

        left_layout.addWidget(mesh_group)

        # --- Solver Group ---
        solver_group = QGroupBox("Elmer Solver")
        solver_layout = QVBoxLayout(solver_group)

        self.btnRunSimulation = QPushButton("Run Simulation")
        self.btnRunSimulation.setObjectName("btnRunSimulation")
        self.btnRunSimulation.clicked.connect(self._on_run_simulation)
        solver_layout.addWidget(self.btnRunSimulation)

        left_layout.addWidget(solver_group)
        left_layout.addStretch()

        # Right panel (tabs)
        self.tabWidget = QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        splitter.addWidget(self.tabWidget)
        splitter.setStretchFactor(1, 1)

        # Tab 0: Cross-Section
        self.canvasCrossSection = FigureCanvas(Figure(figsize=(8, 6)))
        self.tabWidget.addTab(self.canvasCrossSection, "Live Cross-Section")

        # Tab 1: Strain
        self.canvasStrain = FigureCanvas(Figure(figsize=(8, 6)))
        self.tabWidget.addTab(self.canvasStrain, "Strain")

        # Tab 2: Stress
        self.canvasStress = FigureCanvas(Figure(figsize=(8, 6)))
        self.tabWidget.addTab(self.canvasStress, "Stress")

        # Tab 3: Force vs. Deflection
        self.canvasForce = FigureCanvas(Figure(figsize=(8, 6)))
        self.tabWidget.addTab(self.canvasForce, "Force vs. Deflection")

        # Tab 4: Compliance
        self.canvasCompliance = FigureCanvas(Figure(figsize=(8, 6)))
        self.tabWidget.addTab(self.canvasCompliance, "Compliance")

        # Status bar
        self.statusBar().showMessage("Ready")

        # Wire geometry input events
        for widget in [
            self.txtDInnerSpider, self.txtLInnerBond,
            self.txtDOuterLandingID, self.txtDOuterLandingOD,
            self.txtHInner, self.txtHOuter, self.txtT,
        ]:
            widget.editingFinished.connect(self._on_geometry_changed)

        # Wire mesh control events
        for widget in [
            self.txtGlobalElementSize,
            self.txtElementsThroughThickness,
            self.txtMeshRefinementFactor,
        ]:
            widget.editingFinished.connect(self._on_mesh_control_changed)

        # Material combo
        self.cmbMaterial.currentIndexChanged.connect(self._on_material_changed)

        # Populate material combo
        self._populate_material_combo()

    def _add_labeled_row(self, layout, label_text, widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(widget)
        layout.addLayout(row)

    # -----------------------------------------------------------------------
    # Menu
    # -----------------------------------------------------------------------
    def _init_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.menuAction().setObjectName("menuFile")

        self.actionNew = QAction("New", self)
        self.actionNew.setObjectName("actionNew")
        self.actionNew.setShortcut(QKeySequence("Ctrl+N"))
        self.actionNew.triggered.connect(self._on_new_design)
        file_menu.addAction(self.actionNew)

        self.actionOpenDesign = QAction("Open Design...", self)
        self.actionOpenDesign.setObjectName("actionOpenDesign")
        self.actionOpenDesign.setShortcut(QKeySequence("Ctrl+O"))
        self.actionOpenDesign.triggered.connect(self._on_open_design)
        file_menu.addAction(self.actionOpenDesign)

        self.actionSaveDesign = QAction("Save Design...", self)
        self.actionSaveDesign.setObjectName("actionSaveDesign")
        self.actionSaveDesign.setShortcut(QKeySequence("Ctrl+S"))
        self.actionSaveDesign.triggered.connect(self._on_save_design)
        file_menu.addAction(self.actionSaveDesign)

        self.actionDeleteDesign = QAction("Delete Design...", self)
        self.actionDeleteDesign.setObjectName("actionDeleteDesign")
        self.actionDeleteDesign.triggered.connect(self._on_delete_design)
        file_menu.addAction(self.actionDeleteDesign)

        actionSeparator = file_menu.addSeparator()
        actionSeparator.setObjectName("actionSeparator")

        export_menu = file_menu.addMenu("Export")
        export_menu.menuAction().setObjectName("menuExport")

        self.actionExportCrossSectionPng = QAction("Cross-Section PNG...", self)
        self.actionExportCrossSectionPng.setObjectName("actionExportCrossSectionPng")
        self.actionExportCrossSectionPng.triggered.connect(self._on_export_png)
        export_menu.addAction(self.actionExportCrossSectionPng)

        self.actionExportForceDeflectionCsv = QAction("Force-Deflection CSV...", self)
        self.actionExportForceDeflectionCsv.setObjectName("actionExportForceDeflectionCsv")
        self.actionExportForceDeflectionCsv.triggered.connect(self._on_export_force_csv)
        export_menu.addAction(self.actionExportForceDeflectionCsv)

        self.actionExportComplianceCsv = QAction("Compliance CSV...", self)
        self.actionExportComplianceCsv.setObjectName("actionExportComplianceCsv")
        self.actionExportComplianceCsv.triggered.connect(self._on_export_compliance_csv)
        export_menu.addAction(self.actionExportComplianceCsv)

        self.actionExportResultsJson = QAction("Results Summary JSON...", self)
        self.actionExportResultsJson.setObjectName("actionExportResultsJson")
        self.actionExportResultsJson.triggered.connect(self._on_export_json)
        export_menu.addAction(self.actionExportResultsJson)

        self.actionExportDatabase = QAction("Database Backup...", self)
        self.actionExportDatabase.setObjectName("actionExportDatabase")
        self.actionExportDatabase.triggered.connect(self._on_export_database)
        export_menu.addAction(self.actionExportDatabase)

        import_menu = file_menu.addMenu("Import")
        import_menu.menuAction().setObjectName("menuImport")

        self.actionImportDatabase = QAction("Database Backup...", self)
        self.actionImportDatabase.setObjectName("actionImportDatabase")
        self.actionImportDatabase.triggered.connect(self._on_import_database)
        import_menu.addAction(self.actionImportDatabase)

        # Setup menu
        setup_menu = menubar.addMenu("Setup")
        setup_menu.menuAction().setObjectName("menuSetup")

        self.actionSetElmerSolverPath = QAction("ElmerSolver executable path...", self)
        self.actionSetElmerSolverPath.setObjectName("actionSetElmerSolverPath")
        self.actionSetElmerSolverPath.triggered.connect(self._on_set_solver_path)
        setup_menu.addAction(self.actionSetElmerSolverPath)

        self.actionSetElmerGridPath = QAction("ElmerGrid executable path...", self)
        self.actionSetElmerGridPath.setObjectName("actionSetElmerGridPath")
        self.actionSetElmerGridPath.triggered.connect(self._on_set_grid_path)
        setup_menu.addAction(self.actionSetElmerGridPath)

        self.actionSetWorkingDirectory = QAction("Working directory...", self)
        self.actionSetWorkingDirectory.setObjectName("actionSetWorkingDirectory")
        self.actionSetWorkingDirectory.triggered.connect(self._on_set_working_dir)
        setup_menu.addAction(self.actionSetWorkingDirectory)

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.menuAction().setObjectName("menuHelp")

        self.actionAbout = QAction("About", self)
        self.actionAbout.setObjectName("actionAbout")
        self.actionAbout.setShortcut(QKeySequence("F1"))
        self.actionAbout.triggered.connect(self._on_about)
        help_menu.addAction(self.actionAbout)

    def _init_shortcuts(self):
        # Mesh shortcut (Ctrl+M)
        self.actionMesh = QAction("Mesh", self)
        self.actionMesh.setObjectName("actionMesh")
        self.actionMesh.setShortcut(QKeySequence("Ctrl+M"))
        self.actionMesh.triggered.connect(self._on_generate_mesh)
        self.addAction(self.actionMesh)

        # Run shortcut (Ctrl+R)
        self.actionRun = QAction("Run Simulation", self)
        self.actionRun.setObjectName("actionRun")
        self.actionRun.setShortcut(QKeySequence("Ctrl+R"))
        self.actionRun.triggered.connect(self._on_run_simulation)
        self.addAction(self.actionRun)

    # -----------------------------------------------------------------------
    # Population helpers
    # -----------------------------------------------------------------------
    def _populate_material_combo(self):
        self.cmbMaterial.clear()
        try:
            materials = list_available_spider_materials()
        except Exception:
            materials = []
        for mat in materials:
            self.cmbMaterial.addItem(mat["name"])
        # Select default
        index = self.cmbMaterial.findText(self.design.material_name)
        if index >= 0:
            self.cmbMaterial.setCurrentIndex(index)
        self._update_material_labels()

    def _update_material_labels(self):
        self.lblYoungsModulus.setText(f"Young's Modulus: {self.design.youngs_modulus:.1f} MPa")
        self.lblPoissonsRatio.setText(f"Poisson's Ratio: {self.design.poissons_ratio:.2f}")
        self.lblDensity.setText(f"Density: {self.design.density:.1f} kg/m³")

    def _populate_fields_from_design(self):
        self.txtDInnerSpider.setText(str(self.design.D_inner_spider))
        self.txtLInnerBond.setText(str(self.design.L_inner_bond))
        self.txtDOuterLandingID.setText(str(self.design.D_outer_landing_ID))
        self.txtDOuterLandingOD.setText(str(self.design.D_outer_landing_OD))
        self.txtHInner.setText(str(self.design.h_inner))
        self.txtHOuter.setText(str(self.design.h_outer))
        self.txtT.setText(str(self.design.t))
        self.txtGlobalElementSize.setText(str(self.design.global_element_size))
        self.txtElementsThroughThickness.setText(str(self.design.elements_through_thickness))
        self.txtMeshRefinementFactor.setText(str(self.design.mesh_refinement_factor))

    # -----------------------------------------------------------------------
    # Geometry handling
    # -----------------------------------------------------------------------
    def _on_geometry_changed(self):
        sender = self.sender()
        if not isinstance(sender, QLineEdit):
            return

        field_map = {
            self.txtDInnerSpider: ("D_inner_spider", float),
            self.txtLInnerBond: ("L_inner_bond", float),
            self.txtDOuterLandingID: ("D_outer_landing_ID", float),
            self.txtDOuterLandingOD: ("D_outer_landing_OD", float),
            self.txtHInner: ("h_inner", float),
            self.txtHOuter: ("h_outer", float),
            self.txtT: ("t", float),
        }

        field_name, cast = field_map.get(sender, (None, None))
        if field_name is None:
            return

        try:
            value = cast(sender.text())
        except ValueError:
            sender.setStyleSheet("background-color: red;")
            return

        # Validate geometry before applying
        temp_design = self.design
        temp_design = update_geometry_parameter(temp_design, field_name, value)
        valid, msg = api_module.validate_geometry(temp_design)
        if not valid:
            sender.setStyleSheet("background-color: red;")
            self.statusBar().showMessage(f"Geometry error: {msg}")
            return

        sender.setStyleSheet("")
        self.design = temp_design
        self.statusBar().showMessage("Ready")
        self._update_cross_section_tab()
        self._update_simulation_tab_state()

    # -----------------------------------------------------------------------
    # Material handling
    # -----------------------------------------------------------------------
    def _on_material_changed(self):
        material_name = self.cmbMaterial.currentText()
        if not material_name:
            return
        try:
            self.design = update_material_property(self.design, material_name)
        except ValueError as exc:
            QMessageBox.warning(self, "Material Error", str(exc))
            return
        self._update_material_labels()

    # -----------------------------------------------------------------------
    # Mesh control handling
    # -----------------------------------------------------------------------
    def _on_mesh_control_changed(self):
        sender = self.sender()
        field_map = {
            self.txtGlobalElementSize: ("global_element_size", float),
            self.txtElementsThroughThickness: ("elements_through_thickness", int),
            self.txtMeshRefinementFactor: ("mesh_refinement_factor", float),
        }
        field_name, cast = field_map.get(sender, (None, None))
        if field_name is None:
            return
        try:
            value = cast(sender.text())
        except ValueError:
            return
        self.design = update_mesh_control(self.design, field_name, value)
        self._update_simulation_tab_state()

    # -----------------------------------------------------------------------
    # Plotting
    # -----------------------------------------------------------------------
    def _update_cross_section_tab(self):
        fig = self.canvasCrossSection.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if self.design.profile_r and self.design.profile_z:
            ax.fill(
                self.design.profile_r,
                self.design.profile_z,
                color="lightcoral",
                edgecolor="darkred",
                linewidth=2,
                alpha=0.5,
            )

        ax.set_aspect("equal")
        ax.set_xlabel("Radial Distance r [mm]")
        ax.set_ylabel("Axial Distance z [mm]")
        ax.set_title("Spider Cross-Section")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self.canvasCrossSection.draw()

    def _update_result_plots(self):
        # Strain
        fig = self.canvasStrain.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_title("Strain")
        ax.set_xlabel("r [mm]")
        ax.set_ylabel("z [mm]")
        fig.tight_layout()
        self.canvasStrain.draw()

        # Stress
        fig = self.canvasStress.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_title("Stress")
        ax.set_xlabel("r [mm]")
        ax.set_ylabel("z [mm]")
        fig.tight_layout()
        self.canvasStress.draw()

        # Force vs Deflection
        fig = self.canvasForce.figure
        fig.clear()
        ax = fig.add_subplot(111)
        if self.design.force_deflection_data:
            inward = [d for d in self.design.force_deflection_data if d.get("direction") == "inward"]
            outward = [d for d in self.design.force_deflection_data if d.get("direction") == "outward"]
            if inward:
                ax.plot([d["displacement_mm"] for d in inward], [d["force_N"] for d in inward], label="Inward")
            if outward:
                ax.plot([d["displacement_mm"] for d in outward], [d["force_N"] for d in outward], label="Outward")
            ax.legend()
        ax.set_title("Force vs. Deflection")
        ax.set_xlabel("Displacement [mm]")
        ax.set_ylabel("Force [N]")
        fig.tight_layout()
        self.canvasForce.draw()

        # Compliance
        fig = self.canvasCompliance.figure
        fig.clear()
        ax = fig.add_subplot(111)
        if self.design.compliance_data:
            inward = [d for d in self.design.compliance_data if d.get("direction") == "inward"]
            outward = [d for d in self.design.compliance_data if d.get("direction") == "outward"]
            if inward:
                ax.plot([d["displacement_mm"] for d in inward], [d["compliance_mm_per_N"] for d in inward], label="Inward")
            if outward:
                ax.plot([d["displacement_mm"] for d in outward], [d["compliance_mm_per_N"] for d in outward], label="Outward")
            ax.legend()
        ax.set_title("Compliance")
        ax.set_xlabel("Displacement [mm]")
        ax.set_ylabel("Compliance [mm/N]")
        fig.tight_layout()
        self.canvasCompliance.draw()

    # -----------------------------------------------------------------------
    # Simulation state
    # -----------------------------------------------------------------------
    def _update_simulation_tab_state(self):
        has_mesh = self.design.mesh_generated
        has_sim = self.design.simulation_complete
        self.btnRunSimulation.setEnabled(has_mesh)
        for i in range(1, 5):
            self.tabWidget.setTabEnabled(i, has_sim)

    # -----------------------------------------------------------------------
    # Button handlers
    # -----------------------------------------------------------------------
    def _on_generate_mesh(self):
        self.statusBar().showMessage("Meshing...")
        QApplication.processEvents()
        try:
            self.design = generate_mesh(self.design)
            self.statusBar().showMessage("Mesh generated.")
        except Exception as exc:
            QMessageBox.critical(self, "Mesh Error", str(exc))
            self.statusBar().showMessage("Meshing failed.")
            return
        self._update_simulation_tab_state()
        self._update_cross_section_tab()

    def _on_run_simulation(self):
        if not self.design.mesh_generated:
            QMessageBox.information(
                self,
                "Patience, young grasshopper",
                "You can't run a simulation without a mesh. That's like trying to bake a cake without flour.\n\n"
                "Press the Mesh button first.",
            )
            return

        self.statusBar().showMessage("Running Elmer...")
        QApplication.processEvents()
        try:
            self.design = run_simulation(self.design)
            self.statusBar().showMessage("Simulation complete.")
        except Exception as exc:
            QMessageBox.critical(self, "Simulation Error", str(exc))
            self.statusBar().showMessage("Simulation failed.")
            return
        self._update_simulation_tab_state()
        self._update_result_plots()

    # -----------------------------------------------------------------------
    # Menu handlers
    # -----------------------------------------------------------------------
    def _on_new_design(self):
        self.design = create_design()
        self._populate_fields_from_design()
        self._populate_material_combo()
        self._update_cross_section_tab()
        self._update_simulation_tab_state()
        self.statusBar().showMessage("Ready")

    def _on_open_design(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Design Database", "", "SQLite (*.db)")
        if not path:
            return
        try:
            designs = api_module.list_designs(db_path=path)
        except Exception as exc:
            self.statusBar().showMessage(f"Failed to read designs: {exc}")
            return
        if not designs:
            self.statusBar().showMessage("No saved designs found in selected file.")
            return
        names = [d["name"] for d in designs]
        name, ok = QInputDialog.getItem(self, "Open Design", "Select design:", names, 0, False)
        if not ok or not name:
            return
        design_id = next(d["id"] for d in designs if d["name"] == name)
        try:
            self.design = api_module.load_design(design_id, db_path=path)
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", str(exc))
            return
        self._populate_fields_from_design()
        self._populate_material_combo()
        self._update_cross_section_tab()
        self._update_simulation_tab_state()
        self.statusBar().showMessage(f"Loaded design: {name}")

    def _on_save_design(self):
        name, ok = QInputDialog.getText(self, "Save Design", "Design name:")
        if not ok or not name:
            return
        self.design.name = name
        try:
            design_id = save_design(self.design)
            QMessageBox.information(self, "Save Design", f"Design saved with ID {design_id}.")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    def _on_delete_design(self):
        designs = list_designs()
        if not designs:
            self.statusBar().showMessage("No saved designs to delete.")
            return
        names = [d["name"] for d in designs]
        name, ok = QInputDialog.getItem(self, "Delete Design", "Select design:", names, 0, False)
        if not ok or not name:
            return
        design_id = next(d["id"] for d in designs if d["name"] == name)
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete design '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_design(design_id)
            QMessageBox.information(self, "Delete Design", "Design deleted.")
        except Exception as exc:
            QMessageBox.critical(self, "Delete Error", str(exc))

    def _on_export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Cross-Section PNG", "", "PNG (*.png)")
        if not path:
            return
        try:
            export_cross_section_png(self.design, path, show_mesh=False)
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_export_force_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Force-Deflection CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            export_force_deflection_csv(self.design, path)
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_export_compliance_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Compliance CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            export_compliance_csv(self.design, path)
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Results JSON", "", "JSON (*.json)")
        if not path:
            return
        try:
            export_results_json(self.design, path)
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_export_database(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Database", "", "SQLite (*.db)")
        if not path:
            return
        try:
            export_database(path)
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_import_database(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Database", "", "SQLite (*.db)")
        if not path:
            return
        try:
            import_database(path, merge=False)
            QMessageBox.information(self, "Import Database", "Database imported successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Import Error", str(exc))

    def _on_set_solver_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ElmerSolver.exe", "", "Executable (*.exe)")
        if path:
            set_elmer_solver_path(path)

    def _on_set_grid_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ElmerGrid.exe", "", "Executable (*.exe)")
        if path:
            set_elmergrid_path(path)

    def _on_set_working_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            set_working_directory(path)
            self.design.working_directory = path

    def _on_about(self):
        dlg = AboutDialog(parent=self)
        dlg.exec()
