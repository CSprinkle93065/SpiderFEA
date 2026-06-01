# SpiderFEA v0.1.3 — Post-Release Bug Investigation

**Date:** 2026-05-30  
**Investigator:** Kimi Code CLI  
**Status:** Root cause identified; fix direction selected (Option A)

---

## 1. Symptom Report

After pressing the **Mesh** button with geometry that passes validity checks:

1. The **Mesh** button becomes disabled and **never re-enables**.
2. The application **spawns a second window** showing the original geometry / main interface.
3. No mesh is ever generated; no error dialog is shown.

---

## 2. Root Cause

### 2.1 Primary: Missing `multiprocessing.freeze_support()`

`src/api.py::generate_mesh_with_timeout()` uses `multiprocessing.get_context("spawn")` + `Process` to run Gmsh with a 30-second hard timeout. On Windows, the `"spawn"` context starts a **fresh Python interpreter** that re-imports the entry-point module.

Because the application is packaged with **PyInstaller** (`SpiderFEA.spec`), the child process re-executes the frozen `SpiderFEA.exe`. Without `multiprocessing.freeze_support()` in `src/main.py`, PyInstaller does **not** intercept the internal `--multiprocessing-fork` argument. The child process therefore runs:

```python
if __name__ == "__main__":
    main()   # <-- executes in child, creating a SECOND MainWindow
```

The actual mesh worker (`_generate_mesh_worker`) is **never invoked** in the child process.

### 2.2 Secondary: `gmsh.initialize()` parses `sys.argv`

`src/api.py::generate_mesh()` calls `gmsh.initialize()` with no arguments. Gmsh defaults to parsing `sys.argv`, which in a spawned/frozen subprocess may contain the parent’s command line. This can cause Gmsh to enter GUI mode or behave unpredictably.

Safe call: `gmsh.initialize([])`

### 2.3 Tertiary: `result_queue.get()` blocks forever on orphan exit

`generate_mesh_with_timeout()` calls `result_queue.get()` without a timeout. If the child process exits abnormally without enqueueing a result (e.g., the `freeze_support()` bug), the parent blocks indefinitely.

---

## 3. Why the Button Stays Disabled

1. `_on_generate_mesh()` disables the button and starts a `QThread` / `MeshWorker`.
2. `MeshWorker.run()` → `generate_mesh_with_timeout()` → spawns subprocess.
3. Subprocess opens a **second GUI window** instead of running the mesh worker.
4. After 30 s, `process.join(timeout=30)` expires.
5. If the user closes the second window, the child exits with `exitcode == 0`.
6. Parent skips the timeout/terminate branch and calls `result_queue.get()`.
7. **Queue is empty** → `result_queue.get()` blocks forever.
8. `MeshWorker.run()` never returns → `error`/`finished` signals never fire → button is never re-enabled.

---

## 4. Evidence

| File | Line | Issue |
|---|---|---|
| `src/main.py` | 25 | `multiprocessing.freeze_support()` absent |
| `src/api.py` | 210 | `gmsh.initialize()` should be `gmsh.initialize([])` |
| `src/api.py` | 311 | `result_queue.get()` has no timeout |
| `SpiderFEA.spec` | 5 | Confirms PyInstaller entry point is `src\\main.py` |

---

## 5. Fix Options Evaluated

| Option | Description | Risk |
|---|---|---|
| **A** | Add `freeze_support()` + `gmsh.initialize([])` + `result_queue.get(timeout=5)` | Minimal. Direct fix. |
| **B** | Replace `multiprocessing` with `QProcess` | Higher risk; redesigns timeout mechanism. |
| **C** | Run mesh synchronously in `MeshWorker` QThread | Loses hard-kill safety if Gmsh hangs. |

**Selected: Option A.**

---

## 6. Fix Specification

### 6.1 `src/main.py`

```python
import multiprocessing
# ...
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
```

### 6.2 `src/api.py` — `generate_mesh()`

```python
gmsh.initialize([])
```

### 6.3 `src/api.py` — `generate_mesh_with_timeout()`

```python
try:
    status, payload = result_queue.get(timeout=5)
except Exception:
    raise RuntimeError("Mesh generation worker did not return a result")
```

---

## 7. Regression Tests Required

- `test_real_mesh_generation_completes` — real Gmsh path
- `test_generate_mesh_with_timeout_rejects_bad_geometry` — timeout path
- `test_generate_mesh_sets_flag` — mocked path
- UI test: verify `btnGenerateMesh` is re-enabled after error
