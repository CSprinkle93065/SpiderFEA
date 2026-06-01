import numpy as np
import math
from math import cos, sin, radians, sqrt, pi

def build_clean(D_inner_spider, L_inner_bond, D_outer_landing_ID, D_outer_landing_OD,
                h_inner, h_outer, t, theta_deg, n_peaks):
    theta = radians(theta_deg)
    R_inner_spider = D_inner_spider / 2.0
    R_outer_landing_ID = D_outer_landing_ID / 2.0
    R_outer_landing_OD = D_outer_landing_OD / 2.0
    R_inner_corr = R_inner_spider + L_inner_bond * cos(theta)
    z_inner_cone = -L_inner_bond * sin(theta)
    
    n_pts_cone = 100
    n_pts_corr = 800
    n_pts_ext = 100
    
    r_cone = np.linspace(R_inner_spider, R_inner_corr, n_pts_cone)
    z_cone = np.tan(theta) * (r_cone - R_inner_spider) + z_inner_cone
    
    r_corr = np.linspace(R_inner_corr, R_outer_landing_ID, n_pts_corr)
    phase = pi * n_peaks * (r_corr - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
    h = h_inner + (h_outer - h_inner) * (r_corr - R_inner_corr) / (R_outer_landing_ID - R_inner_corr)
    z_corr = (h / 2) * np.sin(phase)
    
    r_ext = np.linspace(R_outer_landing_ID, R_outer_landing_OD, n_pts_ext)
    z_ext = np.zeros_like(r_ext)
    
    half_t = t / 2.0
    
    r_c = np.concatenate([r_cone, r_corr[1:], r_ext[1:]])
    z_c = np.concatenate([z_cone, z_corr[1:], z_ext[1:]])
    
    dr = np.zeros_like(r_c)
    dz = np.zeros_like(z_c)
    dr[1:-1] = r_c[2:] - r_c[:-2]
    dz[1:-1] = z_c[2:] - z_c[:-2]
    dr[0] = r_c[1] - r_c[0]
    dz[0] = z_c[1] - z_c[0]
    dr[-1] = r_c[-1] - r_c[-2]
    dz[-1] = z_c[-1] - z_c[-2]
    
    length = np.sqrt(dr**2 + dz**2)
    nr_inward = dz / length
    nz_inward = -dr / length
    
    r_lo = r_c + half_t * nr_inward
    z_lo = z_c + half_t * nz_inward
    r_up = r_c - half_t * nr_inward
    z_up = z_c - half_t * nz_inward
    
    # Upper inner junction
    p1 = np.array([r_up[n_pts_cone-2], z_up[n_pts_cone-2]])
    d1 = np.array([r_up[n_pts_cone-1] - r_up[n_pts_cone-2], z_up[n_pts_cone-1] - z_up[n_pts_cone-2]])
    p2 = np.array([r_up[n_pts_cone], z_up[n_pts_cone]])
    d2 = np.array([r_up[n_pts_cone+1] - r_up[n_pts_cone], z_up[n_pts_cone+1] - z_up[n_pts_cone]])
    det = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(det) > 1e-12:
        dp = p2 - p1
        t = (dp[0]*d2[1] - dp[1]*d2[0]) / det
        s = (dp[0]*d1[1] - dp[1]*d1[0]) / det
        P_up_i = p1 + t * d1
        print(f'  Upper inner junction: t={t:.3f}, s={s:.3f}, P=({P_up_i[0]:.4f}, {P_up_i[1]:.4f})')
    
    # Lower inner junction
    p1 = np.array([r_lo[n_pts_cone-2], z_lo[n_pts_cone-2]])
    d1 = np.array([r_lo[n_pts_cone-1] - r_lo[n_pts_cone-2], z_lo[n_pts_cone-1] - z_lo[n_pts_cone-2]])
    p2 = np.array([r_lo[n_pts_cone], z_lo[n_pts_cone]])
    d2 = np.array([r_lo[n_pts_cone+1] - r_lo[n_pts_cone], z_lo[n_pts_cone+1] - z_lo[n_pts_cone]])
    det = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(det) > 1e-12:
        dp = p2 - p1
        t = (dp[0]*d2[1] - dp[1]*d2[0]) / det
        s = (dp[0]*d1[1] - dp[1]*d1[0]) / det
        P_lo_i = p1 + t * d1
        print(f'  Lower inner junction: t={t:.3f}, s={s:.3f}, P=({P_lo_i[0]:.4f}, {P_lo_i[1]:.4f})')
    
    # Upper outer junction
    idx = n_pts_cone + n_pts_corr - 2
    p1 = np.array([r_up[idx-1], z_up[idx-1]])
    d1 = np.array([r_up[idx] - r_up[idx-1], z_up[idx] - z_up[idx-1]])
    p2 = np.array([r_up[idx+1], z_up[idx+1]])
    d2 = np.array([r_up[idx+2] - r_up[idx+1], z_up[idx+2] - z_up[idx+1]])
    det = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(det) > 1e-12:
        dp = p2 - p1
        t = (dp[0]*d2[1] - dp[1]*d2[0]) / det
        s = (dp[0]*d1[1] - dp[1]*d1[0]) / det
        P_up_o = p1 + t * d1
        print(f'  Upper outer junction: t={t:.3f}, s={s:.3f}, P=({P_up_o[0]:.4f}, {P_up_o[1]:.4f})')
    
    # Lower outer junction
    p1 = np.array([r_lo[idx-1], z_lo[idx-1]])
    d1 = np.array([r_lo[idx] - r_lo[idx-1], z_lo[idx] - z_lo[idx-1]])
    p2 = np.array([r_lo[idx+1], z_lo[idx+1]])
    d2 = np.array([r_lo[idx+2] - r_lo[idx+1], z_lo[idx+2] - z_lo[idx+1]])
    det = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(det) > 1e-12:
        dp = p2 - p1
        t = (dp[0]*d2[1] - dp[1]*d2[0]) / det
        s = (dp[0]*d1[1] - dp[1]*d1[0]) / det
        P_lo_o = p1 + t * d1
        print(f'  Lower outer junction: t={t:.3f}, s={s:.3f}, P=({P_lo_o[0]:.4f}, {P_lo_o[1]:.4f})')

print('=== USER PARAMS JUNCTION CORNERS ===')
build_clean(75.0, 2.5, 120.0, 130.0, 2.0, 2.0, 0.75, 30.0, 7)
print()
print('=== DEFAULT PARAMS JUNCTION CORNERS ===')
build_clean(75.0, 2.5, 110.0, 122.0, 7.0, 10.0, 0.75, 30.0, 7)
