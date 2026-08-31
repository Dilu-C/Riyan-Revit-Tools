# -*- coding: utf-8 -*-
"""Projects selected model lines onto a complex surface to generate beams."""

import traceback
from pyrevit import revit, DB, UI, forms
import sys
import clr

clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
from System.Windows.Media import Brushes

doc = revit.doc
uidoc = revit.uidoc

class CustomAlertWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name, msg, title):
        forms.WPFWindow.__init__(self, xaml_file_name)
        if title:
            self.Title = title
        self.MessageText.Text = msg

    def ok_clicked(self, sender, args):
        self.DialogResult = True
        self.Close()

def custom_alert(msg, title="Message", exitscript=False):
    import sys
    import os
    try:
        script_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(script_dir, 'alert.xaml')
        ui = CustomAlertWindow(xaml_path, msg, title)
        ui.ShowDialog()
    except Exception:
        pass
    if exitscript:
        sys.exit()

forms.alert = custom_alert

# Global state
selected_face_ref = None
selected_line_refs = []

class CurveSelectionFilter(UI.Selection.ISelectionFilter):
    def AllowElement(self, elem):
        return isinstance(elem, DB.CurveElement)
    def AllowReference(self, ref, pos):
        return True

def get_3d_view(document):
    view_collector = DB.FilteredElementCollector(document)\
        .OfClass(DB.View3D)\
        .WhereElementIsNotElementType()
    for v in view_collector:
        if not v.IsTemplate and not v.IsAssemblyView:
            return v
    return None

class BeamProjectorWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name, current_face, current_lines, last_beam_index):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self._current_face = current_face
        self._current_lines = current_lines
        self.action_requested = None
        self.selected_beam_type = None
        
        self.populate_beam_types()
        if last_beam_index is not None and last_beam_index < self.beam_type_cb.Items.Count:
            self.beam_type_cb.SelectedIndex = last_beam_index
            
        self.update_ui_state()

    def populate_beam_types(self):
        framing_types = DB.FilteredElementCollector(doc)\
            .OfCategory(DB.BuiltInCategory.OST_StructuralFraming)\
            .WhereElementIsElementType()\
            .ToElements()
            
        self.beam_types = {}
        for ft in framing_types:
            try:
                fam = ft.Family.Name
            except Exception:
                fam = getattr(ft, "FamilyName", "Beam")
            try:
                typ = ft.Name
            except Exception:
                typ = "Type"
                
            name = "{} - {}".format(fam, typ)
            self.beam_types[name] = ft
            
        for name in sorted(self.beam_types.keys()):
            self.beam_type_cb.Items.Add(name)
            
        if self.beam_type_cb.Items.Count > 0:
            self.beam_type_cb.SelectedIndex = 0

    def update_ui_state(self):
        if self._current_face:
            self.surface_status.Text = "Surface Checked"
            self.surface_status.Foreground = Brushes.Green
        else:
            self.surface_status.Text = "Not Selected"
            self.surface_status.Foreground = Brushes.Red
            
        if self._current_lines:
            self.lines_status.Text = "{} Lines Checked".format(len(self._current_lines))
            self.lines_status.Foreground = Brushes.Green
        else:
            self.lines_status.Text = "0 Selected"
            self.lines_status.Foreground = Brushes.Red

    def select_surface_clicked(self, sender, args):
        # We must CLOSE the UI completely to let Revit API take control without crashing
        self.action_requested = "pick_surface"
        self.DialogResult = True
        self.Close()

    def select_lines_clicked(self, sender, args):
        # We must CLOSE the UI completely to let Revit API take control without crashing
        self.action_requested = "pick_lines"
        self.DialogResult = True
        self.Close()

    def create_beams_clicked(self, sender, args):
        if not self._current_face:
            forms.alert("Please select a target surface first.")
            return
        if not self._current_lines:
            forms.alert("Please select model lines first.")
            return
            
        selected_beam_name = self.beam_type_cb.SelectedItem
        if not selected_beam_name:
            forms.alert("Please select a beam type.")
            return
            
        self.selected_beam_type = self.beam_types[selected_beam_name]
        self.action_requested = "generate"
        self.DialogResult = True
        self.Close()


