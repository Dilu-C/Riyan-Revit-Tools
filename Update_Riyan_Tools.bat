@echo off
title Riyan Revit Tools 1-Click Updater
color 0B

echo ========================================================
echo            RIYAN REVIT TOOLS - 1-CLICK UPDATER
echo ========================================================
echo.

echo [1/3] Downloading latest tools from GitHub...
set "PS_SCRIPT=%TEMP%\riyan_install.ps1"
if exist "%PS_SCRIPT%" del "%PS_SCRIPT%"

(
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo $extDir = Join-Path $env:APPDATA 'pyRevit\Extensions'
echo if (!(Test-Path $extDir^)^) { New-Item -ItemType Directory -Path $extDir -Force ^| Out-Null }
echo.
echo Write-Host 'Downloading repository package...' -ForegroundColor Cyan
echo $zipPath = Join-Path $env:TEMP 'RiyanTools.zip'
echo Invoke-WebRequest -Uri 'https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip' -OutFile $zipPath
echo.
echo Write-Host '[2/3] Extracting files...' -ForegroundColor Cyan
echo $extractFolder = Join-Path $env:TEMP 'Riyan_Extract'
echo if (Test-Path $extractFolder^) { Remove-Item $extractFolder -Recurse -Force -ErrorAction SilentlyContinue }
echo Expand-Archive -Path $zipPath -DestinationPath $extractFolder -Force
echo Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
echo.
echo $sourceRoot = Join-Path $extractFolder 'Riyan-Revit-Tools-main'
echo $targetTools = Join-Path $extDir 'Riyan-Revit-Tools'
echo $targetExt = Join-Path $extDir 'Riyan.extension'
echo.
echo Write-Host '[3/3] Installing and configuring extension...' -ForegroundColor Cyan
echo if (!(Test-Path $targetTools^)^) { New-Item -ItemType Directory -Path $targetTools -Force ^| Out-Null }
echo Copy-Item -Path (Join-Path $sourceRoot '*'^) -Destination $targetTools -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo # Mirror to Riyan.extension for native auto-discovery by pyRevit
echo $sourceExt = Join-Path $sourceRoot 'Riyan.extension'
echo if (Test-Path $sourceExt^) {
echo     if (!(Test-Path $targetExt^)^) { New-Item -ItemType Directory -Path $targetExt -Force ^| Out-Null }
echo     Copy-Item -Path (Join-Path $sourceExt '*'^) -Destination $targetExt -Recurse -Force -ErrorAction SilentlyContinue
echo }
echo.
echo Remove-Item $extractFolder -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo # Ensure pyRevit config has Riyan enabled and registered
echo $cfg = Join-Path $env:APPDATA 'pyRevit\pyRevit_config.ini'
echo if (Test-Path $cfg^) {
echo     $content = Get-Content $cfg -Raw
echo     $content = $content -replace '\[Riyan\.extension\]\s*[\r\n]+disabled\s*=\s*true', "[Riyan.extension]`ndisabled = false"
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
del "%PS_SCRIPT%" 2>nul

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS RESTORED & UPDATED!
echo ========================================================
echo.
echo Please restart Revit, or click pyRevit Reload.
echo.
pause

