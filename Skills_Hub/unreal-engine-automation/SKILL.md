---
name: unreal-engine-automation
description: >-
  Automating Unreal Engine 5.x via Python Remote Execution for architectural visualization,
  batch FBX/NWC model imports, camera sequencing, and real-time walkthroughs.
author: "Asanka (Sri Lanka) - Curated by Dilu"
office: "Sri Lanka & Maldives"
discipline: "Visualization / Realtime / Automation"
version: "1.0.0"
---

# Unreal Engine 5 Automation via Python Remote Execution

Use this skill when interacting with, inspecting, or automating Unreal Engine 5 (UE 5.0 - 5.5+) from Antigravity.

---

## 1. Prerequisites in Unreal Engine

1. In Unreal Editor, open **Project Settings**:
   - Go to **Plugins -> Python**.
   - Enable **Enable Remote Execution**.
2. Keep the Unreal Editor project open in the background.

---

## 2. Remote Execution Connection Pattern

Unreal Engine broadcasts its presence over UDP multicast. Use Python's built-in socket/multicast or Unreal's bundled `remote_execution` module:

```python
import os
import sys
import time

def find_ue_remote_execution():
    """Locates the Python remote execution library across UE installations."""
    for base in [r"C:\Program Files\Epic Games\UE_5.5", r"C:\Program Files\Epic Games\UE_5.4", r"C:\Program Files\Epic Games\UE_5.3"]:
        py_dir = os.path.join(base, r"Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
        if os.path.exists(py_dir):
            if py_dir not in sys.path:
                sys.path.append(py_dir)
            return True
    return False

def execute_unreal_code(python_code):
    """Executes Python code remotely inside the running Unreal Editor."""
    if not find_ue_remote_execution():
        return {"success": False, "error": "Unreal PythonScriptPlugin path not found."}
        
    import remote_execution
    config = remote_execution.RemoteExecutionConfig()
    config.multicast_bind_address = '127.0.0.1'
    remote_exec = remote_execution.RemoteExecution(config)
    remote_exec.start()
    time.sleep(1.5)  # Wait for node discovery

    try:
        nodes = remote_exec.remote_nodes
        if not nodes:
            return {"success": False, "error": "No running Unreal Editor instance found."}

        node = nodes[0]
        remote_exec.open_command_connection(node.get("node_id"))
        time.sleep(0.5)

        result = remote_exec.run_command(python_code, unattended=True)
        return {
            "success": result.get("success", False) if result else False,
            "output": result.get("output", "") if result else ""
        }
    finally:
        remote_exec.stop()
```

---

## 3. High-Value Automation Tasks in Unreal

### A. Batch Importing Datasmith / FBX Files
```python
import unreal

def import_fbx(file_path, destination_path="/Game/BIM_Models"):
    task = unreal.AssetImportTask()
    task.filename = file_path
    task.destination_path = destination_path
    task.replace_existing = True
    task.automated = True
    
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_materials = True
    options.import_textures = True
    task.options = options
    
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
```

### B. Spawning Perspective Camera & Setting Transform
```python
import unreal

def spawn_camera(location, rotation, actor_name="BIM_Walkthrough_Camera"):
    actor_location = unreal.Vector(location[0], location[1], location[2])
    actor_rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
    
    world = unreal.EditorLevelLibrary.get_editor_world()
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, actor_location, actor_rotation)
    camera.set_actor_label(actor_name)
    return camera
```
