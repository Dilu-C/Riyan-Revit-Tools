@echo off
title Riyan Revit Tools 1-Click Updater
color 0B

echo ========================================================
echo            RIYAN REVIT TOOLS - 1-CLICK UPDATER
echo ========================================================
echo.

:: Switch working directory to TEMP to prevent any file locks
cd /d "%TEMP%"

set "PS_SCRIPT=%TEMP%\riyan_update_%RANDOM%.ps1"
if exist "%PS_SCRIPT%" del /f /q "%PS_SCRIPT%" 2>nul

(
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo $ErrorActionPreference = 'SilentlyContinue'
echo.
echo Write-Host '[1/4] Clean-Slate Wipe: Clearing old duplicates & pyRevit cache...' -ForegroundColor Yellow
echo $extDir = Join-Path $env:APPDATA 'pyRevit\Extensions'
echo $pyrevitRoot = Join-Path $env:APPDATA 'pyRevit'
echo $targetTools = Join-Path $extDir 'Riyan-Revit-Tools'
echo.
echo # 1. Delete all old legacy duplicate folders
echo @('Riyan-Revit-Tools.extension', 'Riyan.extension', 'Riyan-Revit-Tools-main') ^| ForEach-Object {
echo     $target = Join-Path $extDir $_
echo     if (Test-Path $target^) {
echo         Write-Host "  Removing: $_" -ForegroundColor DarkGray
echo         Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue
echo     }
echo }
echo if (Test-Path $extDir^) {
echo     Get-ChildItem -Path $extDir -Directory -Filter '*Riyan*.extension*' ^| ForEach-Object {
echo         Write-Host "  Removing duplicate: $_" -ForegroundColor DarkGray
echo         Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
echo     }
echo     # Clean stray root files
echo     @('GEMINI.md', 'GEMINI', '.agents', 'test_compile.py', 'test_msg.py') ^| ForEach-Object {
echo         $stray = Join-Path $extDir $_
echo         if (Test-Path $stray^) { Remove-Item -Path $stray -Force -ErrorAction SilentlyContinue }
echo     }
echo }
echo.
echo # 2. Clean tools directory contents (except updater itself if preserved)
echo if (Test-Path $targetTools^) {
echo     Get-ChildItem -Path $targetTools -Force ^| Where-Object { $_.Name -ne 'Update_Riyan_Tools.bat' } ^| Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
echo }
echo.
echo # 3. Wipe pyRevit UI Cache and compiled binaries
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
echo $extractFolder = Join-Path $env:TEMP 'Riyan_Extract'
echo if (Test-Path $extractFolder^) { Remove-Item $extractFolder -Recurse -Force -ErrorAction SilentlyContinue }
echo Expand-Archive -Path $zipPath -DestinationPath $extractFolder -Force
echo Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
echo.
echo $sourceRoot = Join-Path $extractFolder 'Riyan-Revit-Tools-main'
echo if (!(Test-Path $targetTools^)^) { New-Item -ItemType Directory -Path $targetTools -Force ^| Out-Null }
echo Copy-Item -Path (Join-Path $sourceRoot '*'^) -Destination $targetTools -Recurse -Force -ErrorAction SilentlyContinue
echo Remove-Item -Path $extractFolder -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo Write-Host '[4/4] Ensuring clean pyRevit configuration...' -ForegroundColor Cyan
echo $cfg = Join-Path $pyrevitRoot 'pyRevit_config.ini'
echo if (Test-Path $cfg^) {
echo     $content = Get-Content $cfg -Raw
echo     $content = $content -replace '\[Riyan\.extension\]\s*[\r\n]+disabled\s*=\s*true', "[Riyan.extension]`ndisabled = false"
echo     $content = $content -replace '\[Riyan-Revit-Tools\.extension\][\s\S]*?(?=(\[|$^)^)', ''
echo     $escaped = $targetTools.Replace('\', '\\'^)
echo     if ($content -notmatch [regex]::Escape($targetTools^)^) {
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
echo Write-Host 'Done!' -ForegroundColor Green
) > "%PS_SCRIPT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del /f /q "%PS_SCRIPT%" 2>nul

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS RESTORED & UPDATED!
echo ========================================================
echo.
echo All old files erased cleanly. Latest tools installed.
echo Please restart Revit, or click pyRevit Reload.
echo.
pause