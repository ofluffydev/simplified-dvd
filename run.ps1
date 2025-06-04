param(
    [Parameter(Mandatory=$true)][string]$InputVideo,
    [Parameter(Mandatory=$true)][string]$DvdXml,
    [string]$DvdDevice
)

$WorkDir = "dvd_workdir"
$IsoFile = "dvd_image.iso"
$OutputMpg = Join-Path $WorkDir "output.mpg"

function Ensure-Directory {
    param ($Path)
    if (Test-Path $Path) { Remove-Item $Path -Recurse -Force }
    New-Item -Path $Path -ItemType Directory | Out-Null
}

function Command-Exists {
    param ($Cmd)
    $null -ne (Get-Command $Cmd -ErrorAction SilentlyContinue)
}

function Wsl-Command {
    param ($Cmd)
    wsl bash -c "$Cmd"
}

# Step 0: Check arguments
if (-not $InputVideo -or -not $DvdXml) {
    Write-Host "Usage: .\create-and-burn-dvd.ps1 <input_video.mp4> <dvd.xml> [dvd_drive]"
    exit 1
}

# Step 1: Prepare workdir
Ensure-Directory $WorkDir

# Step 2: Convert video to NTSC DVD MPEG-2
Write-Host "Converting video to NTSC DVD MPEG-2..."
if (Command-Exists "ffmpeg") {
    ffmpeg -i $InputVideo -target ntsc-dvd -b:v 1800k $OutputMpg
} else {
    Write-Host "ffmpeg not found in Windows PATH. Trying WSL..."
    Wsl-Command "ffmpeg -i '$InputVideo' -target ntsc-dvd -b:v 1800k '$OutputMpg'"
}

# Step 3: Author DVD structure
Write-Host "Authoring DVD structure..."
Copy-Item $DvdXml (Join-Path $WorkDir "dvd.xml")
Push-Location $WorkDir

# Ensure VIDEO_FORMAT is set for dvdauthor
$env:VIDEO_FORMAT = "NTSC"

if (Command-Exists "dvdauthor") {
    dvdauthor -o . -x "dvd.xml"
} else {
    Write-Host "dvdauthor not found in Windows PATH. Trying WSL..."
    # WSL expects Linux paths, so convert as needed
    $wslWorkDir = Wsl-Command "wslpath -a '$PWD'"
    Wsl-Command "export VIDEO_FORMAT=NTSC; cd '$wslWorkDir' && dvdauthor -o . -x dvd.xml"
}
Pop-Location

# Step 4: Create ISO image
Write-Host "Creating ISO image..."
if (Command-Exists "genisoimage") {
    genisoimage -o $IsoFile -dvd-video $WorkDir
} else {
    Write-Host "genisoimage not found in Windows PATH. Trying WSL..."
    $wslWorkDir = Wsl-Command "wslpath -a '$PWD\$WorkDir'"
    $wslIsoFile = Wsl-Command "wslpath -a '$PWD\$IsoFile'"
    Wsl-Command "genisoimage -o '$wslIsoFile' -dvd-video '$wslWorkDir'"
}

# Step 5: (Optional) Preview with VLC
if ($args.Count -ge 3 -and $args[2] -eq "--preview") {
    Write-Host "Previewing output with VLC..."
    if (Command-Exists "vlc") {
        vlc $OutputMpg
    } else {
        Write-Host "VLC not found in Windows PATH. Please install VLC to preview."
    }
}

# Step 6: Burn ISO to DVD
if ($DvdDevice) {
    Write-Host "Burning ISO to DVD device $DvdDevice..."
    if (Command-Exists "growisofs") {
        growisofs -dvd-compat -Z "$DvdDevice=$IsoFile"
    } else {
        Write-Host "growisofs not found in Windows PATH. Trying WSL..."
        $wslIsoFile = Wsl-Command "wslpath -a '$PWD\$IsoFile'"
        Wsl-Command "growisofs -dvd-compat -Z '$DvdDevice=$wslIsoFile'"
    }
    Write-Host "DVD creation and burning complete."
} else {
    Write-Host "No DVD device specified, skipping burn. DVD ISO is at $IsoFile."
}
