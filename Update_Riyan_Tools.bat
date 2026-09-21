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

    Write-Host "[1/5] Clean-Slate Wipe: Clearing old duplicates & pyRevit cache..." -ForegroundColor Yellow

    # Delete all old legacy duplicate folders (both singular Extension and plural Extensions)
    $singularExtDir = Join-Path $pyrevitRoot 'Extension'
    if (Test-Path $singularExtDir) {
        Write-Host "  Removing ancient legacy singular Extension folder: $singularExtDir" -ForegroundColor DarkGray
        Remove-Item -Path $singularExtDir -Recurse -Force -ErrorAction SilentlyContinue
    }

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

    # Wipe pyRevit UI Cache and compiled binaries across all Revit versions (2020-2027+)
    $cacheDir = Join-Path $pyrevitRoot 'Cache'
    if (Test-Path $cacheDir) {
        Write-Host "  Clearing pyRevit UI cache..." -ForegroundColor DarkGray
        Remove-Item -Path $cacheDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    Get-ChildItem -Path $pyrevitRoot -Directory -Filter '20*' -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  Clearing Revit cache: $($_.Name)..." -ForegroundColor DarkGray
        Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    Get-ChildItem -Path $pyrevitRoot -Include '__pycache__', '*.pyc' -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "[2/5] Downloading latest tools from GitHub..." -ForegroundColor Cyan
    $zipPath = Join-Path $env:TEMP 'RiyanTools.zip'
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }

    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    $wc.DownloadFile('https://github.com/Dilu-C/Riyan-Revit-Tools/archive/refs/heads/main.zip', $zipPath)

    if (!(Test-Path $zipPath) -or (Get-Item $zipPath).Length -lt 1000) {
        throw "Failed to download zip file from GitHub (file is missing or empty)."
    }

    Write-Host "[3/5] Extracting & installing latest tools..." -ForegroundColor Cyan
    $extractFolder = Join-Path $env:TEMP 'Riyan_Extract'
    if (Test-Path $extractFolder) { Remove-Item $extractFolder -Recurse -Force -ErrorAction SilentlyContinue }
    Expand-Archive -Path $zipPath -DestinationPath $extractFolder -Force
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    $sourceRoot = Join-Path $extractFolder 'Riyan-Revit-Tools-main'
    if (!(Test-Path $sourceRoot)) {
        throw "Extracted archive does not contain 'Riyan-Revit-Tools-main'."
    }

    # Atomic Clean-Slate Installation: Wipe old extension to eliminate ghost panels and orphaned buttons
    $targetExt = Join-Path $targetTools 'Riyan.extension'
    if (Test-Path $targetExt) {
        Write-Host "  Performing clean-slate purge of previous extension..." -ForegroundColor DarkGray
        Remove-Item -Path $targetExt -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (!(Test-Path $targetTools)) {
        New-Item -ItemType Directory -Path $targetTools -Force | Out-Null
    }

    # Copy fresh files from source
    Copy-Item -Path (Join-Path $sourceRoot '*') -Destination $targetTools -Recurse -Force
    Remove-Item -Path $extractFolder -Recurse -Force -ErrorAction SilentlyContinue

    # Purge leftover md, zip, txt, .idea, and deprecated Tool.panel & About.panel from target
    Get-ChildItem -Path $targetTools -Recurse -Include '*.md', '*.zip' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    # Strip UTF-8 BOM from all bundle.yaml files
    Get-ChildItem -Path $targetTools -Recurse -Filter '*.yaml' -ErrorAction SilentlyContinue | ForEach-Object {
        $b = [System.IO.File]::ReadAllBytes($_.FullName)
        if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) {
            [System.IO.File]::WriteAllBytes($_.FullName, $b[3..($b.Length - 1)])
        }
    }
    @('extension.json.txt', '.idea', '.gitattributes', '.gitignore', 'Other', '__pycache__') | ForEach-Object {
        $p = Join-Path (Join-Path $targetTools 'Riyan.extension') $_
        if (Test-Path $p) { Remove-Item -Path $p -Recurse -Force -ErrorAction SilentlyContinue }
    }
    @('Tool.panel', 'About.panel') | ForEach-Object {
        $legacyPanel = Join-Path $targetTools "Riyan.extension\Riyan.tab\$_"
        if (Test-Path $legacyPanel) { Remove-Item -Path $legacyPanel -Recurse -Force -ErrorAction SilentlyContinue }
    }
    @("Riyan.extension\Riyan.tab\System.panel\Update.pulldown\SyncSharedParameters.pushbutton",
      "Riyan.extension\Riyan.tab\Coordination.panel\ChangeLevel.pushbutton",
      "Riyan.extension\Riyan.tab\Coordination.panel\Change Level.pushbutton",
      "Riyan.extension\Riyan.tab\Coordination.panel\link.pushbutton") | ForEach-Object {
        $legacyItem = Join-Path $targetTools $_
        if (Test-Path $legacyItem) { Remove-Item -Path $legacyItem -Recurse -Force -ErrorAction SilentlyContinue }
    }

    Write-Host "[4/5] Ensuring clean pyRevit configuration..." -ForegroundColor Cyan
    $cfg = Join-Path $pyrevitRoot 'pyRevit_config.ini'
    if (Test-Path $cfg) {
        $content = Get-Content $cfg -Raw
        # Remove broken/non-existent RGLK-Drive references
        $content = [regex]::Replace($content, '["''][^"'']*RGLK-Drive[^"'']*["'']\s*,?', '')
        $content = $content -replace '\[Riyan\.extension\]\s*[\r\n]+disabled\s*=\s*true', "[Riyan.extension]`ndisabled = false"
        $content = $content -replace '\[Riyan-Revit-Tools\.extension\][\s\S]*?(?=(\[|$))', ''
        
        # Clean userextensions to avoid duplicate loading
        $escaped = $targetTools.Replace('\', '\\')
        if ($content -match 'userextensions\s*=\s*\[(.*?)\]') {
            $existingItems = $matches[1].Split(',') | ForEach-Object { $_.Trim().Trim('"').Trim('''') } | Where-Object { 
                $_ -and (Test-Path $_) -and ($_ -notmatch 'RGLK-Drive') -and ($_ -notmatch '(?i)pyRevit[\\/]Extension([\\/]|$)')
            }
            # Add targetTools if not already present
            if ($existingItems -notcontains $targetTools -and $existingItems -notcontains $escaped) {
                $existingItems += $targetTools
            }
            # Remove raw Extensions root if targetTools is also present to prevent dual-loading of Riyan
            $uniqueExts = $existingItems | Select-Object -Unique | ForEach-Object { '\"' + $_.Replace('\', '\\') + '\"' }
            $newVal = "userextensions = [" + ($uniqueExts -join ', ') + "]"
            $content = $content -replace 'userextensions\s*=\s*\[.*?\]', $newVal
        } else {
            $content = $content + "`nuserextensions = [`"$escaped`"]`n"
        }
        $content = $content -replace ',\s*\]', ']' -replace '\[\s*,', '['
        Set-Content $cfg $content -NoNewline
    }

    Write-Host "[5/5] Enforcing Riyan Shared Parameters across all Revit versions..." -ForegroundColor Cyan
    $targetParamPath = $null
    $cacheSpDir = Join-Path $targetTools 'Library_Cache\SharedParameters'

    # Check SharePoint paths first if available
    $spCandidates = @(
        (Join-Path $env:USERPROFILE 'OneDrive - Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER'),
        (Join-Path $env:USERPROFILE 'Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER'),
        'D:\RIYAN\Riyan Private Limited\Riyan LK Projects - 00 - RIYAN REVIT STANDARD\01 SHARED PARAMETER'
    )

    $foundFiles = New-Object System.Collections.Generic.List[PSObject]

    foreach ($sp in $spCandidates) {
        if (Test-Path $sp) {
            Get-ChildItem -Path $sp -Filter 'RYN_SharedParameters*.txt' -File -ErrorAction SilentlyContinue | Where-Object { 
                $_.FullName -notmatch '(?i)(previous|old|backup|archive)' 
            } | ForEach-Object {
                $ver = 0
                if ($_.Name -match '\d+') { $ver = [int64]$matches[0] }
                $foundFiles.Add([PSCustomObject]@{ Path = $_.FullName; Version = $ver; IsCloud = $true })
            }
        }
    }

    if (Test-Path $cacheSpDir) {
        Get-ChildItem -Path $cacheSpDir -Filter 'RYN_SharedParameters*.txt' -File -ErrorAction SilentlyContinue | ForEach-Object {
            $ver = 0
            if ($_.Name -match '\d+') { $ver = [int64]$matches[0] }
            $foundFiles.Add([PSCustomObject]@{ Path = $_.FullName; Version = $ver; IsCloud = $false })
        }
    }

    if ($foundFiles.Count -gt 0) {
        $best = $foundFiles | Sort-Object -Property @{Expression={$_.Version}; Descending=$true}, @{Expression={$_.IsCloud}; Descending=$true} | Select-Object -First 1
        $targetParamPath = $best.Path

        # If best came from SharePoint, sync to local cache so offline always works
        if ($best.IsCloud -and (Test-Path $cacheSpDir)) {
            $localDest = Join-Path $cacheSpDir (Split-Path $best.Path -Leaf)
            try {
                Copy-Item -Path $best.Path -Destination $localDest -Force -ErrorAction SilentlyContinue
                $targetParamPath = $localDest
            } catch {}
        }
    }

    if (-not $targetParamPath -or -not (Test-Path $targetParamPath)) {
        $targetParamPath = Join-Path $cacheSpDir 'RYN_SharedParameters_V-RS20260918.txt'
    }
    if (-not $targetParamPath -or -not (Test-Path $targetParamPath)) {
        $targetParamPath = Join-Path (Join-Path $targetTools 'Riyan.extension\lib') 'RYN_SharedParameters_V-RS20260918.txt'
    }

    if (Test-Path $targetParamPath) {
        Write-Host "  Active Shared Parameter File: $(Split-Path $targetParamPath -Leaf)" -ForegroundColor DarkGray

        # Permissions: Read-Only for standard users, Read/Write for Dilupa
        $currentUser = $env:USERNAME.ToLower()
        $adminUsers = @('user', 'windows', 'dilupa', 'dilupa.chathuranga', 'dilupac', 'dilupa1990')
        try {
            if ($adminUsers -contains $currentUser) {
                Set-ItemProperty -Path $targetParamPath -Name IsReadOnly -Value $false -ErrorAction SilentlyContinue
                Write-Host "  Permission: Full Edit (Admin Mode)" -ForegroundColor DarkGray
            } else {
                Set-ItemProperty -Path $targetParamPath -Name IsReadOnly -Value $true -ErrorAction SilentlyContinue
                Write-Host "  Permission: Locked Read-Only (Standard User Mode)" -ForegroundColor DarkGray
            }
        } catch {}

        # Iterate all Revit.ini files across all Revit versions (2021-2027+)
        $revitRoot = Join-Path $env:APPDATA 'Autodesk\Revit'
        if (Test-Path $revitRoot) {
            $revitInis = Get-ChildItem -Path $revitRoot -Filter 'Revit.ini' -Recurse -ErrorAction SilentlyContinue | Where-Object { 
                $_.FullName -notmatch '(?i)backup' 
            }

            foreach ($iniItem in $revitInis) {
                try {
                    $iniPath = $iniItem.FullName
                    $rawBytes = [System.IO.File]::ReadAllBytes($iniPath)
                    $encoding = [System.Text.Encoding]::Unicode
                    if ($rawBytes.Length -ge 3 -and $rawBytes[0] -eq 0xEF -and $rawBytes[1] -eq 0xBB -and $rawBytes[2] -eq 0xBF) {
                        $encoding = [System.Text.Encoding]::UTF8
                    } elseif ($rawBytes.Length -ge 2 -and $rawBytes[0] -eq 0xFF -and $rawBytes[1] -eq 0xFE) {
                        $encoding = [System.Text.Encoding]::Unicode
                    }

                    $lines = [System.IO.File]::ReadAllLines($iniPath, $encoding)
                    $newLines = New-Object System.Collections.Generic.List[string]
                    $inDirectories = $false
                    $hasDirectories = $false
                    $sharedWritten = $false
                    $externalWritten = $false

                    foreach ($line in $lines) {
                        $trim = $line.Trim()
                        if ($trim -eq '[Directories]') {
                            $inDirectories = $true
                            $hasDirectories = $true
                            $newLines.Add($line)
                            continue
                        }
                        if ($inDirectories -and $trim.StartsWith('[') -and $trim.EndsWith(']')) {
                            if (-not $sharedWritten) {
                                $newLines.Add("SharedParameters=$targetParamPath")
                                $sharedWritten = $true
                            }
                            if (-not $externalWritten) {
                                $newLines.Add("ExternalParameters=$targetParamPath")
                                $externalWritten = $true
                            }
                            $inDirectories = $false
                        }

                        if ($inDirectories -and $trim -match '^SharedParameters\s*=') {
                            $newLines.Add("SharedParameters=$targetParamPath")
                            $sharedWritten = $true
                        } elseif ($inDirectories -and $trim -match '^ExternalParameters\s*=') {
                            $newLines.Add("ExternalParameters=$targetParamPath")
                            $externalWritten = $true
                        } else {
                            $newLines.Add($line)
                        }
                    }

                    if ($inDirectories) {
                        if (-not $sharedWritten) {
                            $newLines.Add("SharedParameters=$targetParamPath")
                            $sharedWritten = $true
                        }
                        if (-not $externalWritten) {
                            $newLines.Add("ExternalParameters=$targetParamPath")
                            $externalWritten = $true
                        }
                    }

                    if (-not $hasDirectories) {
                        $newLines.Add("")
                        $newLines.Add("[Directories]")
                        $newLines.Add("SharedParameters=$targetParamPath")
                        $newLines.Add("ExternalParameters=$targetParamPath")
                    }

                    [System.IO.File]::WriteAllLines($iniPath, $newLines.ToArray(), $encoding)
                    $relParent = Split-Path (Split-Path $iniPath -Parent) -Leaf
                    Write-Host "  [OK] $relParent linked to Riyan Shared Parameters!" -ForegroundColor Green
                } catch {
                    Write-Host "  [!] Could not update $($iniItem.FullName): $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
        }
    } else {
        Write-Host "  [!] Warning: Shared Parameter file could not be found." -ForegroundColor Yellow
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