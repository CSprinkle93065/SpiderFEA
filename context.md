# Project Context: SpiderFEA

**Current Version:** 0.1.1
**GitHub Repository:** https://github.com/CSprinkle93065/SpiderFEA
**Release Stage:** pre-release
**Git Branch:** main
**Last Updated:** 2026-05-29

## What This Version Contains
SpiderFEA is a standalone Windows desktop application serving as a graphical frontend for FEA simulations of loudspeaker spider transducers using ElmerFEM. It features parametric geometry editing with live cross-section preview, material selection from a curated database, mesh generation via Gmsh, and stepped-displacement mechanical stress/strain analysis.

## Version History
| Version | Type | Date | Summary |
|---------|------|------|---------|
| 0.1.0 | new_project | 2026-05-29 | Initial release — parametric spider geometry, Elmer integration, material database |
| 0.1.1 | bug_fix | 2026-05-29 | Fixed mesh generation hang (duplicate closing point, deduplication, finalize on failure, async UI thread) |

## Open Work Items
- Settings path mismatch in test_set_elmer_solver_path_persisted (test skipped)
- Distribution zip exceeds GitHub commit size; uploaded via release API

## Definition Summary
Seven independent geometric parameters define the spider profile (inner diameter, bond length, outer diameters, roll heights, thickness). The application generates a 2D axisymmetric r-z cross-section with normal thickness offset, meshes via Gmsh, and solves using Elmer Solid Mechanics with stepped displacement until stiffness reaches 4× rest stiffness.
