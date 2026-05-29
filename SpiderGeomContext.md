# Spider Geometry Context

**Project:** SpiderFEA  
**Purpose:** Parametric 2D axisymmetric r-z cross-section of a loudspeaker spider (damper) for Elmer Multiphysics meshing.  
**Canonical Script:** `src/spider_profile.py`

---

## 1. Geometry Overview

The spider is a flexible corrugated disc that centers the voice coil former within the magnetic gap and provides restoring force. It connects the voice coil assembly (inner edge) to the basket/chassis (outer edge). For 2D axisymmetric FEA in Elmer, only a single r-z cross-section is required — Elmer integrates the revolution analytically.

The profile is a **closed polygon** representing the full wall thickness, traced clockwise starting from the innermost point of the lower surface.

### Key Features
- **Inner conical bond:** A straight section at fixed angle from the reference plane, providing glue surface to the voice coil former
- **Corrugation:** Sinusoidal waves that provide compliant flexure; amplitude tapers linearly from inner to outer
- **Outer flat landing:** Horizontal extension for glue bond to the basket
- **Normal thickness offset:** Upper and lower surfaces are offset by ±t/2 in the direction normal to the centerline at every point

---

## 2. Control Parameters (6 Independent Dimensions)

These are the **red dimensions** that fully constrain the geometry. All other values are derived.

| Symbol | Variable | Reference Value | Description |
|--------|----------|-----------------|-------------|
| `D_inner` | `D_inner_spider` | 75.0 mm | Spider inner diameter (voice coil former bond) |
| `L_bond` | `L_inner_bond` | 2.5 mm | Inner glue bond length along cone |
| `D_outer_ID` | `D_outer_landing_ID` | 110.0 mm | Outer landing inner diameter (corrugation end) |
| `D_outer_OD` | `D_outer_landing_OD` | 122.0 mm | Outer landing outer diameter (basket bond) |
| `h_inner` | `h_inner` | 7.0 mm | Peak-to-peak roll height at inner edge |
| `h_outer` | `h_outer` | 10.0 mm | Peak-to-peak roll height at outer edge |
| `t` | `t` | 0.75 mm | Total wall thickness |

> **Note:** Diameters are supplied as control inputs; the script converts to radii internally.

---

## 3. Fixed Constraints

| Parameter | Value | Description |
|-----------|-------|-------------|
| `θ` | 30° | Inner cone angle from reference plane |
| `n_peaks` | 7 | Number of corrugation peaks (must be **odd integer**) |

### Why Odd `n_peaks`?
The corrugation phase runs from `0` to `n_peaks × π`. For the sine wave to start **and end at z = 0** (the reference plane), `sin(n_peaks × π)` must equal zero. This requires `n_peaks` to be an integer. Using an **odd** integer ensures both ends are at the same phase (0), creating a smooth transition to the cone and landing without a half-wave cutoff.

> **Agent Note:** Always validate that `n_peaks` is an odd positive integer. Even values will produce a corrugation that ends at a peak or trough, not at z = 0.

---

## 4. Derived Geometry

### Radii (from diameters)
```
R_inner_spider      = D_inner_spider / 2
R_outer_landing_ID  = D_outer_landing_ID / 2
R_outer_landing_OD  = D_outer_landing_OD / 2
```

### Inner Cone
```
R_inner_corr = R_inner_spider + L_inner_bond * cos(θ)
z_inner_cone = -L_inner_bond * sin(θ)
```

The cone centerline runs from `(R_inner_spider, z_inner_cone)` to `(R_inner_corr, 0)`.

### Outer Extension
```
extension = R_outer_landing_OD - R_outer_landing_ID
```

The flat landing runs from `(R_outer_landing_ID, 0)` to `(R_outer_landing_OD, 0)`.

### Corrugation
```
phase = π * n_peaks * (r - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
h(r)  = h_inner + (h_outer - h_inner) * (r - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
z(r)  = (h(r) / 2) * sin(phase)
```

- `h(r)` tapers linearly from `h_inner` to `h_outer`
- Amplitude at any radius = `h(r) / 2`
- The `sin(phase)` term creates `n_peaks` peaks and `n_peaks - 1` troughs

---

## 5. Normal Thickness Offset

The wall thickness `t` is offset **normal to the local centerline tangent** at every point. This is critical for accurate FEA meshing, especially in the corrugations where slope varies continuously.

### Algorithm
For each point on the centerline `(r, z)`:
1. Compute tangent via central differences: `(dr, dz)`
2. Unit inward normal (into material, downward side): `n = (dz, -dr) / √(dr² + dz²)`
3. Lower surface (material side): `(r, z) + (t/2) * n`
4. Upper surface (air side): `(r, z) - (t/2) * n`

