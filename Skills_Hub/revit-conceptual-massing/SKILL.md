---
name: revit-conceptual-massing
description: >-
  Parametric and conceptual freeform massing in Autodesk Revit, including procedural curved geometry,
  DirectShape mesh generation via TessellatedShapeBuilder, and curtain system application on complex faces.
author: "Asanka (Sri Lanka) - Curated by Dilu"
office: "Sri Lanka & Maldives"
discipline: "BIM / Massing / Conceptual Design / Geometry"
version: "1.0.0"
---

# Revit Conceptual Massing & Procedural Freeform Geometry

Use this skill whenever creating, scripting, or generating organic freeform masses, curved curtain facades, or complex DirectShape geometry in Autodesk Revit.

---

## 1. DirectShape 3D Mesh Generation (`TessellatedShapeBuilder`)

When complex mathematical or procedural surfaces (e.g. hyperbolic paraboloids, organic shells, double-curved roofs) cannot be easily modeled via standard family extrusions, use `TessellatedShapeBuilder` to create native Revit DirectShape solids:

```python
from Autodesk.Revit.DB import *

def create_freeform_directshape(doc, triangles, category_id=BuiltInCategory.OST_Mass):
    """
    Creates a native DirectShape in Revit from a collection of 3D triangles.
    Each triangle is a tuple or list of 3 XYZ points: [(p0, p1, p2), ...]
    """
    builder = TessellatedShapeBuilder()
    builder.OpenConnectedFaceSet(True)
    
    for p0, p1, p2 in triangles:
        loop = [p0, p1, p2]
        face = TessellatedFace(loop, ElementId.InvalidElementId)
        builder.AddFace(face)
        
    builder.CloseConnectedFaceSet()
    builder.Target = TessellatedShapeBuilderTarget.Solid
    builder.Fallback = TessellatedShapeBuilderFallback.Mesh
    
    result = builder.Build()
    geometries = result.GetGeometricalObjects()
    
    tx = Transaction(doc, "Generate Procedural Freeform Shape")
    tx.Start()
    ds = DirectShape.CreateElement(doc, ElementId(category_id))
    ds.SetShape(geometries)
    tx.Commit()
    return ds
```

---

## 2. Generating Curved Curtain Systems on Freeform Faces

To apply curtain panels or mullions over organic massing faces:

```python
from Autodesk.Revit.DB import *

def apply_curtain_system_to_face(doc, face_reference, curtain_system_type):
    """Applies a curtain grid and panel system directly onto a mass face reference."""
    ref_array = ReferenceArray()
    ref_array.Append(face_reference)
    
    tx = Transaction(doc, "Apply Curtain System")
    tx.Start()
    cs = doc.Create.NewCurtainSystem2(ref_array, curtain_system_type)
    tx.Commit()
    return cs
```

---

## 3. Best Practices for High Stability in Freeform Geometries

1. **Verify Solid Closure**:
   - Ensure triangle face normals point outward consistently (counter-clockwise vertex ordering). Inconsistent winding orders cause Revit's Boolean geometry engine to fail solid generation and fall back to wireframes.
2. **Category Scoping**:
   - Use `BuiltInCategory.OST_Mass` for conceptual studies so Revit's mass visibility (`Show Mass by View Settings`) controls it properly.
   - For permanent structural/architectural geometry, scope to `BuiltInCategory.OST_GenericModel` or `BuiltInCategory.OST_Roofs`.
