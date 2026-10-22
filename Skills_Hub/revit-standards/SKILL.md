---
name: revit-standards
description: Standard workflows, API syntax, and guidelines for interacting with the Revit AI Agent via the execute_revit_python MCP tool. Use this when answering user requests about Revit, modeling, or formatting.
---

# Revit AI Agent Standards & Guidelines

This skill defines how you (the Gemini AI Agent) should interact with the user's Revit environment. The user communicates via an MCP tool called `execute_revit_python` (on the `Revit_Agent` server).

## 1. IronPython 2.7 Quirks
The Revit AI Agent uses a file-based IPC to run scripts in Revit via pyRevit (IronPython 2.7). 
**CRITICAL RULES:**
- NO f-strings (`f"..."`). Use `.format()` or `%` formatting.
- All code runs inside a `try/except` block with global variables pre-loaded: `doc`, `uidoc`, `uiapp`, `app`, and `__builtins__`.
- `out` parameters: In IronPython, do NOT use `clr.Reference` or `StrongBox` for `out` parameters. Omitting the parameter and accepting a tuple is the safest native way, or using `StrongBox[Type](Type())` if it fails.
- E.g., `roof = doc.Create.NewFootPrintRoof(curves, level, type)` returns `(Roof, ModelCurveArray)`.

## 2. Transactions
- All database modifications MUST be wrapped in a transaction:
```python
from Autodesk.Revit.DB import *
with Transaction(doc, 'AI: Action Name') as t:
    t.Start()
    # do stuff
    t.Commit()
```

## 3. Formatting Standards for the User
The user expects high-quality, professional, and neat outputs:
- **Tags (Doors/Windows):** Do NOT just place tags directly on the element (`LocationPoint`). Tags MUST have leader lines (`tag.HasLeader = True`) and MUST be offset from the wall by at least 3-4 feet in the normal direction so they do not intersect the elements or walls.
- **Dimensions:** Auto-dimensioning should follow standard practices. Horizontal dimensions above the building, vertical dimensions to the right/left. Use `HostObjectUtils.GetSideFaces(wall, ShellLayerType.Exterior)` to get `Reference` objects for dimensioning.
- **Overlapping Elements:** Never allow tags or dimensions to overlap. Use simple separation algorithms or manual offsets if needed.

## 4. Modeling Standards
- **Floors:** Use `Floor.Create(doc, list_of_curveloops, floorType.Id, level.Id)` (Modern API 2022+).
- **Roofs:** Always add appropriate overhangs (e.g., 2 feet). To create a Hip Roof, iterate over the `ModelCurveArray` returned from `NewFootPrintRoof` and set `DefinesSlope = True` and `SlopeAngle = 0.577` (approx 30 deg).
- **Units:** All API coordinates are in decimal feet. Always convert user requests (e.g., "3 meters") to decimal feet (3m = 9.84252 ft).

## 5. Execution State
- The user does not need to click any buttons. The `startup.py` script automatically listens via Revit's `Idling` event.
- Whenever writing a script for the user, use `print()` statements to return status, counts, or IDs back to the MCP server.

## 6. Structural & Modeling Pitfalls (Lessons Learned)
- **Flush Wall Corners (No "Kattak"):** To make walls perfectly flush with the outer edge of columns, calculate the wall centerline by offsetting half the wall thickness inward from the column's outer edge. Draw the walls corner-to-corner using the centerline intersections. This ensures Revit's automatic corner joining engages without leaving odd gaps on the exterior.
- **Slab and Rebar Z-Coordinates:** Floor elements in Revit grow downwards from their placed level (Top = Level, Bottom = Level - Thickness). Ensure rebar meshes are calculated relative to the *actual* concrete Z-elevation. If a roof slab is placed at `MEZZANINE FLR LEVEL` (Z=3500mm) but offset to 4500mm using `BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM`, the rebar mesh must also be placed at Z=4500mm. Floating meshes occur when coordinates mismatch.
- **Door and Window Hosted Z-Coordinates:** When hosting doors and windows on walls that start at a specific level (e.g., `GROUND FLOOR LEVEL` at Z=1000mm), their base placement `XYZ` points MUST account for this base level. Placing a door at Z=0.0 when the ground floor is at Z=1000mm will cause the door to hang 1 meter below the floor slab. Add the host level's global Z to the insertion point.
- **Beam Offsets:** If a roof slab is elevated via offsets, the supporting beams must also be raised to match by setting both `Start Level Offset` and `End Level Offset` so the slab and beam sit perfectly monolithic.

If you follow these standards, the user will be very happy with your professional architectural output!
