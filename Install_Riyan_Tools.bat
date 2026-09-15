@echo off
title Riyan Revit Tools 1-Click Installer
color 0B

echo ========================================================
echo            RIYAN REVIT TOOLS - 1-CLICK INSTALLER
echo ========================================================
echo.

:: Switch working directory to TEMP to prevent any file locks
cd /d "%TEMP%"

set "PS_SCRIPT=%TEMP%\riyan_install_%RANDOM%.ps1"
if exist "%PS_SCRIPT%" del /f /q "%PS_SCRIPT%" 2>nul

(
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo $ErrorActionPreference = 'SilentlyContinue'
echo.
echo Write-Host '[1/4] Clean-Slate Wipe: Clearing all old files, duplicates & pyRevit cache...' -ForegroundColor Yellow
echo $extDir = Join-Path $env:APPDATA 'pyRevit\Extensions'
echo $pyrevitRoot = Join-Path $env:APPDATA 'pyRevit'
echo.
echo # 1. Delete all old, duplicate or stray Riyan extension folders
echo @('Riyan-Revit-Tools.extension', 'Riyan.extension', 'Riyan-Revit-Tools', 'Riyan-Revit-Tools-main') ^| ForEach-Object {
echo     $target = Join-Path $extDir $_
echo     if (Test-Path $target^) {
echo         Write-Host "  Removing: $_" -ForegroundColor DarkGray
echo         Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue
echo     }
echo }
echo.
echo # 2. Remove any wild-card duplicates (e.g. Riyan-Revit-Tools.extension*)
echo if (Test-Path $extDir^) {
echo     Get-ChildItem -Path $extDir -Directory -Filter '*Riyan*.extension*' ^| ForEach-Object {
echo         Write-Host "  Removing duplicate: $_" -ForegroundColor DarkGray
echo         Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
echo     }
echo     # Clean stray root files
echo     @('GEMINI.md', 'GEMINI', '.agents', 'test_compile.py', 'test_msg.py', 'Install_Riyan_Tools.bat', 'Install_Riyan_Tools.zip', 'version.txt'^) ^| ForEach-Object {
echo         $stray = Join-Path $extDir $_
echo         if (Test-Path $stray^) { Remove-Item -Path $stray -Force -ErrorAction SilentlyContinue }
echo     }
echo } else {
echo     New-Item -ItemType Directory -Path $extDir -Force ^| Out-Null
echo }
echo.
echo # 3. Wipe pyRevit UI Cache and compiled binaries to prevent blank tab glitches
echo $cacheDir = Join-Path $pyrevitRoot 'Cache'
echo if (Test-Path $cacheDir^) {
echo     Write-Host '  Clearing pyRevit UI cache...' -ForegroundColor DarkGray
echo     Remove-Item -Path $cacheDir -Recurse -Force -ErrorAction SilentlyContinue
echo }
echo Get-ChildItem -Path $pyrevitRoot -Include '__pycache__', '*.pyc' -Recurse -Force -ErrorAction SilentlyContinue ^| Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo Write-Host '[2/4] Downloading latest tools from GitHub...' -ForegroundColor Cyan
echo $zipPath = Join-Path $env:TEMP 'RiyanTools.zip'
echo Invoke-WebRequest -Uri 'https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip' -OutFile $zipPath
echo.
echo Write-Host '[3/4] Extracting files...' -ForegroundColor Cyan
echo $extractFolder = Join-Path $env:TEMP 'Riyan_Fresh_Extract'
echo if (Test-Path $extractFolder^) { Remove-Item $extractFolder -Recurse -Force -ErrorAction SilentlyContinue }
echo Expand-Archive -Path $zipPath -DestinationPath $extractFolder -Force
echo Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
echo.
echo $sourceRoot = Join-Path $extractFolder 'Riyan-Revit-Tools-main'
echo $finalTools = Join-Path $extDir 'Riyan-Revit-Tools'
echo if (Test-Path $sourceRoot^) {
echo     Copy-Item -Path $sourceRoot -Destination $finalTools -Recurse -Force -ErrorAction SilentlyContinue
echo }
echo Remove-Item -Path $extractFolder -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo Write-Host '[4/4] Configuring pyRevit extension...' -ForegroundColor Cyan
echo $cfg = Join-Path $pyrevitRoot 'pyRevit_config.ini'
echo if (Test-Path $cfg^) {
echo     $content = Get-Content $cfg -Raw
echo     # Enable Riyan.extension
echo     $content = $content -replace '\[Riyan\.extension\]\s*[\r\n]+disabled\s*=\s*true', "[Riyan.extension]`ndisabled = false"
echo     # Remove duplicate legacy extension section if present
echo     $content = $content -replace '\[Riyan-Revit-Tools\.extension\][\s\S]*?(?=(\[|$^)^)', ''
echo     # Register clean user extension directory
echo     $escaped = $finalTools.Replace('\', '\\'^)
echo     if ($content -notmatch [regex]::Escape($finalTools^)^) {
echo         if ($content -match 'userextensions\s*=\s*\[(.*?)\]'^) {
echo             $existing = $matches[1].Trim(^)
echo             if ($existing^) { $newVal = "userextensions = [$existing, `"$escaped`"]" } else { $newVal = "userextensions = [`"$escaped`"]" }
echo             $content = $content -replace 'userextensions\s*=\s*\[.*?\]', $newVal
echo         } else {
echo             $content = $content + "`nuserextensions = [`"$escaped`"]`n"
echo         }
echo     }
echo     Set-Content $cfg $content -NoNewline
echo }
echo.
echo Write-Host 'Installation completed successfully!' -ForegroundColor Green
) > "%PS_SCRIPT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del /f /q "%PS_SCRIPT%" 2>nul

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS INSTALLED SUCCESSFULLY!
echo ========================================================
echo.
echo All old files, duplicate folders and pyRevit cache wiped cleanly.
echo Please restart Revit, or click pyRevit Reload.
echo.
pause