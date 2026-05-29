import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# SPIDER PARAMETRIC GEOMETRY — 2D AXISYMMETRIC r-z CROSS-SECTION
# =============================================================================
# No inner or outer landings: corrugations extend from R_inner to R_outer.

# --- CONTROL PARAMETERS ---
R_inner = 25.0          # Inner radius (voice coil former) [mm]
R_outer = 55.0          # Outer radius (basket) [mm]
N_peaks = 5             # Number of corrugation cycles
h_peak = 2.0            # Peak-to-peak corrugation height [mm]
t = 0.5                 # Wall thickness [mm]
baseline_angle_deg = 0.0  # Baseline slope from inner to outer [deg]
progressive_power = 1.0   # 0=constant, 1=linear, 2=quadratic amplitude growth
n_pts = 400             # Points along upper surface

# --- DERIVED ---
baseline_angle = np.deg2rad(baseline_angle_deg)
dr = (R_outer - R_inner) / (n_pts - 1)
r = np.linspace(R_inner, R_outer, n_pts)

# Baseline (mean surface)
z_baseline = (r - R_inner) * np.tan(baseline_angle)

# Progressive amplitude factor: 0 at inner, 1 at outer
prog = ((r - R_inner) / (R_outer - R_inner)) ** progressive_power

# Corrugation: sinusoid with peak-to-peak h_peak
phase = 2 * np.pi * N_peaks * (r - R_inner) / (R_outer - R_inner)
corr = (h_peak / 2) * prog * np.sin(phase)

# Upper surface
z_upper = z_baseline + corr

# Lower surface: offset by thickness normal to upper surface
# Compute local slope dz/dr by central differencing
dzdr = np.zeros_like(r)
dzdr[1:-1] = (z_upper[2:] - z_upper[:-2]) / (2 * dr)
dzdr[0] = (z_upper[1] - z_upper[0]) / dr
dzdr[-1] = (z_upper[-1] - z_upper[-2]) / dr

# Normal pointing INTO material (downward for upper surface)
norm_r = -dzdr / np.sqrt(1 + dzdr**2)
norm_z = 1.0 / np.sqrt(1 + dzdr**2)

z_lower = z_upper - t * norm_z
r_lower = r - t * norm_r

# --- BUILD CLOSED PROFILE ---
profile_r = []
profile_z = []

# 1. Upper surface: inner → outer
profile_r.extend(r)
profile_z.extend(z_upper)

# 2. Outer edge
profile_r.append(r_lower[-1])
profile_z.append(z_lower[-1])

# 3. Lower surface: outer → inner
profile_r.extend(r_lower[::-1])
profile_z.extend(z_lower[::-1])

# 4. Inner edge (close)
profile_r.append(r[0])
profile_z.append(z_upper[0])

# --- PLOT ---
fig, ax = plt.subplots(figsize=(12, 8))

# Fill profile
ax.fill(profile_r, profile_z, color='lightcoral', edgecolor='darkred', linewidth=2, alpha=0.5)

# Highlight surfaces
ax.plot(r, z_upper, 'b-', lw=2.5, label='Upper surface')
ax.plot(r_lower, z_lower, 'g-', lw=2.5, label='Lower surface')

# Baseline reference
ax.plot(r, z_baseline, 'k--', lw=1, alpha=0.4, label='Baseline')

# Parameter annotations
mid_r = (R_inner + R_outer) / 2
max_z = np.max(z_upper)
min_z = np.min(z_lower)

ax.annotate(f'N_peaks = {N_peaks}', xy=(mid_r, max_z + 0.5),
            fontsize=12, color='darkblue', fontweight='bold', ha='center')
ax.annotate(f'h_peak = {h_peak} mm', xy=(mid_r, min_z - 1.0),
            fontsize=12, color='darkgreen', fontweight='bold', ha='center')
ax.annotate(f't = {t} mm', xy=(R_outer + 2, (z_upper[-1] + z_lower[-1]) / 2),
            fontsize=11, color='purple', fontweight='bold', va='center')
ax.annotate(f'R_inner = {R_inner} mm', xy=(R_inner, z_upper[0]),
            xytext=(R_inner - 8, z_upper[0] + 2),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=11, color='red', fontweight='bold')
ax.annotate(f'R_outer = {R_outer} mm', xy=(R_outer, z_upper[-1]),
            xytext=(R_outer + 2, z_upper[-1] + 2),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=11, color='red', fontweight='bold')

# Axis of revolution
ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax.text(1, max_z + 1.5, 'Axis of\nRevolution', fontsize=10, color='black', alpha=0.6)

# Info box
info = (
    f'Baseline angle: {baseline_angle_deg}°\n'
    f'Progressive power: {progressive_power}\n'
    f'Max amplitude: {h_peak/2 * prog[-1]:.2f} mm\n'
    f'Profile closed: YES'
)
ax.text(0.02, 0.98, info, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))

ax.set_xlim(0, R_outer + 15)
ax.set_ylim(min_z - 3, max_z + 3)
ax.set_aspect('equal')
ax.set_xlabel('Radial Distance r [mm]', fontsize=13)
ax.set_ylabel('Axial Distance z [mm]', fontsize=13)
ax.set_title('Spider Parametric Profile — Axisymmetric r-z Section (No Landings)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig('spider_profile.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: spider_profile.png")
