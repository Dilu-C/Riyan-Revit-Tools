@echo off
title Riyan Revit Tools 1-Click Installer
color 0B

echo ========================================================
echo            RIYAN REVIT TOOLS - 1-CLICK INSTALLER
echo ========================================================
echo.

echo [1/3] Cleaning up previous installation...
if exist "%APPDATA%\pyRevit\Extensions\Riyan.extension" rmdir /s /q "%APPDATA%\pyRevit\Extensions\Riyan.extension"
if exist "%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools" rmdir /s /q "%APPDATA%\pyRevit\Extensions\Riyan-Revit-Tools"

echo [2/3] Downloading latest tools from GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    " = Join-Path C:\Users\User\AppData\Local\Temp 'RiyanTools.zip'; " ^
    " = Join-Path C:\Users\User\AppData\Roaming 'pyRevit\Extensions'; " ^
    "if (!(Test-Path )) { New-Item -ItemType Directory -Path  -Force | Out-Null }; " ^
    "Write-Host 'Downloading repository package...'; " ^
    "Invoke-WebRequest -Uri 'https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip' -OutFile ; " ^
    "Write-Host 'Extracting files...'; " ^
    "Expand-Archive -Path  -DestinationPath  -Force; " ^
    "Remove-Item  -Force; " ^
    " = Join-Path  'Riyan-Revit-Tools-main'; " ^
    " = Join-Path  'Riyan-Revit-Tools'; " ^
    "if (Test-Path ) { " ^
    "  if (Test-Path ) { Remove-Item  -Recurse -Force }; " ^
    "  Rename-Item -Path  -NewName 'Riyan-Revit-Tools'; " ^
    "}"

echo [3/3] Configuring pyRevit extension...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    " = Join-Path C:\Users\User\AppData\Roaming 'pyRevit\pyRevit_config.ini'; " ^
    " = Join-Path C:\Users\User\AppData\Roaming 'pyRevit\Extensions\Riyan-Revit-Tools'; " ^
    "if (Test-Path ) { " ^
    "   = Get-Content  -Raw; " ^
    "  if ( -notmatch [regex]::Escape()) { " ^
    "     = .Replace('\', '\\'); " ^
    "    if ( -match 'userextensions\s*=\s*\[(.*?)\]') { " ^
    "       = [1].Trim(); " ^
    "      if () {  = \"userextensions = [, \"\"]\" } else {  = \"userextensions = [\"\"]\" }; " ^
    "       =  -replace 'userextensions\s*=\s*\[.*?\]', ; " ^
    "    } else { " ^
    "       =  + \"
userextensions = [\"\"]
\"; " ^
    "    }; " ^
    "    Set-Content  ; " ^
    "  } " ^
    "}"

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS INSTALLED SUCCESSFULLY!
echo ========================================================
echo.
echo Please restart Revit, or click pyRevit Reload.
echo.
pause
