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
set "PS_SCRIPT=%TEMP%\riyan_install.ps1"
if exist "%PS_SCRIPT%" del "%PS_SCRIPT%"

echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 >> "%PS_SCRIPT%"
echo $zipPath = Join-Path $env:TEMP 'RiyanTools.zip' >> "%PS_SCRIPT%"
echo $extDir = Join-Path $env:APPDATA 'pyRevit\Extensions' >> "%PS_SCRIPT%"
echo if (!(Test-Path $extDir^)^) { New-Item -ItemType Directory -Path $extDir -Force ^| Out-Null } >> "%PS_SCRIPT%"
echo Write-Host 'Downloading repository package...' >> "%PS_SCRIPT%"
echo Invoke-WebRequest -Uri 'https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip' -OutFile $zipPath >> "%PS_SCRIPT%"
echo Write-Host 'Extracting files...' >> "%PS_SCRIPT%"
echo Expand-Archive -Path $zipPath -DestinationPath $extDir -Force >> "%PS_SCRIPT%"
echo Remove-Item $zipPath -Force >> "%PS_SCRIPT%"
echo $extracted = Join-Path $extDir 'Riyan-Revit-Tools-main' >> "%PS_SCRIPT%"
echo $final = Join-Path $extDir 'Riyan-Revit-Tools' >> "%PS_SCRIPT%"
echo if (Test-Path $extracted^) { >> "%PS_SCRIPT%"
echo     if (Test-Path $final^) { Remove-Item $final -Recurse -Force } >> "%PS_SCRIPT%"
echo     Rename-Item -Path $extracted -NewName 'Riyan-Revit-Tools' >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"
echo Write-Host '[3/3] Configuring pyRevit extension...' >> "%PS_SCRIPT%"
echo $cfg = Join-Path $env:APPDATA 'pyRevit\pyRevit_config.ini' >> "%PS_SCRIPT%"
echo $target = Join-Path $env:APPDATA 'pyRevit\Extensions\Riyan-Revit-Tools' >> "%PS_SCRIPT%"
echo if (Test-Path $cfg^) { >> "%PS_SCRIPT%"
echo     $content = Get-Content $cfg -Raw >> "%PS_SCRIPT%"
echo     if ($content -notmatch [regex]::Escape($target^)^) { >> "%PS_SCRIPT%"
echo         $escaped = $target.Replace('\', '\\'^) >> "%PS_SCRIPT%"
echo         if ($content -match 'userextensions\s*=\s*\[(.*?)\]'^) { >> "%PS_SCRIPT%"
echo             $existing = $matches[1].Trim(^) >> "%PS_SCRIPT%"
echo             if ($existing^) { $newVal = "userextensions = [$existing, `"$escaped`"]" } else { $newVal = "userextensions = [`"$escaped`"]" } >> "%PS_SCRIPT%"
echo             $content = $content -replace 'userextensions\s*=\s*\[.*?\]', $newVal >> "%PS_SCRIPT%"
echo         } else { >> "%PS_SCRIPT%"
echo             $content = $content + "`nuserextensions = [`"$escaped`"]`n" >> "%PS_SCRIPT%"
echo         } >> "%PS_SCRIPT%"
echo         Set-Content $cfg $content >> "%PS_SCRIPT%"
echo     } >> "%PS_SCRIPT%"
echo } >> "%PS_SCRIPT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%"

echo.
echo ========================================================
echo   [SUCCESS] RIYAN REVIT TOOLS INSTALLED SUCCESSFULLY!
echo ========================================================
echo.
echo Please restart Revit, or click pyRevit Reload.
echo.
pause
