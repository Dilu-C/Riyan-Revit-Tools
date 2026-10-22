---
name: revit-surface-snapping
description: >-
  Automated, single-pass mathematical alignment and snapping of 2D/3D Model Lines,
  structural framing centerlines, and rafters to sloped Roof or Floor Slab bottom/top
  planar surfaces without distorting plan (X, Y) coordinates, plus vertical Z-offset beam placement.
author: "Dilu (BIM Automation)"
office: "Sri Lanka & Maldives"
discipline: "Revit / Structural / Architectural / Geometry"
version: "1.1.0"
---

# Revit Surface Snapping & 3D Line Projection Engine

Use this skill whenever aligning, projecting, or placing Model Curves, layout lines, or structural framing (beams/rafters) along sloped roofs, floors, or irregular ceiling surfaces in Autodesk Revit.

---

## 1. Core Geometric Invariants (Strict Protection)

1. **Zero Plan $(X, Y)$ Distortion**:
   - The $(X, Y)$ plan positions of endpoints must NEVER be shifted, translated, scaled, or rotated.
   - Only the **$Z$ elevation** of each endpoint ($p_0.Z, p_1.Z$) is calculated and adjusted.
2. **Bottom Face vs. Top Face Normal Filtering**:
   - For rafters/framing below a roof: target bottom faces where normal $N_z < -0.05$.
   - For slabs/floors above: target top faces where normal $N_z > 0.05$.
3. **Target Host Element Scoping**:
   - Always scope geometric collection to the active host element (Roof/Slab) in the active view/selection to prevent cross-level face interference.
4. **Resilient Dynamic SketchPlane**:
   - Revit 3D `ModelCurve` elements require a non-collinear `SketchPlane`. Construct the plane using the line vector and its cross product with the vertical basis.
5. **Strict Vertical $(Z)$ Offset for Structural Framing**:
   - When placing beams along aligned lines with an offset (e.g., beam centerline offset or clearance from surface), the offset must be applied **strictly along the vertical $Z$ axis** ($p_0.Z + \Delta Z, p_1.Z + \Delta Z$) with $(X, Y)$ 100% frozen.

---

## 2. Mathematical Projection Formula

For any planar face with origin $\mathbf{O} = (O_x, O_y, O_z)$ and unit normal $\mathbf{N} = (N_x, N_y, N_z)$, the exact $Z$ elevation at any given plan coordinate $(X, Y)$ is:

$$Z(X, Y) = O_z - \frac{N_x (X - O_x) + N_y (Y - O_y)}{N_z}$$

This delivers infinite sub-millimeter precision in $\mathcal{O}(1)$ time without iterative geometric ray-casting.

---

## 3. High-Speed Implementation Pattern (C# / Revit API)

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

public static class SurfaceSnapEngine
{
    public static void SnapLinesToRoofBottom(Document doc, IList<ElementId> lineIds, RoofBase roof)
    {
        var opt = new Options { DetailLevel = ViewDetailLevel.Fine, ComputeReferences = true };
        var geom = roof.get_Geometry(opt);
        
        // 1. Collect bottom planar faces
        var bottomFaces = new List<PlanarFace>();
        foreach (var gObj in geom)
        {
            if (gObj is Solid s && s.Volume > 0.001)
            {
                foreach (Face f in s.Faces)
                {
                    if (f is PlanarFace pf && pf.FaceNormal.Z < -0.05)
                        bottomFaces.Add(pf);
                }
            }
        }

        using var tx = new Transaction(doc, "Snap Lines to Roof Bottom");
        tx.Start();

        foreach (var id in lineIds)
        {
            if (doc.GetElement(id) is not ModelCurve mc) continue;
            var line = mc.GeometryCurve as Line;
            if (line == null) continue;

            XYZ p0 = line.GetEndPoint(0);
            XYZ p1 = line.GetEndPoint(1);

            // 2. Find matching planar face containing both endpoints (or closest face)
            PlanarFace targetFace = null;
            foreach (var face in bottomFaces)
            {
                var uv0 = face.Project(p0);
                var uv1 = face.Project(p1);
                if (uv0 != null && uv1 != null)
                {
                    targetFace = face;
                    break;
                }
            }
            if (targetFace == null) targetFace = bottomFaces.FirstOrDefault();
            if (targetFace == null) continue;

            // 3. Compute exact Z elevations using planar equation
            var n = targetFace.FaceNormal;
            var o = targetFace.Origin;

            double z0 = o.Z - (n.X * (p0.X - o.X) + n.Y * (p0.Y - o.Y)) / n.Z;
            double z1 = o.Z - (n.X * (p1.X - o.X) + n.Y * (p1.Y - o.Y)) / n.Z;

            XYZ newP0 = new XYZ(p0.X, p0.Y, z0);
            XYZ newP1 = new XYZ(p1.X, p1.Y, z1);

            // 4. Construct resilient SketchPlane
            XYZ lineDir = (newP1 - newP0).Normalize();
            XYZ perp = lineDir.CrossProduct(XYZ.BasisZ);
            if (perp.GetLength() < 1e-4) perp = lineDir.CrossProduct(XYZ.BasisX);
            perp = perp.Normalize();

            Plane plane = Plane.CreateByNormalAndOrigin(perp, newP0);
            SketchPlane sp = SketchPlane.Create(doc, plane);

            // 5. Replace with new sloped 3D curve & preserve Graphic Style
            var newCurve = doc.Create.NewModelCurve(Line.CreateBound(newP0, newP1), sp);
            if (mc.LineStyle != null) newCurve.LineStyle = mc.LineStyle;

            doc.Delete(mc.Id);
        }

        tx.Commit();
    }
}
```

---

## 4. Python Implementation (pyRevit / IronPython / CPython 3)

```python
from Autodesk.Revit.DB import *

