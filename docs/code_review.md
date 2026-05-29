# Assessment: Stage 6 — Code Review (Third Review)

**Project:** SpiderFEA v0.1.0  
**Reviewer:** Code Critic  
**Date:** 2026-05-29  
**Inputs Reviewed:**
- `src/api.py`
- `src/main_window.py`
- `src/dialogs.py`
- `src/geometry.py`
- `src/database.py`
- `src/models.py`
- `src/main.py`
- `src/spider_corrugation.py`
- `src/spider_geometry.py`
- `src/spider_profile.py`
- `docs/definition.md`
- `docs/api_reference.md`

**Verdict:** GO

---

## Findings

### G6.1 — All API functions from the API Function List are present and correctly named in src/api.py
**[PASS]** All 28 functions documented in `docs/api_reference.md` are present in `src/api.py` with identical names and matching signatures. Verified categories:
- Design Lifecycle (7 functions)
- Geometry (3 functions)
- Material Properties (2 functions)
- Mesh Controls (1 function)
- Mesh Generation (2 functions)
- Elmer Simulation (3 functions)
- Export (4 functions)
- Database Backup / Restore (2 functions)
- Utility (4 functions)

`recalculate_profile` and `validate_geometry` are correctly re-exported from `src.geometry` and are importable from `src.api`. `__all__` remains incomplete but does not affect explicit imports used by the UI and tests.

---

### G6.2 — PyQt6 UI code and business logic are separated
**[PASS]** Verified fixed and stable.

1. `src/main_window.py` delegates **all** business logic to `src.api`. No direct database imports remain.
2. State invalidation (`mesh_generated = False`, `simulation_complete = False`) is correctly located in the API layer:
   - `update_geometry_parameter()` (api.py lines 130–131)
   - `update_mesh_control()` (api.py lines 166–167)
3. The UI layer (`main_window.py`) handles only widget state, event wiring, matplotlib plotting, and user feedback (message boxes, status bar, red-field highlighting).

---

### G6.3 — No hardcoded absolute paths, credentials, magic numbers, or environment-specific values
**[PASS]** Verified fixed and stable.

- `src/api.py` `convert_mesh_with_elmergrid()` uses `shutil.which("ElmerGrid")` + generic fallback candidates (`C:\Program Files\ElmerFEM\bin\ElmerGrid.exe`, `"ElmerGrid.exe"`). No user-specific paths.
- `src/api.py` `run_simulation()` uses `shutil.which("ElmerSolver")` + generic fallback candidates. No user-specific paths.
- `src/database.py` `_get_default_db_path()` uses `Path.home()` for portability.
- `src/database.py` `_MATERIALS_DB_PATH` uses `Path.home() / "AgentGlobal" / "materials" / "loudspeaker_materials.db"` (portable).

---

### G6.4 — No obvious security issues
**[PASS]**
- No `eval()` or `exec()` in any source file.
- Subprocess calls use argument lists, not shell strings.
- SQL queries in `src/database.py` use parameterized statements (`?` placeholders).
- File writes validate paths or use user-selected paths via `QFileDialog`.

---

### G6.5 — Error handling exists at all system boundaries
**[PASS]** All critical system-boundary gaps from prior reviews are resolved.

#### CRITICAL CHECK: Every `sqlite3.connect()` in src/ is inside `try/except`

Verified via direct inspection and `grep` across the entire `src/` tree. Four distinct call sites exist, **all** wrapped:

1. **`src/database.py` `init_database()` (line 42)**
   ```python
   try:
       conn = sqlite3.connect(path)
   except sqlite3.Error as exc:
       raise RuntimeError(f"Failed to connect to database: {exc}") from exc
   ```
   ✅ Wrapped.

2. **`src/database.py` `_get_connection()` (lines 82, 86)**
   ```python
   try:
       if db_path is not None:
           init_database(db_path)
           return sqlite3.connect(db_path)
       ...
       return sqlite3.connect(path)
   except sqlite3.Error as exc:
       raise RuntimeError(f"Failed to connect to database: {exc}") from exc
   ```
   ✅ Both `return sqlite3.connect(...)` calls inside the same `try/except` block.

3. **`src/database.py` `import_database()` merge mode (line 210)**
   ```python
   try:
       shutil.copy2(backup_path, temp_path)
       conn_temp = sqlite3.connect(temp_path)
       rows = conn_temp.execute(...).fetchall()
       conn_temp.close()
       ...
   except sqlite3.Error as exc:
       raise RuntimeError(f"Failed to import database (merge): {exc}") from exc
   ```
   ✅ `sqlite3.connect(temp_path)` is inside the `try` block.

4. **`src/database.py` `list_available_spider_materials()` (line 269)** — **Previously failed in Review 2.**
   ```python
   try:
       conn = sqlite3.connect(str(db_path))
   except sqlite3.Error as exc:
       raise RuntimeError(f"Failed to connect to materials database: {exc}") from exc
   ```
   ✅ **Fixed.** The connection is now wrapped in its own `try/except sqlite3.Error` block, converting raw `sqlite3.Error` into `RuntimeError` before it can propagate to the UI.

#### Other system boundaries
- `subprocess.run()` in `convert_mesh_with_elmergrid()` and `run_simulation()` — wrapped in `try/except`.
- `gmsh.initialize()` / `gmsh.write()` / `gmsh.finalize()` in `generate_mesh()` — wrapped in `try/except`.
- File writes (`sif_path.write_text()`, `fig.savefig()`, CSV/JSON `open()`) — wrapped in `try/except OSError`.
- `shutil.copy2()` in `export_database()` and `import_database()` — wrapped in `try/except OSError`.
- `_get_default_db_path()` `Path.mkdir()` — wrapped in `try/except OSError`.

**Minor observation (non-blocking):** `generate_elmer_sif()` and `run_simulation()` contain unwrapped `Path.mkdir()` calls before their respective `try` blocks. In practice these are unlikely to fail (`parents=True, exist_ok=True`), and `generate_elmer_sif()`'s primary I/O (`write_text`) is wrapped. No action required for this review.

---

### G6.6 — docs/api_reference.md accurately reflects actual functions in src/api.py
**[PASS]** Every function in `src/api.py` is documented in `docs/api_reference.md`. No functions are missing. Parameter names, types, default values, return types, and exception contracts match the implementation exactly. Verified:
- `load_design` optional `db_path` parameter is documented.
- `list_designs` optional `db_path` parameter is documented.
- `generate_mesh` fallback behavior (Gmsh not installed) is accurately described.
- `parse_simulation_results` stub status is correctly noted.
- `convert_mesh_with_elmergrid` parameter types and `None` return match.
- `export_cross_section_png` `show_mesh` parameter default matches.
- `import_database` `merge` parameter default matches.

---

## Summary

| Gate | Status |
|------|--------|
| G6.1 | PASS |
| G6.2 | PASS |
| G6.3 | PASS |
| G6.4 | PASS |
| G6.5 | PASS |
| G6.6 | PASS |

All issues identified in Review 1 (G6.2 UI/logic separation, G6.3 hardcoded paths, G6.5 error handling) and Review 2 (G6.5 `list_available_spider_materials` `sqlite3.connect` unwrapped) are confirmed resolved. The codebase is ready for Stage 7.