def main():
    face_ref = None
    line_refs = []
    last_beam_index = 0

    # Safe UI Loop - Never call uidoc.Selection while UI is open!
    while True:
        try:
            ui = BeamProjectorWindow('ui.xaml', face_ref, line_refs, last_beam_index)
            if not ui.ShowDialog():
                return # User manually closed the window with 'X'
                
            last_beam_index = ui.beam_type_cb.SelectedIndex
            
            if ui.action_requested == "pick_surface":
                try:
                    face_ref = uidoc.Selection.PickObject(
                        UI.Selection.ObjectType.Face, 
                        "Select target Roof/Floor (supports multiple faces)"
                    )
                except Exception:
                    pass
                continue # Reopen UI loop
                
            elif ui.action_requested == "pick_lines":
                try:
                    refs = uidoc.Selection.PickObjects(
                        UI.Selection.ObjectType.Element, 
                        CurveSelectionFilter(), 
                        "Select Model Lines"
                    )
                    if refs:
                        line_refs = list(refs)
                except Exception:
                    pass
                continue # Reopen UI loop
                
            elif ui.action_requested == "generate":
                selected_beam_type = ui.selected_beam_type
                break # Exit loop to create beams
                
            else:
                return # Safety fallback

        except Exception as e:
            UI.TaskDialog.Show("UI Error", "Error in main loop:\n" + traceback.format_exc())
            return

    # User chose Generate, execute core logic
    
    target_element = doc.GetElement(face_ref)
    
    # Get the actual Face geometry from the selected face reference
    target_face = None
    try:
        target_face = target_element.GetGeometryObjectFromReference(face_ref)
    except Exception:
        pass
    
    if not target_face:
        forms.alert("Could not get surface geometry. Please try selecting the face again.", title="Error")
        return
    
    level = None
    if isinstance(doc.ActiveView, DB.ViewPlan):
        level = doc.ActiveView.GenLevel
    else:
        level = DB.FilteredElementCollector(doc).OfClass(DB.Level).FirstElement()
        
    if not level:
        forms.alert("No levels found for building beams.")
        return

    created_beams = []

    with revit.Transaction("Project Beams"):
        if not selected_beam_type.IsActive:
            selected_beam_type.Activate()
            
        for ref in line_refs:
            line_elem = doc.GetElement(ref)
            original_curve = line_elem.GeometryCurve
            
            # Dynamically divide curve based on length for high accuracy
            length = original_curve.Length
            num_segments = max(20, int(length / 0.25))  # Segment every ~75mm
            
            points = []
            for i in range(num_segments + 1):
                param = original_curve.GetEndParameter(0) + (original_curve.GetEndParameter(1) - original_curve.GetEndParameter(0)) * (i / float(num_segments))
                points.append(original_curve.Evaluate(param, False))
                
            # Project each point to nearest point on the selected face
            projected_pts = []
            for pt in points:
                try:
                    result = target_face.Project(pt)
                    if result:
                        projected_pts.append(result.XYZPoint)
                except Exception:
                    pass
            
            if len(projected_pts) < 2:
                continue
            
            # Clean duplicate/close points
            clean_points = [projected_pts[0]]
            for p in projected_pts[1:]:
                if p.DistanceTo(clean_points[-1]) > 0.05:
                    clean_points.append(p)

            if len(clean_points) < 2:
                continue
            
            # For 2 points, just create a straight beam
            if len(clean_points) == 2:
                try:
                    line = DB.Line.CreateBound(clean_points[0], clean_points[1])
                    beam = doc.Create.NewFamilyInstance(line, selected_beam_type, level, DB.Structure.StructuralType.Beam)
                    created_beams.append(beam)
                except Exception:
                    pass
                continue
            
            # For 3+ points: Flatten to best-fit plane, then create smooth spline beam
            # Revit beams MUST lie on a plane - this ensures that
            
            # Step 1: Compute best-fit plane using first, middle, and last points
            p0 = clean_points[0]
            p_mid = clean_points[len(clean_points) // 2]
            p_end = clean_points[-1]
            
            v1 = p_mid - p0
            v2 = p_end - p0
            normal = v1.CrossProduct(v2)
            n_len = normal.GetLength()
            
            # If points are nearly collinear, try using the surface normal at midpoint
            if n_len < 0.001:
                try:
                    mid_result = target_face.Project(p_mid)
                    if mid_result:
                        face_normal = target_face.ComputeNormal(mid_result.UVPoint)
                        # Use face normal and line direction to define plane
                        line_dir = p_end - p0
                        normal = line_dir.CrossProduct(face_normal)
                        n_len = normal.GetLength()
                except Exception:
                    pass
            
            if n_len < 0.001:
                # Points are truly collinear - create straight beam
                try:
                    line = DB.Line.CreateBound(clean_points[0], clean_points[-1])
                    beam = doc.Create.NewFamilyInstance(line, selected_beam_type, level, DB.Structure.StructuralType.Beam)
                    created_beams.append(beam)
                except Exception:
                    pass
                continue
            
            # Step 2: Normalize the plane normal
            normal = DB.XYZ(normal.X / n_len, normal.Y / n_len, normal.Z / n_len)
            
            # Step 3: Flatten all projected points onto this plane
            planar_pts = []
            for p in clean_points:
                v = p - p0
                dist = v.DotProduct(normal)
                planar_pts.append(DB.XYZ(p.X - normal.X * dist, p.Y - normal.Y * dist, p.Z - normal.Z * dist))
            
            # Re-clean flattened points (some may merge after flattening)
            final_pts = [planar_pts[0]]
            for p in planar_pts[1:]:
                if p.DistanceTo(final_pts[-1]) > 0.05:
                    final_pts.append(p)
            
            if len(final_pts) < 2:
                continue
            
            # Step 4: Create smooth beam
            try:
                if len(final_pts) == 2:
                    curve = DB.Line.CreateBound(final_pts[0], final_pts[1])
                else:
                    curve = DB.HermiteSpline.Create(final_pts, False)
                beam = doc.Create.NewFamilyInstance(curve, selected_beam_type, level, DB.Structure.StructuralType.Beam)
                created_beams.append(beam)
            except Exception:
                # Absolute last resort: straight beam from start to end
                try:
                    line = DB.Line.CreateBound(clean_points[0], clean_points[-1])
                    beam = doc.Create.NewFamilyInstance(line, selected_beam_type, level, DB.Structure.StructuralType.Beam)
                    created_beams.append(beam)
                except Exception:
                    pass

    if created_beams:
        forms.alert("Successfully created {} projected beams.".format(len(created_beams)), title="Success")
    else:
        forms.alert("Failed to project beams. Lines may not align with surface.", title="Warning")

if __name__ == '__main__':
    main()