def calculate_surface_z(planar_face, x, y):
    n = planar_face.FaceNormal
    o = planar_face.Origin
    if abs(n.Z) < 1e-6:
        return o.Z
    return o.Z - (n.X * (x - o.X) + n.Y * (y - o.Y)) / n.Z

def snap_model_line_to_face(doc, model_curve, planar_face):
    curve = model_curve.GeometryCurve
    p0 = curve.GetEndPoint(0)
    p1 = curve.GetEndPoint(1)
    
    z0 = calculate_surface_z(planar_face, p0.X, p0.Y)
    z1 = calculate_surface_z(planar_face, p1.X, p1.Y)
    
    new_p0 = XYZ(p0.X, p0.Y, z0)
    new_p1 = XYZ(p1.X, p1.Y, z1)
    
    line_dir = (new_p1 - new_p0).Normalize()
    perp = line_dir.CrossProduct(XYZ.BasisZ)
    if perp.GetLength() < 1e-4:
        perp = line_dir.CrossProduct(XYZ.BasisX)
    perp = perp.Normalize()
    
    plane = Plane.CreateByNormalAndOrigin(perp, new_p0)
    sp = SketchPlane.Create(doc, plane)
    
    new_mc = doc.Create.NewModelCurve(Line.CreateBound(new_p0, new_p1), sp)
    if model_curve.LineStyle:
        new_mc.LineStyle = model_curve.LineStyle
        
    doc.Delete(model_curve.Id)
    return new_mc
```

---

## 5. Structural Framing / Beam Placement with Vertical (Z) Centerline Offset

When placing beams along aligned sloped model lines or curves:
- **Zero Plan $(X, Y)$ Drift**: The plan coordinates $(p_0.X, p_0.Y)$ and $(p_1.X, p_1.Y)$ remain 100% frozen.
- **Vertical Centerline Offset ($\Delta Z$)**: Apply the offset strictly to the $Z$ component of both endpoints.

```python
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType

def place_beam_along_sloped_line(doc, model_curve_or_line, beam_symbol, level, delta_z_feet=0.0):
    """
    Places a Structural Framing (Beam) instance along a 3D line with an explicit vertical Z-offset.
    X and Y plan coordinates are strictly preserved.
    """
    if hasattr(model_curve_or_line, "GeometryCurve"):
        curve = model_curve_or_line.GeometryCurve
    else:
        curve = model_curve_or_line

    p0 = curve.GetEndPoint(0)
    p1 = curve.GetEndPoint(1)

    # 1. Apply vertical offset strictly to Z
    offset_p0 = XYZ(p0.X, p0.Y, p0.Z + delta_z_feet)
    offset_p1 = XYZ(p1.X, p1.Y, p1.Z + delta_z_feet)
    sloped_line = Line.CreateBound(offset_p0, offset_p1)

    # 2. Activate family symbol
    if not beam_symbol.IsActive:
        beam_symbol.Activate()
        doc.Regenerate()

    # 3. Create the beam instance directly on the 3D curve
    beam = doc.Create.NewFamilyInstance(sloped_line, beam_symbol, level, StructuralType.Beam)

    # 4. Enforce Center justification on beam if requested
    # Z Justification: 0 = Top, 1 = Center, 2 = Bottom
    z_just_param = beam.get_Parameter(BuiltInParameter.Z_JUSTIFICATION)
    if z_just_param and not z_just_param.IsReadOnly:
        z_just_param.Set(1)  # 1 = Centerline placement

    return beam
```

### High-Speed C# Equivalent:
```csharp
public static FamilyInstance PlaceBeamWithVerticalOffset(
    Document doc, Line baseCurve, FamilySymbol beamSymbol, Level level, double deltaZ)
{
    XYZ p0 = baseCurve.GetEndPoint(0);
    XYZ p1 = baseCurve.GetEndPoint(1);

    // Keep X and Y frozen, offset only Z
    XYZ offsetP0 = new XYZ(p0.X, p0.Y, p0.Z + deltaZ);
    XYZ offsetP1 = new XYZ(p1.X, p1.Y, p1.Z + deltaZ);
    Line beamLine = Line.CreateBound(offsetP0, offsetP1);

    if (!beamSymbol.IsActive)
    {
        beamSymbol.Activate();
        doc.Regenerate();
    }

    var beam = doc.Create.NewFamilyInstance(
        beamLine, beamSymbol, level, Autodesk.Revit.DB.Structure.StructuralType.Beam);

    // Ensure Center Z justification
    var pZJust = beam.get_Parameter(BuiltInParameter.Z_JUSTIFICATION);
    if (pZJust != null && !pZJust.IsReadOnly)
    {
        pZJust.Set(1); // Center
    }

    return beam;
}
```
