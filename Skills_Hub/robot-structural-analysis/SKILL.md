---
name: robot-structural-analysis
description: Automation patterns, COM scripting, and structural analysis workflows for Autodesk Robot Structural Analysis Professional 2025 using Python (pywin32).
author: "Asanka (Sri Lanka) - Curated by Dilu"
office: "Sri Lanka"
discipline: "Structural Engineering / Analysis"
version: "1.0.0"
---

# Robot Structural Analysis 2025 Automation Guide

This skill provides patterns for controlling Autodesk Robot Structural Analysis Professional 2025 via Windows COM using Python.

---

## 1. Architecture & Environment
- **Interface**: Windows COM Out-of-Process (`Robot.Application`).
- **Python Runtime**: Standard **CPython 3.x** using the `pywin32` library.
- **Prerequisites**:
  - Autodesk Robot Structural Analysis 2025 must be installed.
  - Python package: `pip install pywin32`

---

## 2. Connecting to Robot COM Server
```python
import win32com.client as win32

# Connect to running Robot instance or start a new one
robot = win32.gencache.EnsureDispatch("Robot.Application")

# Control UI visibility
robot.Visible = True
robot.Interactive = 1  # 1 = Interactive, 0 = Background
```

---

## 3. Project Management (Open, Save, Structure Access)
```python
project = robot.Project

# Open an existing RTD model
project.Open(r"C:\Projects\StructuralModels\Tower_Analysis.rtd")

# Access the structural model database
structure = project.Structure

# Query nodes and bars
nodes = structure.Nodes
bars = structure.Bars
print(f"Total Nodes: {nodes.Count}, Total Bars: {bars.Count}")

# Save the project
project.Save()
```

---

## 4. Best Practices & Safety
- **COM Release**: Always close or release COM objects when long batch runs complete to prevent orphaned background processes.
- **Unit Awareness**: Ensure project unit settings (Metric kN/m vs Imperial kips/ft) match the parameters passed through COM methods.