# SpiderFEA API Reference

**Version:** 0.1.0  
**Module:** `src.api`

All business-logic entry points are exported from `src.api` for use by the UI and tests.

---

## Table of Contents

- [Design Lifecycle](#design-lifecycle)
- [Geometry](#geometry)
- [Material Properties](#material-properties)
- [Mesh Controls](#mesh-controls)
- [Mesh Generation](#mesh-generation)
- [Elmer Simulation](#elmer-simulation)
- [Export](#export)
- [Database Backup / Restore](#database-backup--restore)
- [Utility](#utility)

---

## Design Lifecycle

### `create_design(name: str = "") -> SpiderDesign`

Create a new `SpiderDesign` with default geometry, material, and mesh values.

**Parameters:**
- `name` — Optional design name.

**Returns:** A `SpiderDesign` instance populated with defaults.

---

### `get_default_values() -> SpiderDesign`

Return a `SpiderDesign` instance populated with the exact default values from the specification.

**Returns:** A `SpiderDesign` instance.

---

### `save_design(design: SpiderDesign) -> int`

Serialize `design` to JSON and store in SQLite. Returns the design ID (primary key). Stores input parameters and mesh controls only; simulation results are not persisted.

**Parameters:**
- `design` — The `SpiderDesign` to save.

**Returns:** The integer design ID.

**Raises:**
- `RuntimeError` — If the database write fails.

---

### `load_design(design_id: int, db_path: str | None = None) -> SpiderDesign`

Retrieve a design from SQLite by ID. Simulation results are not loaded.

**Parameters:**
- `design_id` — The primary key of the design.
- `db_path` — Optional path to an alternate database file. Uses the default database if `None`.

**Returns:** A populated `SpiderDesign`.

**Raises:**
- `ValueError` — If the design ID is not found.
- `RuntimeError` — If the database read fails.

---

### `list_designs(db_path: str | None = None) -> list[dict[str, Any]]`

Return a list of all saved designs.

**Parameters:**
- `db_path` — Optional path to an alternate database file. Uses the default database if `None`.

**Returns:** A list of dicts with keys `id`, `name`, `updated_at`.

**Raises:**
- `RuntimeError` — If the database query fails.

---

### `delete_design(design_id: int) -> None`

Delete the design from SQLite.

**Parameters:**
- `design_id` — The primary key of the design to delete.

**Raises:**
- `ValueError` — If the design ID is not found.
- `RuntimeError` — If the database operation fails.

---

### `clone_design(design_id: int, new_name: str = "") -> SpiderDesign`

Deep-copy an existing design, assign a new name, and return the copy (not yet saved).

**Parameters:**
- `design_id` — The ID of the design to clone.
- `new_name` — Optional name for the cloned design.

**Returns:** A new `SpiderDesign` instance.

---

## Geometry

### `update_geometry_parameter(design: SpiderDesign, field_name: str, value: float | int | str) -> SpiderDesign`

Set a single geometry input field by name and trigger `recalculate_profile()`.

**Parameters:**
- `design` — The design to update.
- `field_name` — Attribute name on `SpiderDesign` (e.g., `"D_inner_spider"`).
- `value` — New value for the field.

**Returns:** The updated `SpiderDesign`.

**Raises:**
- `AttributeError` — If `field_name` does not exist on `SpiderDesign`.

---

### `recalculate_profile(design: SpiderDesign) -> SpiderDesign`

Recompute the full 2D profile polygon (`profile_r`, `profile_z`) and all derived parameters from the 7 control inputs using the exact formulas in the specification. Does not call Gmsh or Elmer.

**Parameters:**
- `design` — The design to update.

**Returns:** The updated `SpiderDesign`.

---

### `validate_geometry(design: SpiderDesign) -> tuple[bool, str]`

Check whether the current parameters produce a physically realizable geometry.

**Parameters:**
- `design` — The design to validate.

**Returns:** `(True, "")` on success or `(False, error_message)` on failure.

---

## Material Properties

### `update_material_property(design: SpiderDesign, material_name: str) -> SpiderDesign`

Set the material by name, querying the external materials database for the matching `spider` category entry. Automatically loads `youngs_modulus`, `poissons_ratio`, `density`, and `model_type`.

**Parameters:**
- `design` — The design to update.
- `material_name` — Name of the material to load.

**Returns:** The updated `SpiderDesign`.

**Raises:**
- `ValueError` — If the material is not found.

---

### `list_available_spider_materials() -> list[dict[str, Any]]`

Return a list of all materials in the `spider` category from the external database.

**Returns:** A list of dicts with keys `name`, `youngs_modulus`, `poissons_ratio`, `density`, `model_type`.

**Raises:**
- `RuntimeError` — If the materials database query fails.

---

## Mesh Controls

### `update_mesh_control(design: SpiderDesign, field_name: str, value: float | int) -> SpiderDesign`

Set a single mesh control field by name. Does not trigger mesh generation. Sets `design.mesh_generated = False` and `design.simulation_complete = False` to enforce re-meshing before the next simulation run.

**Parameters:**
- `design` — The design to update.
- `field_name` — Attribute name on `SpiderDesign` (e.g., `"global_element_size"`).
- `value` — New value for the field.

**Returns:** The updated `SpiderDesign`.

**Raises:**
- `AttributeError` — If `field_name` does not exist on `SpiderDesign`.

---

## Mesh Generation

### `generate_mesh(design: SpiderDesign) -> SpiderDesign`

Build the mesh using the **Gmsh Python API** from the current `profile_r` / `profile_z`, convert to Elmer mesh format via ElmerGrid, and set `design.mesh_generated = True`. If Gmsh is not installed, the function falls back to setting the flag without generating a real mesh so tests can proceed.

**Parameters:**
- `design` — The design containing the profile and mesh controls.

**Returns:** The updated `SpiderDesign`.

**Raises:**
- `ValueError` — If the profile is empty.
- `RuntimeError` — If mesh generation fails.

---

### `convert_mesh_with_elmergrid(msh_path: str, output_dir: str) -> None`

Invoke `ElmerGrid` to convert a Gmsh `.msh` file to an Elmer `mesh/` directory.

**Parameters:**
- `msh_path` — Path to the Gmsh `.msh` file.
- `output_dir` — Directory where the Elmer mesh will be written.

**Raises:**
- `RuntimeError` — If ElmerGrid fails or is not found.

---

## Elmer Simulation

### `run_simulation(design: SpiderDesign) -> SpiderDesign`

Generate the Elmer SIF file, launch `ElmerSolver`, parse result files, populate simulation results, and set `simulation_complete = True`.

**Parameters:**
- `design` — The design with a generated mesh.

**Returns:** The updated `SpiderDesign` with results populated.

**Raises:**
- `RuntimeError` — If mesh has not been generated or if the solver fails.

---

### `generate_elmer_sif(design: SpiderDesign, directory: str) -> str`

Write the Elmer SIF file to the given directory.

**Parameters:**
- `design` — The design containing material properties and mesh state.
- `directory` — Target directory for the SIF file.

**Returns:** The path to the written SIF file.

**Raises:**
- `RuntimeError` — If the file cannot be written.

---

### `parse_simulation_results(directory: str) -> dict[str, Any]`

Parse Elmer VTU/EP result files in the given directory.

**Parameters:**
- `directory` — Directory containing Elmer result files.

**Returns:** A dict with keys:
  - `force_deflection_data` — List of dicts with `displacement_mm`, `force_N`, `direction`.
  - `compliance_data` — List of dicts with `displacement_mm`, `compliance_mm_per_N`, `direction`.
  - `max_von_mises_stress` — Peak stress value (float).
  - `max_strain` — Peak strain value (float).
  - `strain_field_data` — List of `(r, z, strain)` tuples.
  - `stress_field_data` — List of `(r, z, stress)` tuples.

> **Note:** This is a stub implementation that returns empty/placeholder data. In a full deployment, it would parse VTU files (e.g., via `meshio` or `vtk`). The test suite mocks this function.

---

## Export

### `export_cross_section_png(design: SpiderDesign, filepath: str, show_mesh: bool = False) -> None`

Render the current cross-section plot to a PNG file.

**Parameters:**
- `design` — The design containing the profile.
- `filepath` — Output PNG file path.
- `show_mesh` — If `True` and mesh exists, overlay mesh edges.

**Raises:**
- `RuntimeError` — If the file cannot be written.

---

### `export_force_deflection_csv(design: SpiderDesign, filepath: str) -> None`

Write force-deflection data to a CSV file with columns `displacement_mm`, `force_N`, `direction`.

**Parameters:**
- `design` — The design containing simulation results.
- `filepath` — Output CSV file path.

**Raises:**
- `RuntimeError` — If the file cannot be written.

---

### `export_compliance_csv(design: SpiderDesign, filepath: str) -> None`

Write compliance data to a CSV file with columns `displacement_mm`, `compliance_mm_per_N`, `direction`.

**Parameters:**
- `design` — The design containing simulation results.
- `filepath` — Output CSV file path.

**Raises:**
- `RuntimeError` — If the file cannot be written.

---

### `export_results_json(design: SpiderDesign, filepath: str) -> None`

Write a JSON file containing all input parameters, derived dimensions, and simulation results.

**Parameters:**
- `design` — The design to export.
- `filepath` — Output JSON file path.

**Raises:**
- `RuntimeError` — If the file cannot be written.

---

## Database Backup / Restore

### `export_database(backup_path: str) -> None`

Copy the entire SQLite designs database to the specified backup file path.

**Parameters:**
- `backup_path` — Destination file path.

**Raises:**
- `RuntimeError` — If the copy operation fails.

---

### `import_database(backup_path: str, merge: bool = False) -> None`

Import designs from a backup database file.

**Parameters:**
- `backup_path` — Path to the backup database.
- `merge` — If `False`, replaces the current database. If `True`, merges backup designs into the current database (skipping duplicates by name).

**Raises:**
- `RuntimeError` — If the import operation fails.

---

## Utility

### `init_database(db_path: str | None = None) -> None`

Create the SQLite database and `designs` / `settings` tables if they do not exist.

**Parameters:**
- `db_path` — Optional explicit database path. Uses the default path if `None`.

---

### `set_elmer_solver_path(path: str) -> None`

Update the global setting for the ElmerSolver executable path. Persisted in the SQLite settings table.

**Parameters:**
- `path` — Absolute path to `ElmerSolver.exe`.

---

### `set_elmergrid_path(path: str) -> None`

Update the global setting for the ElmerGrid executable path. Persisted in the SQLite settings table.

**Parameters:**
- `path` — Absolute path to `ElmerGrid.exe`.

---

### `set_working_directory(path: str) -> None`

Update the global setting for the working directory. Persisted in the SQLite settings table.

**Parameters:**
- `path` — Absolute path to the working directory.

---

*End of API Reference*
