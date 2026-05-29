# Project Definition

## Project Name: SpiderFEA

## Project Description:

This project will be a standalone windows program that functions as a graphical frontend for FEA simulations using Elmer.  Specifically, this program will focus on mechanical stress/strain analysis of loudspeaker transducer spiders.

## Input Parameters

- Spider ID

- Inner Bond Length
  
  - Inner glue bond length along cone

- Spider OD
  
  - Outer landing outer diameter (basket bond)

- Frame Landing ID
  
  - Outer landing inner diameter (corrugation end)

- h_inner
  
  - Peak-to-peak roll height at inner edge

- h_outer
  
  - Peak-to-peak roll height at outer edge

- Spider Thickness
  
  - Total wall thickness

## Outputs

- Graphics (tabbed)
  
  - Cross section (live) with mesh
  
  - Cross section with strain (color coded)
    
    - Inward AND outward deflection
    - This shows the distorted shape of the profile at the extremes of travel.
    - Zoom this into geometry...  No blank space.
  
  - Force vs. deflection curve
    
    - Inward AND outward deflection
    
    - Vertical axis is force in N
    
    - Horizontal is displacement in mm, with x=0 at center.
    
    - Zoom this into geometry... No blank space.
  
  - Compliance curve
    
    - Units: mm/N

## Controls

- Mesh Controls (as appropriate to adjust)

- "Mesh" button

- "Run Simulation" button

## GUI

- Similar to project "LoudspeakerFEA", but with some differences
  
  - Input parameter fields have no scroll bars.  Only text input is acceptable.  Condense the fields, making them big enough for 3 significant figures.
  
  - Tab between fields or select with mouse.
  
  - Derived dimensional parameters have only two decimal places (e.g. 38.45 mm)
  
  - Elmer options still in top menu bar, but mesh options placed on side with input parameters

- Sections on side:
  
  - Surround Geometry
    
    - Input Parameters
  
  - Elmer Mesh
    
    - Mesh Controls
    
    - Mesh button
  
  - Elmer Solver
    
    - Run Simulation button

## User Workflow

- User enters input parameters

- User checks mesh controls and adjusts if necessary

- User presses mesh button and inspects mesh shown in live cross section.
  
  - Adjusts mesh controls and iterates if required

- User presses "Run Simulation"button.
  
  - Adjust input parameters and iterate simulation if required.

## Program Operation

- As user enters input parameters, the live cross section updates.  (they have to move to a different field for the graph to update, either by clicking away or by hitting tab to move to the next field)  The graph doesn't show the mesh during live update.  The derived papameters are also updated.  If the geometry fails during calculation based on the input parameters, the input fields should be colored RED and the live cross section should be blank.

- When the user presses the "Mesh" button, the live cross section is updated with the mesh after it is generated

- When the user presses the "Run Simulation" button, the results are shown in the corresponding graphics tabs, which are now selectable.  Before simulation is run, the graphics tabs cannot be selected. The live cross section is the only graphic shown until simulation results are available.

## Geometry

Geometry engine is already developed as a python script.  see projects\SpiderFEA\SpiderGeomContext.md

## Simulation

The simulation fixes the outer spider landing as static, then displaces the inner bond cone in the Z direction to determine stress, strain, and force.  The simulation continues to step the displacement at 1mm increments until the stiffness k(x) is four times the stiffness at x=0.  Inner bond cone as well as outer landing should remain undistorted.  Displacement is simulated in both positive and negative direction from x=0.
