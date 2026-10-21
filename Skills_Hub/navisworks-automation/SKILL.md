---
name: navisworks-automation
description: Guidelines, API patterns, and automation workflows for Autodesk Navisworks 2025 using Python, C# plugins, 4D Timeliner scheduling, and model coordination.
author: "Asanka (Sri Lanka) - Curated by Dilu"
office: "Sri Lanka"
discipline: "BIM / Coordination / Navisworks"
version: "1.0.0"
---

# Navisworks 2025 Automation & 4D Simulation Guide

This skill provides step-by-step API patterns, architecture, and code templates for automating Autodesk Navisworks 2025.

---

## 1. Environment & Target Framework
- **Runtime**: Unlike Revit 2025 (which runs .NET 8.0), **Navisworks 2025 runs on .NET Framework 4.8**.
- **Embedded Python**: Uses IronPython 2.7 when running inside Navisworks plugins or IPC.
- **External C# Plugins**: Must target `.NET Framework 4.8`.
- **Plugin Directory**:
  `%APPDATA%\Autodesk\Navisworks Manage 2025\Plugins\<PluginName>\`

---

## 2. Injected Global Variables & References
When running IronPython scripts inside Navisworks:

```python
import clr
clr.AddReference("Autodesk.Navisworks.Api")
clr.AddReference("Autodesk.Navisworks.Timeliner")

from Autodesk.Navisworks.Api import Application, ModelItemCollection
from Autodesk.Navisworks.Api.Timeliner import TimelinerTask, DocumentTimeliner

# Key Application Globals:
# doc: ActiveDocument
# app: ActiveDocument.Database
doc = Application.ActiveDocument
```

---

## 3. Appending and Managing Model Files
To programmatically append NWC, DWG, or IFC models into the active session:

```python
# Append model file
filepath = r"C:\Projects\ExportedModels\Structural.nwc"
doc.AppendFile(filepath)
```

---

## 4. Timeliner & 4D Construction Simulation
Automate 4D schedules, tasks, and element assignments:

```python
import System
from Autodesk.Navisworks.Api.Timeliner import TimelinerTask

# Access the Timeliner document part
timeliner = doc.Timeliner

# Clear existing tasks if rebuilding
# timeliner.TasksClear()

# Create a new simulation task
task = TimelinerTask()
task.DisplayName = "Cast-in-Place Concrete Columns"
task.PlannedStartDate = System.DateTime(2026, 11, 1)
task.PlannedEndDate = System.DateTime(2026, 11, 15)

# Simulation Types: "Construct", "Demolish", "Temporary"
task.SimulationTaskTypeName = "Construct"

# Attach model elements (ModelItemCollection) to task
# task.Selection.CopyFrom(selected_items)

# Commit the task to the root schedule
timeliner.TaskAddCopy(task)
```

---

## 5. Camera & 3D Perspective Views
When calculating perspective view vectors, Revit and Navisworks will throw exceptions if the `up` and `forward` camera vectors are not mathematically perpendicular.

**Correct Perpendicular Calculation**:
```python
# target = XYZ point being looked at, eye = XYZ camera location
forward = (target - eye).Normalize()
right = forward.CrossProduct(XYZ(0, 0, 1)).Normalize()
up = right.CrossProduct(forward).Normalize()
```