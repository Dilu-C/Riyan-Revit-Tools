<# :
@echo off
setlocal
title Riyan Revit Tools 1-Click Updater
color 0B

echo ========================================================
echo            RIYAN REVIT TOOLS - 1-CLICK UPDATER
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression ([System.IO.File]::ReadAllText('%~f0'))"

echo.
pause
goto :eof
#>

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

try {
    # 1. Check if Revit is running
    $revit = Get-Process Revit -ErrorAction SilentlyContinue
    if ($revit) {
        Write-Host " [!] Autodesk Revit is currently running." -ForegroundColor Yellow
        Write-Host "     Please save your work and close Revit to proceed with update..." -ForegroundColor Yellow
        Write-Host ""
        while (Get-Process Revit -ErrorAction SilentlyContinue) {
            Write-Host "     Waiting for Revit to close... (Close Revit to continue)" -ForegroundColor DarkYellow
            Start-Sleep -Seconds 3
        }
        Write-Host " [OK] Revit closed successfully!" -ForegroundColor Green
        Write-Host ""
    }

    $extDir = Join-Path $env:APPDATA 'pyRevit\Extensions'
    $pyrevitRoot = Join-Path $env:APPDATA 'pyRevit'
    $targetTools = Join-Path $extDir 'Riyan-Revit-Tools'

    Write-Host "[1/4] Clean-Slate Wipe: Clearing old duplicates & pyRevit cache..." -ForegroundColor Yellow

    # Delete all old legacy duplicate folders
    @('Riyan-Revit-Tools.extension', 'Riyan.extension', 'Riyan-Revit-Tools-main') | ForEach-Object {
        $target = Join-Path $extDir $_
        if (Test-Path $target) {
            Write-Host "  Removing duplicate: $_" -ForegroundColor DarkGray
            Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    if (Test-Path $extDir) {
        Get-ChildItem -Path $extDir -Directory -Filter '*Riyan*.extension*' -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  Removing duplicate: $($_.Name)" -ForegroundColor DarkGray
            Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        @('GEMINI.md', 'GEMINI', '.agents', 'test_compile.py', 'test_msg.py') | ForEach-Object {
            $stray = Join-Path $extDir $_
            if (Test-Path $stray) { Remove-Item -Path $stray -Force -ErrorAction SilentlyContinue }
        }
    }

    # Check Program Files and ProgramData for legacy Riyan extensions
    @("$env:ProgramFiles\pyRevit-Master\extensions\Riyan.extension",
      "$env:ProgramFiles\pyRevit-Master\extensions\Riyan.extension\Riyan.extension",
      "$env:ProgramData\pyRevit\Extensions\Riyan.extension",
      "$env:ProgramData\pyRevit\Extensions\Riyan-Revit-Tools") | ForEach-Object {
        if (Test-Path $_) {
            Write-Host "  Removing legacy system extension: $_" -ForegroundColor DarkGray
            Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    # Wipe pyRevit UI Cache and compiled binaries
    $cacheDir = Join-Path $pyrevitRoot 'Cache'
    if (Test-Path $cacheDir) {
        Write-Host "  Clearing pyRevit UI cache..." -ForegroundColor DarkGray
        Remove-Item -Path $cacheDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    Get-ChildItem -Path $pyrevitRoot -Include '__pycache__', '*.pyc' -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "[2/4] Downloading latest tools from GitHub..." -ForegroundColor Cyan
    $zipPath = Join-Path $env:TEMP 'RiyanTools.zip'
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }

    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    $wc.DownloadFile('https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip', $zipPath)

    if (!(Test-Path $zipPath) -or (Get-Item $zipPath).Length -lt 1000) {
        throw "Failed to download zip file from GitHub (file is missing or empty)."
    }

    Write-Host "[3/4] Extracting & installing latest tools..." -ForegroundColor Cyan
    $extractFolder = Join-Path $env:TEMP 'Riyan_Extract'
    if (Test-Path $extractFolder) { Remove-Item $extractFolder -Recurse -Force -ErrorAction SilentlyContinue }
    Expand-Archive -Path $zipPath -DestinationPath $extractFolder -Force
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    $sourceRoot = Join-Path $extractFolder 'Riyan-Revit-Tools-main'
    if (!(Test-Path $sourceRoot)) {
        throw "Extracted archive does not contain 'Riyan-Revit-Tools-main'."
    }

    if (!(Test-Path $targetTools)) {
        New-Item -ItemType Directory -Path $targetTools -Force | Out-Null
    }

    # Copy files
    Copy-Item -Path (Join-Path $sourceRoot '*') -Destination $targetTools -Recurse -Force
    Remove-Item -Path $extractFolder -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "[4/4] Ensuring clean pyRevit configuration..." -ForegroundColor Cyan
    $cfg = Join-Path $pyrevitRoot 'pyRevit_config.ini'
    if (Test-Path $cfg) {
        $content = Get-Content $cfg -Raw
        $content = $content -replace '\[Riyan\.extension\]\s*[\r\n]+disabled\s*=\s*true', "[Riyan.extension]`ndisabled = false"
        $content = $content -replace '\[Riyan-Revit-Tools\.extension\][\s\S]*?(?=(\[|$))', ''
        $escaped = $targetTools.Replace('\', '\\')
        if ($content -notmatch [regex]::Escape($targetTools)) {
            if ($content -match 'userextensions\s*=\s*\[(.*?)\]') {
                $existing = $matches[1].Trim()
                if ($existing) { $newVal = "userextensions = [$existing, `"$escaped`"]" } else { $newVal = "userextensions = [`"$escaped`"]" }
                $content = $content -replace 'userextensions\s*=\s*\[.*?\]', $newVal
            } else {
                $content = $content + "`nuserextensions = [`"$escaped`"]`n"
            }
        }
        Set-Content $cfg $content -NoNewline
    }

    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "   [SUCCESS] RIYAN REVIT TOOLS RESTORED & UPDATED!      " -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "All old files erased cleanly. Latest tools installed." -ForegroundColor Green
    Write-Host "You can now open Autodesk Revit or click pyRevit Reload."
}
catch {
    Write-Host ""
    Write-Host " [ERROR] An error occurred during update:" -ForegroundColor Red
    Write-Host " $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}