# SpiderFEA — Application Definition

**Version:** 0.1.0  
**Revision Type:** new_project  
**Workflow ID:** wvc_20260529_061307  
**Date:** 2026-05-29  
**Status:** FINAL

---

## 1. Application Overview

### 1.1 Purpose
SpiderFEA is a standalone Windows desktop application that serves as a graphical frontend for Finite Element Analysis (FEA) simulations of loudspeaker transducer spiders (dampers) using the open-source **ElmerFEM** multiphysics solver. The application focuses on **2D axisymmetric mechanical stress/strain analysis** of the flexible corrugated disc that centers the voice-coil former within the magnetic gap and provides restoring force.

The program parametrically builds a 2D axisymmetric r-z cross-section of the spider from seven independent geometric control parameters, generates a finite element mesh via **Gmsh**, drives Elmer's **Solid Mechanics** solver to compute displacement-induced stress, strain, and reaction force, and visualizes the deformed geometry, force-deflection characteristics, and compliance curves.

### 1.2 Target User
Loudspeaker transducer design engineers and technicians who need to predict the mechanical behavior (stiffness, stress concentration, force-deflection linearity, compliance) of a spider geometry before manufacturing.

### 1.3 Key Value Proposition
- Parametric spider geometry editor with live preview — see the cross-section update instantly as dimensions change.
- One-click mesh generation and FEA execution through an intuitive GUI.
- Visualizes strain distribution, stress distribution, force vs. displacement, and compliance curves to identify nonlinearities and potential failure points.
- Eliminates manual Elmer SIF editing and Gmsh scripting for standard spider analyses.

### 1.4 Platform
Windows 10/11 desktop application. Single-user, local execution. Single-design execution (no side-by-side design comparison).

---

## 2. UI Layout

The main window is a single PyQt6 `QMainWindow` with a horizontal splitter layout:
- **Left side panel**: fixed-width (~380 px) scrollable `QScrollArea` containing stacked `QGroupBox` widgets.
- **Right panel**: `QTabWidget` occupying the remaining width, containing matplotlib `FigureCanvas` widgets.
- **Menu bar**: File, Setup, Help.
- **Status bar**: Shows "Ready", "Meshing...", "Running Elmer...", or error messages.

### 2.1 Menu Bar

#### File Menu
- New — reset all inputs to default values
- Open Design — load a saved design from SQLite
- Save Design — save current design to SQLite
- Delete Design — delete a saved design from SQLite
- Export → Cross-Section PNG, Force-Deflection CSV, Compliance CSV, Results Summary JSON

