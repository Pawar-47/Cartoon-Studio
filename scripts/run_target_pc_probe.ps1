[CmdletBinding()]
param(
    [string]$GodotExe = "",
    [string]$OutputDirectory = "",
    [switch]$RunMovie
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$projectDir = Join-Path $repoRoot "tools\godot_target_probe"

if (-not $OutputDirectory) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputDirectory = Join-Path $repoRoot "target_pc_probe_$stamp"
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

# Collect only hardware/OS facts needed for compatibility work.
# Deliberately exclude usernames, computer names, serial numbers, MAC/IP addresses and product keys.
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$system = Get-CimInstance Win32_ComputerSystem
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object {
    [ordered]@{
        name = $_.Name
        driver_version = $_.DriverVersion
        driver_date = $_.DriverDate
        video_processor = $_.VideoProcessor
        adapter_ram_bytes = $_.AdapterRAM
        current_width = $_.CurrentHorizontalResolution
        current_height = $_.CurrentVerticalResolution
        current_refresh_hz = $_.CurrentRefreshRate
    }
})

$intelDrivers = @()
$driverQueryError = $null
try {
    $intelDrivers = @(Get-CimInstance Win32_PnPSignedDriver | Where-Object {
        $_.DeviceName -match "Intel.*(HD )?Graphics.*5500|Intel.*5500"
    } | ForEach-Object {
        [ordered]@{
            device = $_.DeviceName
            version = $_.DriverVersion
            date = $_.DriverDate
            provider = $_.DriverProviderName
            inf = $_.InfName
        }
    })
}
catch {
    $driverQueryError = $_.Exception.Message
    Write-Warning "Could not query signed driver details: $driverQueryError"
}

$memoryModules = @(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
    [ordered]@{
        capacity_bytes = $_.Capacity
        speed_mhz = $_.Speed
        configured_speed_mhz = $_.ConfiguredClockSpeed
    }
})
$disks = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [ordered]@{
        drive = $_.DeviceID
        size_bytes = $_.Size
        free_bytes = $_.FreeSpace
    }
})
$release = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion"

$profile = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    powershell_version = $PSVersionTable.PSVersion.ToString()
    os = [ordered]@{
        caption = $os.Caption
        version = $os.Version
        build = $os.BuildNumber
        architecture = $os.OSArchitecture
        display_version = $release.DisplayVersion
    }
    system = [ordered]@{
        manufacturer = $system.Manufacturer
        model = $system.Model
        system_type = $system.SystemType
        total_ram_bytes = $system.TotalPhysicalMemory
    }
    cpu = @($cpu | ForEach-Object {
        [ordered]@{
            name = $_.Name
            cores = $_.NumberOfCores
            logical_processors = $_.NumberOfLogicalProcessors
            max_clock_mhz = $_.MaxClockSpeed
        }
    })
    gpus = $gpus
    intel_graphics_driver_matches = $intelDrivers
    intel_driver_query_error = $driverQueryError
    memory_modules = $memoryModules
    fixed_disks = $disks
    privacy_note = "No username, computer name, serial number, MAC/IP address or product key is collected."
}

$profilePath = Join-Path $OutputDirectory "system_profile.json"
$profile | ConvertTo-Json -Depth 7 | Set-Content -Path $profilePath -Encoding UTF8
Write-Host "Hardware profile saved: $profilePath"

if (-not $GodotExe) {
    $godotCommand = Get-Command "godot.exe" -ErrorAction SilentlyContinue
    if ($godotCommand) { $GodotExe = $godotCommand.Source }
}
if (-not $GodotExe) {
    Write-Warning "Godot was not supplied/found. Hardware-only collection is complete. Re-run with -GodotExe to run the graphics probe."
    exit 0
}
if (-not (Test-Path -LiteralPath $GodotExe -PathType Leaf)) {
    throw "Godot executable not found: $GodotExe"
}
if (-not (Test-Path -LiteralPath $projectDir -PathType Container)) {
    throw "Probe project directory is missing: $projectDir"
}

$godotVersion = (& $GodotExe --version 2>&1 | Out-String).Trim()
Write-Host "Godot version: $godotVersion"
if ($godotVersion -notmatch "^4\.7\.2") {
    Write-Warning "This probe is designed for Godot 4.7.2 stable. The supplied version differs; results may not be comparable."
}

function Invoke-GodotProbe {
    param(
        [string[]]$Arguments,
        [string]$LogPath
    )
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    & $GodotExe @Arguments *> $LogPath
    $exitCode = $LASTEXITCODE
    $watch.Stop()
    return [ordered]@{
        exit_code = $exitCode
        elapsed_seconds = [Math]::Round($watch.Elapsed.TotalSeconds, 3)
        log = $LogPath
    }
}

$interactiveReport = Join-Path $OutputDirectory "godot_interactive_report.json"
$interactiveLog = Join-Path $OutputDirectory "godot_interactive.log"
$interactiveArgs = @(
    "--path", $projectDir,
    "--", "--mode=interactive", "--report=$interactiveReport"
)
Write-Host "Running 12-second interactive Compatibility renderer test..."
$interactiveResult = Invoke-GodotProbe -Arguments $interactiveArgs -LogPath $interactiveLog

$movieResult = $null
$moviePath = Join-Path $OutputDirectory "godot_probe_720p_24fps.avi"
$movieReport = Join-Path $OutputDirectory "godot_movie_report.json"
if ($RunMovie) {
    $movieLog = Join-Path $OutputDirectory "godot_movie.log"
    $movieArgs = @(
        "--path", $projectDir,
        "--write-movie", $moviePath,
        "--fixed-fps", "24",
        "--quit-after", "260",
        "--", "--mode=movie", "--report=$movieReport"
    )
    Write-Host "Rendering a 10-second 720p / 24 FPS AVI test. This may take several minutes on low-end hardware..."
    $movieResult = Invoke-GodotProbe -Arguments $movieArgs -LogPath $movieLog
    $movieBytes = 0
    if (Test-Path -LiteralPath $moviePath) {
        $movieBytes = (Get-Item -LiteralPath $moviePath).Length
    }
    $movieResult["output_file"] = $moviePath
    $movieResult["output_bytes"] = $movieBytes
}

$summary = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    godot_executable = (Resolve-Path -LiteralPath $GodotExe).Path
    godot_version = $godotVersion
    interactive = $interactiveResult
    movie = $movieResult
    files = [ordered]@{
        system_profile = $profilePath
        interactive_report = $interactiveReport
        interactive_log = $interactiveLog
        movie_report = $(if ($RunMovie) { $movieReport } else { $null })
        movie_file = $(if ($RunMovie) { $moviePath } else { $null })
    }
}
$summaryPath = Join-Path $OutputDirectory "run_summary.json"
$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryPath -Encoding UTF8
Write-Host ""
Write-Host "Probe finished. Output folder: $OutputDirectory"
Write-Host "Please share system_profile.json, godot_interactive_report.json and run_summary.json."
if ($RunMovie) { Write-Host "Also share godot_movie_report.json and godot_probe_720p_24fps.avi if the AVI was created." }
Write-Host "The report intentionally excludes personal identifiers."
