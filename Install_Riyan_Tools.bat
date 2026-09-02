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
    "$zipPath = Join-Path $env:TEMP 'RiyanTools.zip'; " ^
    "$extDir = Join-Path $env:APPDATA 'pyRevit\Extensions'; " ^
    "if (!(Test-Path $extDir)) { New-Item -ItemType Directory -Path $extDir -Force | Out-Null }; " ^
    "Write-Host 'Downloading repository package...'; " ^
    "Invoke-WebRequest -Uri 'https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip' -OutFile $zipPath; " ^
    "Write-Host 'Extracting files...'; " ^
    "Expand-Archive -Path $zipPath -DestinationPath $extDir -Force; " ^
    "Remove-Item $zipPath -Force; " ^
    "$extracted = Join-Path $extDir 'Riyan-Revit-Tools-main'; " ^
    "$final = Join-Path $extDir 'Riyan-Revit-Tools'; " ^
    "if (Test-Path $extracted) { " ^
    "  if (Test-Path $final) { Remove-Item $final -Recurse -Force }; " ^
    "  Rename-Item -Path $extracted -NewName 'Riyan-Revit-Tools'; " ^
    "}"

echo [3/3] Configuring pyRevit extension...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$cfg = Join-Path $env:APPDATA 'pyRevit\pyRevit_config.ini'; " ^
    "$target = Join-Path $env:APPDATA 'pyRevit\Extensions\Riyan-Revit-Tools'; " ^
    "if (Test-Path $cfg) { " ^
    "  $content = Get-Content $cfg -Raw; " ^
    "  if ($content -notmatch [regex]::Escape($target)) { " ^
    "    $escaped = $target.Replace('\', '\\'); " ^
    "    if ($content -match 'userextensions\s*=\s*\[(.*?)\]') { " ^
    "      $existing = $matches[1].Trim(); " ^
    "      if ($existing) { $newVal = \"userextensions = [$existing, `\"$escaped`\"]\" } else { $newVal = \"userextensions = [`\"$escaped`\"]\" }; " ^
    "      $content = $content -replace 'userextensions\s*=\s*\[.*?\]', $newVal; " ^
    "    } else { " ^
    "      $content = $content + \"`nuserextensions = [`\"$escaped`\"]`n\"; " ^
    "    }; " ^
    "    Set-Content $cfg $content; " ^
    "  } " ^
    "}"

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS INSTALLED SUCCESSFULLY!
echo ========================================================
echo.
echo You can now open Autodesk Revit.
echo The 'RIYAN' tab will appear on the top ribbon.
echo.
pause