### Special Cases
| Section | Slope | Normal Direction |
|---------|-------|------------------|
| Inner cone | `tan(θ)` | At `θ + 90°` from horizontal |
| Corrugation peak | `dz/dr = 0` | Straight down `(0, -1)` |
| Corrugation slope | `dz/dr ≠ 0` | Tilted according to local slope |
| Outer landing | `0` | Straight down `(0, -1)` |

---

## 6. Profile Construction Sequence

The closed polygon is built as an ordered list of `(r, z)` points:

| Step | Segment | Description |
|------|---------|-------------|
| 1 | Lower inner cone | From innermost point to corrugation start |
| 2 | Lower corrugation | Follows sinusoid, normal-offset downward |
| 3 | Lower outer landing | Horizontal to outermost radius |
| 4 | Outer edge | Vertical/normal connection to upper surface |
| 5 | Upper outer landing | Horizontal back to landing ID |
| 6 | Upper corrugation | Sinusoid reversed, normal-offset upward |
| 7 | Upper inner cone | Back to corrugation start |
| 8 | Inner edge | Normal connection closing to lower start |

> **Note:** Steps 4 and 8 are implicit — `matplotlib.fill` connects the last lower point to the first upper point, and the last upper point to the first lower point, forming closed edges.

---

## 7. Verification Checks

The script validates these geometric constraints:

- [x] **Profile closed loop** — first and last polygon vertices match within tolerance
- [x] **Corrugation starts at z = 0** — `z(R_inner_corr) = 0`
- [x] **Corrugation ends at z = 0** — `z(R_outer_landing_ID) = 0`
- [x] **Odd peak count** — `n_peaks % 2 == 1` (asserted or warned)
- [x] **Thickness consistency** — upper/lower separation ≈ `t` normal to surface

---

## 8. Usage

### Requirements
```bash
pip install numpy matplotlib
```

### Run
```bash
cd projects/SpiderFEA/src
python spider_profile.py
```

### Output
- `spider_profile.png` — verification plot with annotated dimensions

### Modifying Parameters
Edit the **Control Parameters** block at the top of `spider_profile.py`:

```python
# --- CONTROL PARAMETERS (red dimensions) ---
D_inner_spider = 75.0       # Spider inner diameter [mm]
L_inner_bond = 2.5          # Inner glue bond length along cone [mm]
D_outer_landing_ID = 150.0  # Outer landing inner diameter [mm]
D_outer_landing_OD = 165.0  # Outer landing outer diameter [mm]
h_inner = 7.0               # Peak-to-peak roll height at inner edge [mm]
h_outer = 10.0              # Peak-to-peak roll height at outer edge [mm]
t = 0.75                    # Total wall thickness [mm]
```

The script is robust to parameter changes as long as:
- `D_outer_landing_OD > D_outer_landing_ID > D_inner_spider`
- `n_peaks` is a positive odd integer
- `h_inner` and `h_outer` are positive

---

## 9. Axisymmetric FEA Notes

- **Solver target:** Elmer Multiphysics (2D axisymmetric solid mechanics)
- **Meshing requirement:** At least 3–4 elements through wall thickness to capture bending in corrugations
- **No 360° solid needed:** Elmer handles the analytic revolution of the r-z profile
- **Next step:** Convert `profile_r`, `profile_z` arrays into a Gmsh Python API script or `.geo` file for mesh generation, then pass through ElmerGrid

---

## 10. Coordinate System

- **r:** Radial distance from axis of revolution [mm]
- **z:** Axial distance from reference plane [mm]
- **Reference plane:** `z = 0` (plane where corrugation meets cone and outer landing)
- **Axis of revolution:** `r = 0`

---

## 11. File Inventory

```
projects/SpiderFEA/
├── SpiderGeomContext.md      # This file
└── src/
    ├── spider_profile.py     # Canonical parametric script (current)
    ├── spider_profile.png    # Generated verification plot
    ├── spider_corrugation.py # Earlier centerline-only version
    ├── spider_corrugation.png
    ├── spider_geometry.py    # Earlier version with progressive power
    └── spider_profile.png    # (older)
```

> **Agent Note:** Use `spider_profile.py` as the canonical script. Earlier versions (`spider_corrugation.py`, `spider_geometry.py`) are retained for reference but superseded.

---

*Generated: 2026-05-25*  
*Geometry version: v1 (30° cone, normal thickness, linear amplitude taper)*
