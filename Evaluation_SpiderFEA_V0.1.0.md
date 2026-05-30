# Evaluation: SpiderFEA v0.1.0

## Bug: Mesh Button Hang

### Symptoms
1. When the **Mesh** button is clicked, the terminal prints: `Warning : Impossible to recover edge 1 1 (error tag -1)`
2. The application UI freezes and stops responding.
3. Mesh generation never completes.
4. The **Run Simulation** button remains disabled because `design.mesh_generated` is never set to `True`.
5. The Python process remains in memory, consuming CPU/resources until forcibly killed.

### Root Cause Analysis

The hang is caused by a **degenerate zero-length edge** passed to Gmsh, which triggers an infinite loop or unrecoverable state inside `gmsh.model.mesh.generate(2)`. Three interrelated code defects contribute:

#### 1. Duplicate first/last point creates a zero-length edge (PRIMARY CAUSE)
In `src/geometry.py:113-114`, the profile polygon is explicitly closed by appending the first point to the end:
```python
profile_r.append(profile_r[0])
profile_z.append(profile_z[0])
```

Then in `src/api.py:200-208`, every point in `profile_r`/`profile_z` is turned into a Gmsh point, and lines are created in a closed loop:
```python
for i in range(len(points)):
    lines.append(gmsh.model.geo.addLine(points[i], points[(i + 1) % len(points)]))
```

Because the last point is identical to the first point, the final line segment has **zero length**. Gmsh cannot mesh a degenerate edge and emits `"Impossible to recover edge 1 1 (error tag -1)"`. On many Gmsh versions this causes the 2-D mesher to hang indefinitely rather than raise an exception.

#### 2. Synchronous Gmsh call on the main UI thread
In `src/main_window.py:594-603`, `_on_generate_mesh()` calls `generate_mesh()` directly on the main (GUI) thread:
```python
def _on_generate_mesh(self):
    self.statusBar().showMessage("Meshing...")
    QApplication.processEvents()
    try:
        self.design = generate_mesh(self.design)
```

There is no `QThread`, worker thread, or async mechanism. Once `gmsh.model.mesh.generate(2)` begins, the Qt event loop is blocked. Even if Gmsh did not hang, the UI would freeze for the entire duration of meshing. Because Gmsh *does* hang, the application becomes completely unresponsive.

#### 3. Missing `gmsh.finalize()` on exception path
In `src/api.py:196-238`, `gmsh.finalize()` is called only on the success path (line 231). The exception handler at line 237-238 simply re-raises a `RuntimeError` without cleaning up Gmsh:
```python
try:
    gmsh.initialize()
    ...
    gmsh.finalize()   # only on success
except Exception as exc:
    raise RuntimeError(f"Mesh generation failed: {exc}") from exc
```

If Gmsh hangs or throws, `gmsh.finalize()` is never executed. The Gmsh C++ runtime remains initialized in memory, holding file handles and model state. Repeated clicks of the Mesh button compound the leak.

#### 4. Why the QA tests passed
Both `tests/test_mesh.py` and `tests/test_ui_interactions.py` mock `gmsh` with `unittest.mock.MagicMock`. `MagicMock` methods return new mocks instantly and never perform actual geometry or meshing operations. The tests verify that `mesh_generated` becomes `True` and that certain mock methods were called, but they do not exercise the real Gmsh API with the actual profile geometry.

### Code Locations

| File | Line(s) | Issue |
|------|---------|-------|
| `src/geometry.py` | 113-114 | Duplicate first point appended to close polygon, creating a zero-length edge for Gmsh. |
| `src/api.py` | 196-238 | `gmsh.finalize()` is not protected by `try/finally`; missing cleanup on exception. |
| `src/api.py` | 200-208 | All profile points are fed directly to Gmsh without deduplicating the closing point. |
| `src/api.py` | 224 | `gmsh.model.mesh.generate(2)` runs synchronously; no timeout or thread isolation. |
| `src/main_window.py` | 594-603 | `generate_mesh()` invoked on the main UI thread, blocking the Qt event loop. |

### Recommended Fix

1. **Remove the duplicate closing point** from `src/geometry.py` (lines 113-114). Gmsh's `addCurveLoop` does not require the first point to be repeated at the end; the curve loop itself closes the polygon. The polygon should end at its last unique point.

2. **Guard against degenerate edges** in `src/api.py` by skipping consecutive duplicate points before creating Gmsh entities:
   ```python
   unique_points = []
   for r, z in zip(design.profile_r, design.profile_z):
       if not unique_points or (r, z) != unique_points[-1]:
           unique_points.append((r, z))
   ```

3. **Wrap Gmsh lifecycle in `try/finally`** to guarantee cleanup:
   ```python
   try:
       gmsh.initialize()
       ...
   finally:
       gmsh.finalize()
   ```

4. **Move mesh generation off the main thread** using a `QThread` or `QRunnable` so the UI remains responsive. Signal the main thread when meshing completes or fails.

### Severity
Critical
