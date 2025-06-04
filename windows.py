import os
import shutil
import subprocess
import sys

if sys.platform == "win32":
    import wmi


def try_native_or_wsl(cmd_native, cmd_wsl, check=True, env=None):
    try:
        subprocess.run(cmd_native, check=check, env=env)
    except FileNotFoundError:
        print(f"{cmd_native[0]} not found in Windows PATH. Trying WSL...")
        # Prepend export for env var if needed
        if env and "VIDEO_FORMAT" in env:
            cmd_wsl = f"export VIDEO_FORMAT=NTSC; {cmd_wsl}"
        subprocess.run(["wsl", "bash", "-c", cmd_wsl], check=check)


def run_for_windows(burn, iso, burn_drive, iso_output):
    """
    burn: Path to input video file (e.g., 'input_video.mp4')
    iso: Path to DVD XML file (e.g., 'dvd.xml')
    burn_drive: DVD device path (e.g., 'E:'), or None to skip burning
    iso_output: Path for the output ISO file (e.g., 'dvd_image.iso')
    """
    WORKDIR = "dvd_workdir"
    OUTPUT_MPG = os.path.join(WORKDIR, "output.mpg")

    # Step 1: Ensure workdir exists and is clean
    if os.path.exists(WORKDIR):
        shutil.rmtree(WORKDIR)
    os.makedirs(WORKDIR)

    # Step 2: Convert video to NTSC DVD MPEG-2
    print("Converting video to NTSC DVD MPEG-2...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        burn,
        "-target",
        "ntsc-dvd",
        "-b:v",
        "1800k",
        OUTPUT_MPG,
    ]
    ffmpeg_cmd_wsl = f"ffmpeg -i '{burn}' -target ntsc-dvd -b:v 1800k '{OUTPUT_MPG}'"
    try_native_or_wsl(ffmpeg_cmd, ffmpeg_cmd_wsl)

    # Step 3: Author DVD structure
    print("Authoring DVD structure...")
    dvd_xml_path = os.path.join(WORKDIR, "dvd.xml")
    shutil.copy2(iso, dvd_xml_path)
    dvdauthor_cmd = ["dvdauthor", "-o", WORKDIR, "-x", dvd_xml_path]
    dvdauthor_cmd_wsl = f"dvdauthor -o '{WORKDIR}' -x '{dvd_xml_path}'"
    env = os.environ.copy()
    env["VIDEO_FORMAT"] = "NTSC"
    try_native_or_wsl(dvdauthor_cmd, dvdauthor_cmd_wsl, env=env)

    # Step 4: Create ISO from DVD folder
    print("Creating ISO image...")
    genisoimage_cmd = ["genisoimage", "-o", iso_output, "-dvd-video", WORKDIR]
    genisoimage_cmd_wsl = f"genisoimage -o '{iso_output}' -dvd-video '{WORKDIR}'"
    try_native_or_wsl(genisoimage_cmd, genisoimage_cmd_wsl)

    # Step 5: Burn ISO to DVD if device is specified
    if burn_drive:
        print(f"Burning ISO to DVD device {burn_drive}...")
        growisofs_cmd = ["growisofs", "-dvd-compat", "-Z", f"{burn_drive}={iso_output}"]
        growisofs_cmd_wsl = f"growisofs -dvd-compat -Z '{burn_drive}={iso_output}'"
        try_native_or_wsl(growisofs_cmd, growisofs_cmd_wsl)
        print("DVD creation and burning complete.")
    else:
        print(f"No DVD device specified, skipping burn. DVD ISO is at {iso_output}.")


def get_optical_drives():
    """
    Returns a list of dictionaries with information about available optical drives.
    Each dictionary contains:
        - 'drive': the drive letter (e.g., 'E:')
        - 'media_loaded': True if a disc is present, False otherwise
        - 'name': device name/description
    """
    if sys.platform != "win32":
        # Not implemented on non-Windows systems
        return []
    drives = []
    c = wmi.WMI()
    for cdrom in c.Win32_CDROMDrive():
        drives.append(
            {
                "drive": cdrom.Drive,
                "media_loaded": cdrom.MediaLoaded,
                "name": cdrom.Name,
            }
        )
    return drives


if __name__ == "__main__":
    for drive in get_optical_drives():
        print(
            f"Drive: {drive['drive']}, Media Loaded: {drive['media_loaded']}, Name: {drive['name']}"
        )
