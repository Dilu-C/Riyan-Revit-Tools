@echo off
title Riyan Revit Tools 1-Click Installer
color 0B

echo ========================================================
echo            RIYAN REVIT TOOLS - 1-CLICK INSTALLER
echo ========================================================
echo.

echo [1/2] Cleaning up previous installations...
if exist "%APPDATA%\pyRevit\Extensions\Riyan.extension" rmdir /s /q "%APPDATA%\pyRevit\Extensions\Riyan.extension"
if exist "%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools" rmdir /s /q "%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools"

echo [2/2] Installing Riyan Revit Tools via pyRevit Git...
echo (Please wait, downloading tools from GitHub...)
call pyrevit extend ui Riyan https://github.com/Dilu-C/Riyan-Revit-Tools.git --branch=main --dest=user

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS INSTALLED SUCCESSFULLY!
echo ========================================================
echo.
echo You can now open Autodesk Revit.
echo The auto-updater will check for updates every time Revit starts.
echo.
pause
