import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# SPIDER CORRUGATION CENTERLINE — NO THICKNESS, NO LANDINGS
# =============================================================================

# --- CONTROL PARAMETERS ---
R_inner = 25.0          # Inner radius [mm]
R_outer = 55.0          # Outer radius [mm]
h_inner = 2.0           # Peak-to-peak height at inner edge [mm]
h_outer = 6.0           # Peak-to-peak height at outer edge [mm]
n_peaks = 5             # Number of peaks
n_troughs = 4           # Number of troughs
n_pts = 800             # Points for smooth line

# --- DERIVED ---
# Phase: 0 → n_peaks * π  gives n_peaks peaks, n_troughs troughs, start/end at 0
r = np.linspace(R_inner, R_outer, n_pts)
phase = np.pi * n_peaks * (r - R_inner) / (R_outer - R_inner)

# Linear taper of peak-to-peak height
h = h_inner + (h_outer - h_inner) * (r - R_inner) / (R_outer - R_inner)

# Corrugation centered on z = 0 (reference plane)
z = (h / 2) * np.sin(phase)

# --- PLOT ---
fig, ax = plt.subplots(figsize=(14, 6))

# Corrugation centerline
ax.plot(r, z, 'b-', lw=2.5, label='Corrugation centerline')

# Inner conical section: 45° downward and inward, radial reduction 2.5 mm
R_inner_cone = R_inner - 2.5
z_inner_cone = -2.5
ax.plot([R_inner, R_inner_cone], [0.0, z_inner_cone], 'b-', lw=2.5)
ax.annotate('2.5 mm', xy=((R_inner + R_inner_cone) / 2, z_inner_cone / 2 + 0.5),
            fontsize=11, color='blue', fontweight='bold', ha='center')

# Outer horizontal extension
ax.plot([R_outer, R_outer + 6.0], [0.0, 0.0], 'b-', lw=2.5)
ax.annotate('6 mm', xy=(R_outer + 3, 0.3), fontsize=11, color='blue', fontweight='bold', ha='center')

# Reference plane
ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.5, alpha=0.6, label='Reference plane')

# Parameter labels
ax.annotate(f'R_inner = {R_inner_cone} mm', xy=(R_inner_cone, z_inner_cone),
            xytext=(R_inner_cone - 6, z_inner_cone - 2),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=12, color='red', fontweight='bold')
ax.annotate(f'R_outer = {R_outer} mm', xy=(R_outer, 0), xytext=(R_outer + 1, 2),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=12, color='red', fontweight='bold')

# Height annotations
mid_r = (R_inner + R_outer) / 2
ax.annotate(f'h_inner = {h_inner} mm', xy=(R_inner + 2, h_inner / 2), fontsize=11,
            color='darkgreen', fontweight='bold', ha='left')
ax.annotate(f'h_outer = {h_outer} mm', xy=(R_outer - 2, h_outer / 2), fontsize=11,
            color='darkgreen', fontweight='bold', ha='right')

# Peak/trough count
ax.text(mid_r, h_outer / 2 + 1.5, f'{n_peaks} peaks, {n_troughs} troughs',
        fontsize=13, color='darkblue', fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lavender', alpha=0.5))

# Axis of revolution
ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
ax.text(1, h_outer / 2 + 0.5, 'Axis of\nRevolution', fontsize=10, color='black', alpha=0.5)

ax.set_xlim(0, R_outer + 18)
ax.set_ylim(z_inner_cone - 2, h_outer / 2 + 3)
ax.set_aspect('equal')
ax.set_xlabel('Radial Distance r [mm]', fontsize=13)
ax.set_ylabel('Axial Distance z [mm]', fontsize=13)
ax.set_title('Spider Corrugation Centerline — 45° Inner Cone + 6 mm Outer Extension', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig('spider_corrugation.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: spider_corrugation.png")