#### Setup Menu *(Elmer controls)*
- `ElmerSolver executable path` — string/path (default: `C:\Users\terav\ElmerFEM\bin\ElmerSolver.exe`)
- `ElmerGrid executable path` — string/path (default: `C:\Users\terav\ElmerFEM\bin\ElmerGrid.exe`)
- `Working directory` — string/path (default: `C:\ElmerFEA\SpiderFEA\`)
- `Number of processors` — `QSpinBox`, default `1`

#### Help Menu
- About — shows application version and credits

### 2.2 Left Panel Sections (top to bottom)

#### Section A: Spider Geometry

##### Input Parameters *(no scrollbars, text entry only, width for 3 sig-figs)*
| Parameter | Default | Unit | Widget |
|-----------|---------|------|--------|
| `Spider ID` (D_inner) | 75.0 | mm | `QLineEdit` |
| `Inner Bond Length` (L_bond) | 2.5 | mm | `QLineEdit` |
| `Frame Landing ID` (D_outer_ID) | 110.0 | mm | `QLineEdit` |
| `Spider OD` (D_outer_OD) | 122.0 | mm | `QLineEdit` |
| `h_inner` | 7.0 | mm | `QLineEdit` |
| `h_outer` | 10.0 | mm | `QLineEdit` |
| `Spider Thickness` (t) | 0.75 | mm | `QLineEdit` |

> Tab order follows the list above. Moving focus (Tab or click-away) triggers geometry recalculation.

##### Fixed Geometry *(displayed for reference, not editable)*
| Parameter | Value | Unit | Widget |
|-----------|-------|------|--------|
| `Inner cone angle` (θ) | 30.0 | ° | `QLabel` (read-only) |
| `Number of peaks` (n_peaks) | 7 | — | `QLabel` (read-only) |

##### Material Selection
| Parameter | Default | Widget |
|-----------|---------|--------|
| `Material` | "Phenolic-Treated Cloth" | `QComboBox` (dropdown filtered to `spider` category) |

> When a material is selected, the program automatically loads `Young's Modulus`, `Poisson's Ratio`, and `Density` from the materials database. These values are displayed as read-only labels (not editable fields). Spider materials use a **linear elastic** material model.

#### Section B: Elmer Mesh

##### Mesh Controls
| Parameter | Default | Unit | Widget |
|-----------|---------|------|--------|
| `Global element size` | 0.5 | mm | `QLineEdit` |
| `Elements through thickness` | 4 | — | `QLineEdit` |
| `Mesh refinement factor` | 1.0 | — | `QLineEdit` |

##### Action
- **Mesh** button — generates Gmsh mesh and displays it overlaid on the live cross-section. On successful mesh generation, the **Run Simulation** button is enabled.

#### Section C: Elmer Solver

##### Action
- **Run Simulation** button — executes the Elmer solid-mechanics solve with stepped displacement. Disabled until a valid mesh exists. If pressed while disabled, a snarky popup message is displayed.

### 2.3 Right Panel Tabs

1. **Live Cross-Section** *(always enabled)* — Matplotlib plot of the 2D axisymmetric r-z spider profile. Shows the filled polygon with key dimensions annotated. After meshing, the mesh edges/nodes are overlaid. Before meshing, no mesh is shown. The plot does not show mesh during live geometry update. Auto-fits to geometry bounds with locked 1:1 aspect ratio.
2. **Strain** *(disabled until simulation complete)* — Matplotlib plot of the deformed cross-section with a color-mapped equivalent strain (ε) contour. Shows both inward and outward extreme deflection shapes. Plot is zoomed tightly to the geometry bounds with no blank space.
3. **Stress** *(disabled until simulation complete)* — Matplotlib plot of the deformed cross-section with a color-mapped von Mises stress (σ) contour. Shows both inward and outward extreme deflection shapes. Plot is zoomed tightly to the geometry bounds with no blank space.
4. **Force vs. Deflection** *(disabled until simulation complete)* — Matplotlib plot with vertical axis Force (N) and horizontal axis displacement (mm), centered at x = 0. Shows two curves: inward (negative x) and outward (positive x) deflection. Plot is zoomed tightly to data bounds with no blank space.
5. **Compliance** *(disabled until simulation complete)* — Matplotlib plot with vertical axis compliance (mm/N) and horizontal axis displacement (mm). Shows inward and outward curves. Plot is zoomed tightly to data bounds with no blank space.

### 2.4 Error Visualization
- Invalid geometry inputs → offending `QLineEdit` backgrounds turn red, cross-section canvas is cleared.
- Simulation failure → status bar shows error text; result tabs remain disabled.

---

## 3. User Actions

| # | Action | Description | Trigger |
|---|--------|-------------|---------|
| 3.1 | **Change any geometry input parameter** | User types a new value in any of the 7 geometry input fields. On focus loss (Tab or click-away), the geometry engine recalculates the profile. If valid, the live cross-section updates. If invalid, the field turns red and cross-section clears. | `editingFinished` on geometry `QLineEdit` |
| 3.2 | **Change material selection** | User selects a different material from the dropdown. The application loads E, ν, and ρ from the materials database automatically. No immediate geometry update; values are stored for the next simulation run. | `currentIndexChanged` on material `QComboBox` |
| 3.3 | **Change any mesh control** | User edits global element size, elements through thickness, or refinement factor. No immediate action; values are used on next mesh generation. Changing any mesh control re-disables the **Run Simulation** button until **Mesh** is pressed again. | `editingFinished` on mesh `QLineEdit` |
| 3.4 | **Generate Mesh** | User clicks the **Mesh** button. The application builds the mesh via the Gmsh Python API, converts it to Elmer format via ElmerGrid, and overlays the mesh on the live cross-section tab. Enables the **Run Simulation** button on success. | Button click |
| 3.5 | **Run Simulation** | User clicks the **Run Simulation** button. The application writes the Elmer SIF file (Solid Mechanics, axisymmetric, stepped displacement boundary condition), launches ElmerSolver, parses VTU/EP result files, extracts stress/strain/force/compliance data, and enables the result tabs. Disabled if no valid mesh exists; shows a snarky popup if pressed while disabled. | Button click |
| 3.6 | **New Design** | Resets all inputs to default values. | File → New |
| 3.7 | **Save Design** | Stores current input parameters and mesh controls to the SQLite database as a named design. Simulation state is not saved. | File → Save Design |
| 3.8 | **Load Design** | Retrieves a previously saved design from SQLite and populates all fields. Simulation results are not loaded; the application automatically re-runs simulation after loading. | File → Open Design |
| 3.9 | **Delete Design** | Removes a saved design from the database. | File → Delete Design |
| 3.10 | **Export Cross-Section PNG** | Saves the current live cross-section plot (with or without mesh overlay) to a PNG file. | File → Export → Cross-Section PNG |
| 3.11 | **Export Force-Deflection CSV** | Writes force (N) vs displacement (mm) data to a CSV file with columns `displacement_mm`, `force_N`, `direction`. | File → Export → Force-Deflection CSV |
| 3.12 | **Export Compliance CSV** | Writes compliance (mm/N) vs displacement (mm) data to a CSV file with columns `displacement_mm`, `compliance_mm_per_N`, `direction`. | File → Export → Compliance CSV |
| 3.13 | **Export Results Summary** | Writes all input parameters, peak stress/strain, and max force to a JSON file. | File → Export → Results Summary |
| 3.14 | **Switch to result tab** | User clicks a result tab (Strain, Stress, Force vs. Deflection, Compliance). Only selectable after a successful simulation. | Tab click |
| 3.15 | **Set ElmerSolver path** | User browses to select the ElmerSolver executable location. | Setup menu → ElmerSolver executable path |
| 3.16 | **Set ElmerGrid path** | User browses to select the ElmerGrid executable location. | Setup menu → ElmerGrid executable path |
| 3.17 | **Set Working Directory** | User browses to select the working directory for Elmer files. | Setup menu → Working directory |
| 3.18 | **View About** | Shows application version and credits. *(UI-only; no API function required)* | Help → About |
| 3.19 | **Export Database** | Exports the entire SQLite designs database to a backup file for external storage/restore. | File → Export → Database Backup |
| 3.20 | **Import Database** | Imports a previously exported database backup file, replacing or merging the current designs. | File → Import → Database Backup |

### 3.1 Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Design |
| `Ctrl+O` | Open Design |
| `Ctrl+S` | Save Design |
| `Ctrl+M` | Generate Mesh |
| `Ctrl+R` | Run Simulation |
| `F1` | About |

---

## 4. Data Model

### 4.1 Persistence
- **SQLite** local database at `~/AppData/Local/SpiderFEA/spiderfea.db`.
- Table: `designs` — stores serialized JSON of all input parameters and mesh controls per design. Simulation results are NOT persisted.
- Table: `settings` — stores Elmer executable paths, working directory, and window geometry.
- The database supports export/import for backup and restore operations.

### 4.2 Materials Database
- **External SQLite database** at `C:\Users\terav\AgentGlobal\materials\loudspeaker_materials.db`.
- The application queries this database for materials where `category = 'spider'`.
- Available spider materials:

| Material Name | E (GPa) | ν | ρ (kg/m³) | model_type |
|---------------|---------|---|-----------|------------|
| Phenolic-Treated Cloth | 5.0 | 0.35 | 1200 | linear_elastic |
| Nomex Spider | 3.5 | 0.30 | 720 | linear_elastic |

> Spider materials use **linear elastic** model only. Hyperelastic (e.g., Mooney-Rivlin) is for rubbers/surrounds ONLY and must not be used for spiders.

### 4.3 Primary Entity: `SpiderDesign`
A dataclass representing one spider design.

#### Input Parameters (geometry)
| Field | Type | Default | Unit | UI Section |
|-------|------|---------|------|------------|
| `D_inner_spider` | `float` | `75.0` | mm | Spider Geometry |
| `L_inner_bond` | `float` | `2.5` | mm | Spider Geometry |
| `D_outer_landing_ID` | `float` | `110.0` | mm | Spider Geometry |
| `D_outer_landing_OD` | `float` | `122.0` | mm | Spider Geometry |
| `h_inner` | `float` | `7.0` | mm | Spider Geometry |
| `h_outer` | `float` | `10.0` | mm | Spider Geometry |
| `t` | `float` | `0.75` | mm | Spider Geometry |

#### Input Parameters (material)
| Field | Type | Default | Unit | UI Section | Source |
|-------|------|---------|------|------------|--------|
| `material_name` | `str` | `"Phenolic-Treated Cloth"` | — | Spider Geometry | Dropdown from materials DB |
| `youngs_modulus` | `float` | `5000.0` | MPa | Spider Geometry | Auto-loaded from DB |
| `poissons_ratio` | `float` | `0.35` | — | Spider Geometry | Auto-loaded from DB |
| `density` | `float` | `1200.0` | kg/m³ | Spider Geometry | Auto-loaded from DB |
| `model_type` | `str` | `"linear_elastic"` | — | Spider Geometry | Auto-loaded from DB |

#### Input Parameters (mesh)
| Field | Type | Default | Unit | UI Section |
|-------|------|---------|------|------------|
| `global_element_size` | `float` | `0.5` | mm | Elmer Mesh |
| `elements_through_thickness` | `int` | `4` | — | Elmer Mesh |
| `mesh_refinement_factor` | `float` | `1.0` | — | Elmer Mesh |

#### Input Parameters (setup)
| Field | Type | Default | Unit | UI Section |
|-------|------|---------|------|------------|
| `elmer_solver_path` | `str` | `"C:\\Users\\terav\\ElmerFEM\\bin\\ElmerSolver.exe"` | — | Setup menu |
| `elmergrid_path` | `str` | `"C:\\Users\\terav\\ElmerFEM\\bin\\ElmerGrid.exe"` | — | Setup menu |
| `working_directory` | `str` | `"C:\\ElmerFEA\\SpiderFEA\\"` | — | Setup menu |
| `num_processors` | `int` | `1` | — | Setup menu |

#### Fixed Geometry *(stored as constants, displayed for reference)*
| Field | Type | Value | Unit |
|-------|------|-------|------|
| `theta_deg` | `float` | `30.0` | ° |
| `n_peaks` | `int` | `7` | — |

#### Derived Parameters *(computed internally, NOT displayed in UI)*
| Field | Type | Formula | Unit |
|-------|------|---------|------|
| `R_inner_spider` | `float` | `D_inner_spider / 2.0` | mm |
| `R_outer_landing_ID` | `float` | `D_outer_landing_ID / 2.0` | mm |
| `R_outer_landing_OD` | `float` | `D_outer_landing_OD / 2.0` | mm |
| `R_inner_corr` | `float` | `R_inner_spider + L_inner_bond * cos(radians(theta_deg))` | mm |
| `z_inner_cone` | `float` | `-L_inner_bond * sin(radians(theta_deg))` | mm |
| `extension` | `float` | `R_outer_landing_OD - R_outer_landing_ID` | mm |

#### Geometry Profile Arrays
| Field | Type | Description |
|-------|------|-------------|
| `profile_r` | `list[float]` | Ordered r-coordinates of the closed profile polygon (lower surface → outer edge → upper surface → inner edge) |
| `profile_z` | `list[float]` | Ordered z-coordinates of the closed profile polygon |

#### Simulation State Flags
| Field | Type | Description |
|-------|------|-------------|
| `mesh_generated` | `bool` | True if a mesh has been successfully generated |
| `simulation_complete` | `bool` | True if the solver finished successfully |

#### Simulation Results (populated after Run Simulation)
| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `max_von_mises_stress` | `float` | MPa | Peak von Mises stress across all load steps |
| `max_strain` | `float` | — | Peak equivalent strain across all load steps |
| `force_deflection_data` | `list[dict]` | — | Each dict: `{"displacement_mm": float, "force_N": float, "direction": str}` |
| `compliance_data` | `list[dict]` | — | Each dict: `{"displacement_mm": float, "compliance_mm_per_N": float, "direction": str}` |
| `strain_field_data` | `list[tuple]` | — | (r, z, strain) tuples for the extreme deflection steps |
| `stress_field_data` | `list[tuple]` | — | (r, z, stress) tuples for the extreme deflection steps |

### 4.4 Geometry Derivation Formulas (Exact)

> **CRITICAL CONSTRAINT**: All formulas below must be implemented **exactly** as shown. No algebraic substitution, no simplification, no "correction" of apparent typos. Implement character-for-character and flag any concerns in a code comment.

The following formulas are extracted directly from `SpiderGeomContext.md` and `src/spider_profile.py`. They must be implemented character-for-character.

```python
import numpy as np
from math import cos, sin, radians, sqrt, pi

theta = radians(theta_deg)
n_peaks = 7  # fixed; must be odd positive integer

# Radii from diameters
R_inner_spider     = D_inner_spider / 2.0
R_outer_landing_ID = D_outer_landing_ID / 2.0
R_outer_landing_OD = D_outer_landing_OD / 2.0

# Inner cone
R_inner_corr = R_inner_spider + L_inner_bond * cos(theta)
z_inner_cone = -L_inner_bond * sin(theta)

# Outer extension
extension = R_outer_landing_OD - R_outer_landing_ID

# Corrugation centerline
# phase = pi * n_peaks * (r - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
# h(r)  = h_inner + (h_outer - h_inner) * (r - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
# z(r)  = (h(r) / 2) * sin(phase)

# Normal thickness offset
# For each point on centerline (r, z):
#   1. Tangent via central differences: (dr, dz)
#   2. Unit inward normal: n = (dz, -dr) / sqrt(dr**2 + dz**2)
#   3. Lower surface: (r, z) + (t/2) * n
#   4. Upper surface: (r, z) - (t/2) * n
```

### 4.5 Elmer Output Files
After running the simulation, the following files are produced in the working directory:
- `spider.msh` — Gmsh mesh file (generated via Python API)
- `mesh/` — Elmer mesh directory (from ElmerGrid)
- `spider.sif` — Elmer solver input file
- `results/` — Elmer result VTU/EP files
- `force_deflection.csv` — extracted force-displacement data
- `compliance.csv` — extracted compliance data

---

## 5. API Function List

All functions are exported from `src.api` and are the **only** entry points the AI agent should use.

### 5.1 Design Lifecycle

```python
def create_design(name: str = "") -> SpiderDesign
```
Create a new `SpiderDesign` with default geometry, material, and mesh values. Returns the design object.

```python
def save_design(design: SpiderDesign) -> int
```
Serialize `design` to JSON and store in SQLite. Returns the design ID (primary key). Stores input parameters and mesh controls only; simulation results are not persisted.

```python
def load_design(design_id: int) -> SpiderDesign
```
Retrieve a design from SQLite by ID. Returns a populated `SpiderDesign` with input parameters and mesh controls. Simulation results are not loaded; the caller must re-run simulation if results are needed.

```python
def list_designs() -> list[dict]
```
Return a list of all saved designs as dicts with keys `id`, `name`, `updated_at`.

```python
def delete_design(design_id: int) -> None
```
Delete the design from SQLite. Raises `ValueError` if ID not found.

```python
def clone_design(design_id: int, new_name: str = "") -> SpiderDesign
```
Deep-copy an existing design, assign a new name, and return the copy (not yet saved).

### 5.2 Geometry (No Mesh / No Solver)

```python
def update_geometry_parameter(design: SpiderDesign, field_name: str, value: float | int | str) -> SpiderDesign
```
Set a single geometry input field by name (e.g., `"D_inner_spider"`, `"L_inner_bond"`, `"h_inner"`) and trigger `recalculate_profile()`. Returns the updated design.

```python
def recalculate_profile(design: SpiderDesign) -> SpiderDesign
```
Recompute the full 2D profile polygon (`profile_r`, `profile_z`) and all derived parameters from the 7 control inputs using the exact formulas in Section 4.4. Does **not** call Gmsh or Elmer. Returns the updated design.

```python
def validate_geometry(design: SpiderDesign) -> tuple[bool, str]
```
Check whether the current parameters produce a physically realizable geometry (e.g., `D_outer_landing_OD > D_outer_landing_ID > D_inner_spider`, `n_peaks` is odd positive, `h_inner` and `h_outer` are positive). Returns `(True, "")` on success or `(False, error_message)` on failure.

### 5.3 Material Properties

```python
def update_material_property(design: SpiderDesign, material_name: str) -> SpiderDesign
```
Set the material by name, querying the external materials database (`loudspeaker_materials.db`) for the matching `spider` category entry. Automatically loads `youngs_modulus`, `poissons_ratio`, `density`, and `model_type` from the database. Does **not** trigger geometry recalculation. Returns the updated design.

```python
def list_available_spider_materials() -> list[dict]
```
Return a list of all materials in the `spider` category from the external database. Each dict contains keys: `name`, `youngs_modulus`, `poissons_ratio`, `density`, `model_type`.

### 5.4 Mesh Controls

```python
def update_mesh_control(design: SpiderDesign, field_name: str, value: float | int) -> SpiderDesign
```
Set a single mesh control field by name (e.g., `"global_element_size"`, `"elements_through_thickness"`, `"mesh_refinement_factor"`). Does **not** trigger mesh generation. Sets `design.mesh_generated = False` and `design.simulation_complete = False` to enforce re-meshing before next simulation run. Returns the updated design.

### 5.5 Mesh Generation

```python
def generate_mesh(design: SpiderDesign) -> SpiderDesign
```
Build the mesh using the **Gmsh Python API** (not a `.geo` file + subprocess) from the current `profile_r` / `profile_z`, convert to Elmer mesh format via ElmerGrid, and set `design.mesh_generated = True`. Returns the updated design.

```python
def convert_mesh_with_elmergrid(msh_path: str, output_dir: str) -> None
```
Invoke `ElmerGrid` to convert a Gmsh `.msh` file to an Elmer `mesh/` directory.

### 5.6 Elmer Simulation

```python
def run_simulation(design: SpiderDesign) -> SpiderDesign
```
Generate the Elmer SIF file (Solid Mechanics, axisymmetric, stepped displacement boundary condition), launch `ElmerSolver.exe`, parse result files, populate `force_deflection_data`, `compliance_data`, `strain_field_data`, `stress_field_data`, `max_von_mises_stress`, `max_strain`, and set `simulation_complete = True`. Returns the updated design. Raises `RuntimeError` if `design.mesh_generated` is `False`.

```python
def generate_elmer_sif(design: SpiderDesign, directory: str) -> str
```
Write the Elmer SIF file to the given directory. Returns the SIF file path.

```python
def parse_simulation_results(directory: str) -> dict
```
Parse Elmer VTU/EP result files in the given directory. Returns a dict with keys: `force_deflection_data`, `compliance_data`, `max_von_mises_stress`, `max_strain`, `strain_field_data`, `stress_field_data`.

### 5.7 Export

```python
def export_cross_section_png(design: SpiderDesign, filepath: str, show_mesh: bool = False) -> None
```
Render the current cross-section plot to a PNG file. If `show_mesh=True` and a mesh exists, overlay mesh edges.

```python
def export_force_deflection_csv(design: SpiderDesign, filepath: str) -> None
```
Write force-deflection data to a CSV file with columns `displacement_mm`, `force_N`, `direction`.

```python
def export_compliance_csv(design: SpiderDesign, filepath: str) -> None
```
Write compliance data to a CSV file with columns `displacement_mm`, `compliance_mm_per_N`, `direction`.

```python
def export_results_json(design: SpiderDesign, filepath: str) -> None
```
Write a JSON file containing all input parameters, derived dimensions, and simulation results.

### 5.8 Database Backup / Restore

```python
def export_database(backup_path: str) -> None
```
Copy the entire SQLite designs database to the specified backup file path.

```python
def import_database(backup_path: str, merge: bool = False) -> None
```
Import designs from a backup database file. If `merge=False`, replaces the current database. If `merge=True`, merges backup designs into the current database (skip duplicates by name).

### 5.9 Utility

```python
def init_database(db_path: str | None = None) -> None
```
Create the SQLite database and `designs` / `settings` tables if they do not exist. Uses default path if `db_path` is None.

```python
def set_elmer_solver_path(path: str) -> None
```
Update the global setting for the ElmerSolver executable path. Persisted in SQLite settings table.

```python
def set_elmergrid_path(path: str) -> None
```
Update the global setting for the ElmerGrid executable path. Persisted in SQLite settings table.

```python
def set_working_directory(path: str) -> None
```
Update the global setting for the working directory. Persisted in SQLite settings table.

```python
def get_default_values() -> SpiderDesign
```
Return a `SpiderDesign` instance populated with the exact default values listed in Section 4.3.

---

## 6. Toolchain

| Component | Version / Specification |
|-----------|------------------------|
| **Python** | 3.11+ (64-bit) |
| **PyQt6** | 6.6+ |
| **SQLite** | 3.39+ (bundled with Python) |
| **ElmerFEM** | Latest stable (external dependency; `ElmerSolver.exe` and `ElmerGrid.exe` must be present) |
| **Gmsh** | 4.12+ (Gmsh Python API via `gmsh` package; NOT `.geo` file + subprocess) |
| **numpy** | 1.24+ |
| **matplotlib** | 3.8+ (for plots) |
| **pytest** | 8.0+ (test framework) |
| **PyInstaller** | 6.0+ (packaging to standalone `.exe`) |

### 6.1 Elmer Integration Method
- The application builds the mesh using the **Gmsh Python API** directly from the parametric profile arrays (`profile_r`, `profile_z`). No `.geo` file or subprocess invocation of Gmsh is used.
- `ElmerGrid` converts the Gmsh `.msh` to Elmer mesh directory format.
- The application writes an Elmer SIF file defining a 2D axisymmetric **Solid Mechanics** problem.
- Materials: spider solid with linear elastic properties (Young's modulus, Poisson's ratio, density) loaded from the external materials database.
- Boundary conditions:
  - **Outer landing bottom**: fixed (`Displacement 1 = 0`, `Displacement 2 = 0`) — outer landing remains undistorted.
  - **Inner conical bond**: prescribed Z-displacement stepped in 1 mm increments — inner bond remains undistorted (rigid-body displacement).
  - **Symmetry axis** (`r = 0`): standard axisymmetric boundary condition.
- Solver steps:
  1. Start at rest position (0 mm displacement).
  2. Measure reaction force; compute k(0) = ΔF/Δx.
  3. Step inner bond in +Z by 1 mm, solve, record force.
  4. Repeat until k(x) ≥ 4 × k(0).
  5. Return to rest, then step in –Z by 1 mm, repeating the termination criterion.
- Post-processing:
  - Extract nodal displacements, von Mises stress, and equivalent strain from Elmer VTU/EP files.
  - Build force-deflection and compliance curves from reaction forces at each step.
  - Generate matplotlib strain/stress contour plots on the deformed geometry.

### 6.2 Packaging
- `PyInstaller` bundles Python, PyQt6, matplotlib, numpy, and SQLite into a single folder distribution.
- The `dist/` directory must be added to `.gitignore` before the first commit.

### 6.3 Testing
- `pytest` tests for each API function.
- Unit tests for geometry derivation: given the default 7 inputs, the Python calculation must match the reference `spider_profile.py` outputs to within `1e-9` absolute tolerance.
- Mock-based tests for Elmer integration (verify SIF generation and output parsing without requiring Elmer to be installed).
- Mock-based tests for Gmsh integration (verify mesh building logic via Python API without requiring Gmsh to be installed).

---

*End of Definition*
