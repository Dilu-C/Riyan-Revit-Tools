---
name: powerhouse-revit
description: >
  Project-specific skill for the Power House BIM project. Use this when working
  on this project in Revit, Navisworks, Robot Structural Analysis, or related
  AI agent workflows. Contains project memory, API patterns, and standards.
---

# Power House BIM — Project Skill

## 1. Project Overview
Building: **Power House** (Industrial / Generator Building)
Revit Version: **2025**
AI Agent: **Antigravity (Gemini)**
MCP Servers: Revit_Agent, Navisworks_Agent, Robot_Agent, Excel_Agent, Word_Agent

---

## 2. Revit Model — Key Levels (mm)
| Level Name | Elevation (mm) | Elevation (ft) |
|---|---|---|
| GROUND LEVEL | 0 | 0.0 |
| GROUND FLOOR LEVEL | +1000 | +3.281 |
| MEZZANINE FLR LEVEL | +3700 | +12.139 |
| INTERMEDIATE BEAM LEVEL | +4180 | +13.714 |
| ROOF BEAM LEVEL | +8095 | +26.558 |
| ROOF | +10515 | +34.498 |

## 3. Revit Model — Grid Lines (mm from origin)
**X-Axis (1–14):** 0, 3895, 7786, 12696, 16532, 20317, 24102, 27862, 33180, 37330, 41255, 45180, 49110, 53985  
**Y-Axis (A–J):** 0, 3150, 5680, 7815, 9267, 9864, 11736, 14475, 15865, 16550, 19050

## 4. Wall Types Used
- **Exterior**: `Generic - 225mm Masonry`
- **Interior**: `Interior - Blockwork 140`

---

## 5. IronPython 2.7 — Critical Rules for Revit Scripts

### NO f-strings — use .format() or %
```python
# WRONG
msg = f"Found {count} walls"
# CORRECT
msg = "Found %d walls" % count
msg = "Found {} walls".format(count)
```

### Always wrap modifications in Transaction
```python
from Autodesk.Revit.DB import *
with Transaction(doc, 'AI: Action Name') as t:
    t.Start()
    # ... your changes ...
    t.Commit()
```

### Units: always convert mm → feet
```python
MM = 1.0 / 304.8   # 1 mm in feet
feet = mm_value * MM
```

### out parameters — use ModelCurveArray()
```python
import clr
ref_obj = clr.Reference[ModelCurveArray](ModelCurveArray())
roof = doc.Create.NewFootPrintRoof(curves, level, roof_type, ref_obj)
curves_out = ref_obj.Value
```

---

## 6. MCP Communication Architecture

```
Antigravity AI
    │
    ▼  execute_revit_python(code)
MCP Server (mcp_server\server.py)
    │  → writes C:\Users\User\RevitAI_comm\request.json
    ▼
Revit Idling Event (startup.py)
    │  executes IronPython code
    │  → writes C:\Users\User\RevitAI_comm\response.json
    ▼
MCP Server reads response → returns to AI
```

**Key paths:**
- Revit IPC: `C:\Users\User\RevitAI_comm\`
- Navisworks IPC: `C:\Users\User\NavisworksAI_comm\`
- MCP server: `E:\My\pyrevit mcp ai\mcp_server\server.py`

---

## 7. Navisworks API Patterns

```python
import clr
clr.AddReference("Autodesk.Navisworks.Api")
clr.AddReference("Autodesk.Navisworks.Timeliner")
# doc = ActiveDocument, app = ActiveDocument.Database
doc.AppendFile(filepath)

# Timeliner
from Autodesk.Navisworks.Api.Timeliner import TimelinerTask
task = TimelinerTask()
task.DisplayName = "Task Name"
task.PlannedStartDate = System.DateTime(2025, 1, 1)
task.PlannedEndDate = System.DateTime(2025, 6, 30)
task.SimulationTaskTypeName = "Construct"
doc.Timeliner.TaskAddCopy(task)
```

---

## 8. Robot Structural Analysis API

```python
# COM connection (CPython 3, f-strings allowed here)
import win32com.client as win32
robot = win32.gencache.EnsureDispatch("Robot.Application")
robot.Visible = True
structure = robot.Project.Structure
robot.Project.Open(path)
robot.Project.Save()
```

---

## 9. DirectShape / Massing Pattern (Revit 2025)

For concept models, use TessellatedShapeBuilder with Mesh target + IList wrapper:

```python
import math
from Autodesk.Revit.DB import *
from System.Collections.Generic import List

builder = TessellatedShapeBuilder()
builder.OpenConnectedFaceSet(False)  # False = open mesh

def add_tri(bldr, a, b, c):
    verts = List[XYZ]()
    verts.Add(a); verts.Add(b); verts.Add(c)
    bldr.AddFace(TessellatedFace(verts, ElementId.InvalidElementId))

# ... add triangles ...

builder.CloseConnectedFaceSet()
builder.Target = TessellatedShapeBuilderTarget.Mesh
builder.Fallback = TessellatedShapeBuilderFallback.Salvage
builder.Build()
result = builder.GetBuildResult()

# MUST use IList wrapper — direct GetGeometricalObjects() fails SetShape
geo_list = List[GeometryObject]()
for g in result.GetGeometricalObjects():
    geo_list.Add(g)

cat_id = Category.GetCategory(doc, BuiltInCategory.OST_GenericModel).Id
with Transaction(doc, 'AI: Concept Mass') as t:
    t.Start()
    ds = DirectShape.CreateElement(doc, cat_id)
    ds.SetShape(geo_list)
    ds.Name = "Concept Shape"
    t.Commit()
```

---

## 10. Wall Thickness Filter Pattern (Revit 2025)

```python
from Autodesk.Revit.DB import *
from System.Collections.Generic import List

MM = 1.0 / 304.8
wall_cat_ids = List[ElementId]()
wall_cat_ids.Add(ElementId(BuiltInCategory.OST_Walls))
width_bip_id = ElementId(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)

rules = List[FilterRule]()
rules.Add(ParameterFilterRuleFactory.CreateGreaterOrEqualRule(width_bip_id, min_ft, 0.0001))
rules.Add(ParameterFilterRuleFactory.CreateLessRule(width_bip_id, max_ft, 0.0001))

elem_filter = ElementParameterFilter(rules)
pfe = ParameterFilterElement.Create(doc, "Filter Name", wall_cat_ids, elem_filter)

# Apply color override to view
ogs = OverrideGraphicSettings()
color = Color(255, 0, 0)
ogs.SetSurfaceForegroundPatternColor(color)
ogs.SetProjectionLineColor(color)
view.AddFilter(pfe.Id)
view.SetFilterOverrides(pfe.Id, ogs)
```

---

## 11. Common Pitfalls

| Issue | Solution |
|-------|----------|
| Wall corners with gaps ("kattak") | Calculate wall centreline from column outer edge + half wall thickness |
| Rebar at wrong Z | Add host level elevation to rebar Z coordinate |
| Door/window at wrong height | Add host wall's base level Z to insertion point |
| Roof offset | Use `BuiltInParameter.ROOF_LEVEL_OFFSET_PARAM` |
| 3D ViewFamily enum | Use `ViewFamily.ThreeDimensional` not `ThreeD` |
| Camera vectors not perpendicular | Compute `up = right.CrossProduct(forward).Normalize()` |

---

## 12. Revit Library Paths (This PC)
```
Doors: C:\ProgramData\Autodesk\RVT 2025\Libraries\English\UK\Doors\
```
