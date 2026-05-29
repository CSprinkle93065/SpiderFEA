import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# SPIDER PARAMETRIC PROFILE — 7 CONTROL PARAMETERS, ALL ELSE DRIVEN
# =============================================================================

# --- CONTROL PARAMETERS (red dimensions) ---
D_inner_spider = 75.0       # Spider inner diameter [mm]
L_inner_bond = 2.5          # Inner glue bond length along cone [mm]
D_outer_landing_ID = 150.0  # Outer landing inner diameter [mm]
D_outer_landing_OD = 165.0  # Outer landing outer diameter [mm]
h_inner = 7.0               # Peak-to-peak roll height at inner edge [mm]
h_outer = 10.0              # Peak-to-peak roll height at outer edge [mm]
t = 0.75                    # Total wall thickness [mm]

# --- CONVERT DIAMETERS TO RADII ---
R_inner_spider = D_inner_spider / 2.0
R_outer_landing_ID = D_outer_landing_ID / 2.0
R_outer_landing_OD = D_outer_landing_OD / 2.0

# --- FIXED CONSTRAINTS ---
theta_deg = 30.0            # Inner cone angle from reference plane [deg]
n_peaks = 7                 # Number of peaks (troughs = n_peaks - 1)

# --- DERIVED GEOMETRY ---
theta = np.deg2rad(theta_deg)

# Inner cone endpoints
R_inner_corr = R_inner_spider + L_inner_bond * np.cos(theta)
z_inner_cone = -L_inner_bond * np.sin(theta)

# Outer extension
extension = R_outer_landing_OD - R_outer_landing_ID

# Discretization
n_pts_cone = 100
n_pts_corr = 800
n_pts_ext = 100

# --- INNER CONE CENTERLINE ---
r_cone = np.linspace(R_inner_spider, R_inner_corr, n_pts_cone)
z_cone = np.tan(theta) * (r_cone - R_inner_spider) + z_inner_cone

# --- CORRUGATION CENTERLINE ---
r_corr = np.linspace(R_inner_corr, R_outer_landing_ID, n_pts_corr)
phase = np.pi * n_peaks * (r_corr - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
h = h_inner + (h_outer - h_inner) * (r_corr - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
z_corr = (h / 2) * np.sin(phase)

# --- OUTER EXTENSION CENTERLINE ---
r_ext = np.linspace(R_outer_landing_ID, R_outer_landing_OD, n_pts_ext)
z_ext = np.zeros_like(r_ext)

# --- CONCATENATE CENTERLINE ---
r_center = np.concatenate([r_cone, r_corr[1:], r_ext[1:]])
z_center = np.concatenate([z_cone, z_corr[1:], z_ext[1:]])

# --- NORMAL THICKNESS OFFSET ---
dr = np.zeros_like(r_center)
dz = np.zeros_like(z_center)

# Central differences
dr[1:-1] = r_center[2:] - r_center[:-2]
dz[1:-1] = z_center[2:] - z_center[:-2]
# Endpoints
dr[0] = r_center[1] - r_center[0]
dz[0] = z_center[1] - z_center[0]
dr[-1] = r_center[-1] - r_center[-2]
dz[-1] = z_center[-1] - z_center[-2]

# Unit inward normal = (dz, -dr) / len
length = np.sqrt(dr**2 + dz**2)
nr_inward = dz / length
nz_inward = -dr / length

# Offset surfaces
half_t = t / 2.0
r_lower = r_center + half_t * nr_inward
z_lower = z_center + half_t * nz_inward
r_upper = r_center - half_t * nr_inward
z_upper = z_center - half_t * nz_inward

# --- BUILD CLOSED POLYGON ---
profile_r = []
profile_z = []
profile_r.extend(r_lower)
profile_z.extend(z_lower)
profile_r.extend(r_upper[::-1])
profile_z.extend(z_upper[::-1])

# --- PLOT ---
fig, ax = plt.subplots(figsize=(14, 7))

ax.fill(profile_r, profile_z, color='lightcoral', edgecolor='darkred', linewidth=2, alpha=0.5)
ax.plot(r_center, z_center, 'b--', lw=1.5, alpha=0.6, label='Centerline')
ax.plot(r_lower, z_lower, 'g-', lw=1.5, alpha=0.7, label='Lower surface')
ax.plot(r_upper, z_upper, 'm-', lw=1.5, alpha=0.7, label='Upper surface')
ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.4)

# Dimension labels
ax.annotate(f'ID = {D_inner_spider} mm', xy=(R_inner_spider, z_inner_cone),
            xytext=(R_inner_spider - 8, z_inner_cone - 2),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=12, color='red', fontweight='bold')
ax.annotate(f'OD = {D_outer_landing_OD} mm', xy=(R_outer_landing_OD, 0),
            xytext=(R_outer_landing_OD + 2, 1.5),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=12, color='red', fontweight='bold')

# Bond length annotation
mid_cone_r = (R_inner_spider + R_inner_corr) / 2
mid_cone_z = (z_inner_cone + 0) / 2
ax.annotate(f'{L_inner_bond} mm @ {theta_deg}°', xy=(mid_cone_r, mid_cone_z),
            xytext=(mid_cone_r - 6, mid_cone_z + 2),
            fontsize=11, color='blue', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))

# Landing width annotation
ax.annotate(f'{extension} mm', xy=((R_outer_landing_ID + R_outer_landing_OD) / 2, 0.3),
            fontsize=11, color='blue', fontweight='bold', ha='center')

# Roll height annotations
ax.annotate(f'h_inner = {h_inner} mm', xy=(R_inner_corr + 1, h_inner / 2), fontsize=11,
            color='darkgreen', fontweight='bold', ha='left')
ax.annotate(f'h_outer = {h_outer} mm', xy=(R_outer_landing_ID - 1, h_outer / 2), fontsize=11,
            color='darkgreen', fontweight='bold', ha='right')

# Peak/trough count
mid_r = (R_inner_corr + R_outer_landing_ID) / 2
ax.text(mid_r, h_outer / 2 + 1.5, f'{n_peaks} peaks, {n_peaks - 1} troughs',
        fontsize=13, color='darkblue', fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lavender', alpha=0.5))

# Thickness annotation
mid_idx = len(r_center) // 2
ax.annotate(f't = {t} mm', xy=(r_center[mid_idx], z_center[mid_idx]),
            xytext=(r_center[mid_idx] + 3, z_center[mid_idx] + 1.5),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.5),
            fontsize=11, color='black', fontweight='bold')

# Axis of revolution
ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
ax.text(1, h_outer / 2 + 0.5, 'Axis of\nRevolution', fontsize=10, color='black', alpha=0.5)

# Info box
info = (
    f'Cone angle: {theta_deg}°\n'
    f'Corr. start: R = {R_inner_corr:.2f}, z = 0\n'
    f'Thickness: {t} mm (normal offset)\n'
    f'Profile closed: YES'
)
ax.text(0.02, 0.98, info, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))

ax.set_xlim(0, R_outer_landing_OD + 10)
ax.set_ylim(z_inner_cone - t - 2, h_outer / 2 + t + 3)
ax.set_aspect('equal')
ax.set_xlabel('Radial Distance r [mm]', fontsize=13)
ax.set_ylabel('Axial Distance z [mm]', fontsize=13)
ax.set_title(f'Spider Profile — {theta_deg}° Cone, Normal t = {t} mm', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig('spider_profile.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: spider_profile.png")
