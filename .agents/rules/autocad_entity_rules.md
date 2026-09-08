---
trigger: always_on
description: Rules for AutoCAD CAD entity manipulation, auditing, and truthful verification.
---

# AutoCAD CAD Automation & Entity Handling Rules

## 1. Audit Before Execution
- Never assume what entity types exist in a drawing or block based solely on visual appearance.
- Always run a selection audit (e.g., query DXF group 0 / `ObjectName`) to confirm whether objects are `LINE`, `LWPOLYLINE`, `POLYLINE` (3D), `ARC`, `SPLINE`, `ELLIPSE`, or `INSERT`.

## 2. Geometry-Specific Conversion Requirements
- **Ellipses (`AcDbEllipse`)**: Cannot join with Polylines directly. Always convert via `PEDIT` (`_.pedit <ent> _y ""`).
- **3D Polylines (`AcDb3dPolyline`)**: Cannot join with 2D Polylines. Always convert to 2D by exploding (`_.explode`), flattening to Z=0 (`_.flatten`), and rejoining (`_.join`).
- **Splines (`AcDbSpline`)**: Set `PLINECONVERTMODE 0` (or `1`) before conversion via `SPLINEDIT` or `PEDIT` to prevent extreme arc bulge glitches.

## 3. Truthful Verification
- After executing a script or MCP command, inspect the resulting entity types in the database.
- Never report that an entity type was converted or deleted without confirming the actual database state.

## 4. Preservation of Base Geometry (Zero Deletion Guardrail)
- **Never Delete Base Geometry**: When executing join, close, heal, or boundary operations, NEVER delete, trim away, mutate, or drop any original base geometry (e.g., spine lines, circles, landing geometry, branch bases) without explicit user confirmation.
- **Non-Destructive Healing**: To close gaps or connect elements, bridge the gap with connective segments or generate a new closed boundary on a designated layer, leaving all original base lines and curves 100% intact.
- **Preserve Exact Shape**: Verify that no vertices or features (such as circular landings or junctions) are distorted, simplified, or lost during the operation.
