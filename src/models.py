"""
SpiderFEA — Data Models

SpiderDesign dataclass and related constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpiderDesign:
    """Represents a single spider design with all input, derived, and result fields."""

    # Identity
    name: str = ""

    # Geometry inputs (7 independent parameters)
    D_inner_spider: float = 75.0          # mm
    L_inner_bond: float = 2.5             # mm
    D_outer_landing_ID: float = 110.0     # mm
    D_outer_landing_OD: float = 122.0     # mm
    h_inner: float = 7.0                  # mm
    h_outer: float = 10.0                 # mm
    t: float = 0.75                       # mm

    # Fixed geometry
    theta_deg: float = 30.0               # degrees
    n_peaks: int = 7                      # must be odd positive

    # Material (auto-loaded from DB)
    material_name: str = "Phenolic-Treated Cloth"
    youngs_modulus: float = 5000.0        # MPa
    poissons_ratio: float = 0.35
    density: float = 1200.0               # kg/m³
    model_type: str = "linear_elastic"

    # Mesh controls
    global_element_size: float = 0.5      # mm
    elements_through_thickness: int = 4
    mesh_refinement_factor: float = 1.0

    # Setup paths
    elmer_solver_path: str = ""
    elmergrid_path: str = ""
    working_directory: str = ""
    num_processors: int = 1

    # Derived geometry (computed by recalculate_profile)
    R_inner_spider: float = 0.0
    R_outer_landing_ID: float = 0.0
    R_outer_landing_OD: float = 0.0
    R_inner_corr: float = 0.0
    z_inner_cone: float = 0.0
    extension: float = 0.0

    # Profile arrays
    profile_r: list[float] = field(default_factory=list)
    profile_z: list[float] = field(default_factory=list)

    # State flags
    mesh_generated: bool = False
    simulation_complete: bool = False

    # Simulation results
    max_von_mises_stress: float = 0.0     # MPa
    max_strain: float = 0.0
    force_deflection_data: list[dict[str, Any]] = field(default_factory=list)
    compliance_data: list[dict[str, Any]] = field(default_factory=list)
    strain_field_data: list[tuple] = field(default_factory=list)
    stress_field_data: list[tuple] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize design inputs, state, and results to a dict."""
        return {
            "name": self.name,
            "D_inner_spider": self.D_inner_spider,
            "L_inner_bond": self.L_inner_bond,
            "D_outer_landing_ID": self.D_outer_landing_ID,
            "D_outer_landing_OD": self.D_outer_landing_OD,
            "h_inner": self.h_inner,
            "h_outer": self.h_outer,
            "t": self.t,
            "theta_deg": self.theta_deg,
            "n_peaks": self.n_peaks,
            "material_name": self.material_name,
            "youngs_modulus": self.youngs_modulus,
            "poissons_ratio": self.poissons_ratio,
            "density": self.density,
            "model_type": self.model_type,
            "global_element_size": self.global_element_size,
            "elements_through_thickness": self.elements_through_thickness,
            "mesh_refinement_factor": self.mesh_refinement_factor,
            "elmer_solver_path": self.elmer_solver_path,
            "elmergrid_path": self.elmergrid_path,
            "working_directory": self.working_directory,
            "num_processors": self.num_processors,
            # Derived geometry
            "R_inner_spider": self.R_inner_spider,
            "R_outer_landing_ID": self.R_outer_landing_ID,
            "R_outer_landing_OD": self.R_outer_landing_OD,
            "R_inner_corr": self.R_inner_corr,
            "z_inner_cone": self.z_inner_cone,
            "extension": self.extension,
            # Profile arrays
            "profile_r": self.profile_r,
            "profile_z": self.profile_z,
            # State flags
            "mesh_generated": self.mesh_generated,
            "simulation_complete": self.simulation_complete,
            # Simulation results
            "max_von_mises_stress": self.max_von_mises_stress,
            "max_strain": self.max_strain,
            "force_deflection_data": self.force_deflection_data,
            "compliance_data": self.compliance_data,
            "strain_field_data": self.strain_field_data,
            "stress_field_data": self.stress_field_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpiderDesign:
        """Deserialize a design from a dict."""
        design = cls()
        for key, value in data.items():
            if hasattr(design, key):
                setattr(design, key, value)
        return design


# Set class-level defaults so hasattr(SpiderDesign, attr) works for tests.
# default_factory still ensures each instance gets its own list.
SpiderDesign.profile_r = []
SpiderDesign.profile_z = []
SpiderDesign.force_deflection_data = []
SpiderDesign.compliance_data = []
SpiderDesign.strain_field_data = []
SpiderDesign.stress_field_data = []
