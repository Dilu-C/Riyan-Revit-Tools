import os
import shutil
import filecmp

def is_valid_path(path):
    try:
        if not os.path.exists(path):
            print("Path does not exist: {0}".format(path))
            return False
        if not os.path.isdir(path):
            print("Path is not a directory: {0}".format(path))
            return False
        return True
    except Exception as e:
        print("An error occurred while checking the path: {0}\n{1}".format(path, e))
        return False

def sync_directories(src, dst):
    if not is_valid_path(src) or not is_valid_path(dst):
        return

    src_files = set(os.listdir(src))
    dst_files = set(os.listdir(dst))

    # Delete files in the destination that are not in the source
    for file in dst_files - src_files:
        file_path = os.path.join(dst, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete: {0}\n{1}".format(file_path, e))

    # Copy/update files from the source to the destination
    for file in src_files:
        src_file = os.path.join(src, file)
        dst_file = os.path.join(dst, file)
        try:
            if os.path.isfile(src_file):
                if not os.path.exists(dst_file) or not filecmp.cmp(src_file, dst_file, shallow=False):
                    shutil.copy2(src_file, dst_file)
            elif os.path.isdir(src_file):
                if not os.path.exists(dst_file):
                    shutil.copytree(src_file, dst_file)
                else:
                    sync_directories(src_file, dst_file)
        except Exception as e:
            print("Failed to copy/update: {0}\n{1}".format(src_file, e))

# First pair of source and destination
source_path_1 = os.path.join(os.environ['APPDATA'], "pyRevit\Extensions\Riyan.extension\Other")
destination_path_1 = r"C:\ProgramData\RIY\Other"

# Second pair of source and destination
source_path_2 = os.path.join(os.environ['APPDATA'], "pyRevit\Extensions\Riyan.extension\Other\Dynamo\Settings")
destination_path_2 = os.path.join(os.environ['APPDATA'], "Dynamo\Dynamo Revit")  # Corrected path

# Ensure the destination directories exist
if not os.path.exists(destination_path_1):
    os.makedirs(destination_path_1)
if not os.path.exists(destination_path_2):
    os.makedirs(destination_path_2)

# Perform the synchronization for the first pair
sync_directories(source_path_1, destination_path_1)
print("Reload for first pair complete.")

# Perform the synchronization for the second pair
sync_directories(source_path_2, destination_path_2)
print("Reload for second pair complete.")
