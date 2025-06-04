import os
import shutil
import subprocess
import sys

from loguru import logger

if sys.platform == "win32":
    import wmi


def try_native_or_wsl(cmd_native, cmd_wsl, check=True, env=None, allow_wsl=True, wsl_shared_dir=None):
    if cmd_native is not None:
        try:
            subprocess.run(cmd_native, check=check, env=env)
            return
        except FileNotFoundError:
            if not allow_wsl:
                raise RuntimeError(f"{cmd_native[0]} not found in Windows PATH and WSL fallback is disabled.")
            print(f"WARNING: {cmd_native[0]} not found in Windows PATH. Attempting to use WSL. Make sure your files are accessible from WSL.")
            if wsl_shared_dir:
                print(f"NOTE: Using shared folder for WSL: {wsl_shared_dir}")
    # Prepend export for env var if needed
    if env and "VIDEO_FORMAT" in env:
        cmd_wsl = f"export VIDEO_FORMAT=NTSC; {cmd_wsl}"
    subprocess.run(["wsl", "bash", "-c", cmd_wsl], check=check)


def run_for_windows(burn, iso, burn_drive, iso_output, file_path, skip_burn=False):
    """
    burn: Boolean, whether to burn to DVD device
    iso: Path to DVD XML file (e.g., 'dvd.xml')
    burn_drive: DVD device path (e.g., 'E:'), or None to skip burning
    iso_output: Path for the output ISO file (e.g., 'dvd_image.iso')
    file_path: Path to input video file (e.g., 'input_video.mp4')
    skip_burn: If True, do not run isoburn.exe, just return info for burning
    """
    WORKDIR = "dvd_workdir"
    OUTPUT_MPG = os.path.join(WORKDIR, "output.mpg")
    WSL_SHARED_DIR = os.path.abspath(WORKDIR).replace("\\", "/")

    # Convert Windows path to WSL path
    def to_wsl_path(path):
        abs_path = os.path.abspath(path)
        drive, rest = abs_path[0], abs_path[2:].replace('\\', '/')
        return f"/mnt/{drive.lower()}{rest}"

    WSL_WORKDIR = to_wsl_path(WORKDIR)
    WSL_OUTPUT_MPG = to_wsl_path(OUTPUT_MPG)
    WSL_DVD_XML = to_wsl_path(os.path.join(WORKDIR, "dvd.xml"))
    WSL_ISO_OUTPUT = to_wsl_path(iso_output) if iso_output else None

    # Step 1: Ensure workdir exists and is clean
    if os.path.exists(WORKDIR):
        shutil.rmtree(WORKDIR)
    os.makedirs(WORKDIR)

    # Step 2: Convert video to NTSC DVD MPEG-2
    print("Converting video to NTSC DVD MPEG-2...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        file_path,
        "-target",
        "ntsc-dvd",
        "-b:v",
        "1800k",
        OUTPUT_MPG,
    ]
    ffmpeg_cmd_wsl = f"ffmpeg -i '{to_wsl_path(file_path)}' -target ntsc-dvd -b:v 1800k '{WSL_OUTPUT_MPG}'"
    try_native_or_wsl(ffmpeg_cmd, ffmpeg_cmd_wsl, wsl_shared_dir=WSL_SHARED_DIR)

    # Step 3: Author DVD structure
    print("Authoring DVD structure...")
    dvd_xml_path = os.path.join(WORKDIR, "dvd.xml")
    create_dvd_xml(dvd_xml_path, video_filename="output.mpg")
    # Create DVD output subfolder
    DVD_FOLDER = os.path.join(WORKDIR, "DVD")
    os.makedirs(DVD_FOLDER, exist_ok=True)
    WSL_DVD_FOLDER = to_wsl_path(DVD_FOLDER)
    # Always use WSL for dvdauthor and convert paths
    if not os.path.exists(dvd_xml_path):
        print(f"ERROR: DVD XML file not found at {dvd_xml_path} (Windows path)")
    else:
        print(f"WSL XML file will be used: {WSL_DVD_XML}")
    dvdauthor_cmd_wsl = f"dvdauthor -o '{WSL_DVD_FOLDER}' -x '{WSL_DVD_XML}'"
    env = os.environ.copy()
    env["VIDEO_FORMAT"] = "NTSC"
    # Only run the WSL command for dvdauthor
    try_native_or_wsl(None, dvdauthor_cmd_wsl, env=env, wsl_shared_dir=WSL_SHARED_DIR)

    # Step 4: Create ISO from DVD folder
    print("Creating ISO image...")
    if not iso_output:
        iso_output = "dvd.iso"
        print(f"No ISO output path specified. Defaulting to {iso_output}")
    WSL_ISO_OUTPUT = to_wsl_path(iso_output)
    genisoimage_cmd = ["genisoimage", "-o", iso_output, "-dvd-video", DVD_FOLDER]
    genisoimage_cmd_wsl = f"genisoimage -o '{WSL_ISO_OUTPUT}' -dvd-video '{WSL_DVD_FOLDER}'"
    try_native_or_wsl(genisoimage_cmd, genisoimage_cmd_wsl, wsl_shared_dir=WSL_SHARED_DIR)

    # Step 5: Burn ISO to DVD if device is specified
    if skip_burn:
        # Return info needed for burning
        result = {
            "iso_output": os.path.abspath(iso_output),
            "burn_drive": burn_drive,
        }
        # Cleanup workdir after all processing is done
        if os.path.exists(WORKDIR):
            try:
                shutil.rmtree(WORKDIR)
            except Exception as e:
                print(f"Warning: Could not delete workdir {WORKDIR}: {e}")
        return result
    if burn_drive:
        print(f"Burning ISO to DVD device {burn_drive} using isoburn.exe...")
        # Use isoburn.exe directly, do not fallback to WSL
        isoburn_cmd = ["isoburn.exe", "/q", burn_drive, os.path.abspath(iso_output)]
        try:
            subprocess.run(isoburn_cmd, check=True)
            print("DVD creation and burning complete.")
        except Exception as e:
            print(f"Error running isoburn.exe: {e}")
    else:
        print(f"No DVD device specified, skipping burn. DVD ISO is at {iso_output}.")
    # Cleanup workdir after all processing is done
    if os.path.exists(WORKDIR):
        try:
            shutil.rmtree(WORKDIR)
        except Exception as e:
            print(f"Warning: Could not delete workdir {WORKDIR}: {e}")


def run_isoburn_step(iso_output, burn_drive):
    """Run the isoburn.exe step only."""
    isoburn_cmd = ["isoburn.exe", "/q", burn_drive, os.path.abspath(iso_output)]
    try:
        subprocess.run(isoburn_cmd, check=True)
        print("DVD creation and burning complete.")
    except Exception as e:
        print(f"Error running isoburn.exe: {e}")
    # Cleanup workdir after burning
    workdir = "dvd_workdir"
    if os.path.exists(workdir):
        try:
            shutil.rmtree(workdir)
        except Exception as e:
            print(f"Warning: Could not delete workdir {workdir}: {e}")


def create_dvd_xml(xml_path, video_filename="output.mpg"):
    # Use WSL path for the MPEG file
    def to_wsl_path(path):
        abs_path = os.path.abspath(path)
        drive, rest = abs_path[0], abs_path[2:].replace('\\', '/')
        return f"/mnt/{drive.lower()}{rest}"
    abs_video_path = os.path.abspath(os.path.join(os.path.dirname(xml_path), video_filename))
    wsl_video_path = to_wsl_path(abs_video_path)
    dvd_xml_content = f'''
<dvdauthor>
  <vmgm />
  <titleset>
    <titles>
      <pgc>
        <vob file="{wsl_video_path}" />
      </pgc>
    </titles>
  </titleset>
</dvdauthor>
'''
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(dvd_xml_content)
    print(f"Created DVD XML at {xml_path} with WSL MPEG path {wsl_video_path}")


def get_optical_drives():
    """
    Returns a list of dictionaries with information about available optical drives.
    Each dictionary contains:
        - 'drive': the drive letter (e.g., 'E:')
        - 'media_loaded': True if a disc is present, False otherwise
        - 'name': device name/description
    """
    if sys.platform != "win32":
        logger.debug("Not running on Windows, returning empty drive list.")
        return []
    drives = []
    try:
        import wmi
        logger.debug("Imported wmi successfully.")
        c = wmi.WMI()
        for cdrom in c.Win32_CDROMDrive():
            logger.debug(f"WMI found drive: {cdrom.Drive}, MediaLoaded: {cdrom.MediaLoaded}, Name: {cdrom.Name}")
            drives.append(
                {
                    "drive": cdrom.Drive,
                    "media_loaded": cdrom.MediaLoaded,
                    "name": cdrom.Name,
                }
            )
        logger.debug(f"WMI drives: {drives}")
    except Exception as e:
        logger.error(f"WMI error: {e}")
    # Fallback: Use win32api to find CD-ROM drives
    try:
        import win32api
        import win32file
        logger.debug("Imported win32api and win32file successfully.")
        drive_bits = win32api.GetLogicalDrives()
        logger.debug(f"Logical drive bits: {bin(drive_bits)}")
        for i in range(26):
            mask = 1 << i
            if drive_bits & mask:
                drive_letter = f"{chr(65 + i)}:"
                logger.debug(f"Checking drive: {drive_letter}")
                try:
                    drive_type = win32file.GetDriveType(drive_letter + "\\")
                    logger.debug(f"Drive {drive_letter} type: {drive_type}")
                    # DRIVE_CDROM = 5
                    if drive_type == 5:
                        logger.debug(f"Drive {drive_letter} is a CD-ROM.")
                        # Try to get volume info
                        try:
                            vol_info = win32api.GetVolumeInformation(drive_letter + "\\")
                            name = vol_info[0]
                            media_loaded = True
                            logger.debug(f"Drive {drive_letter} volume info: {vol_info}")
                        except Exception as ve:
                            name = "CD-ROM Drive"
                            media_loaded = False
                            logger.debug(f"Drive {drive_letter} volume info error: {ve}")
                        # Avoid duplicates from WMI
                        if not any(d["drive"] == drive_letter for d in drives):
                            logger.debug(f"Adding drive {drive_letter} to list.")
                            drives.append({
                                "drive": drive_letter,
                                "media_loaded": media_loaded,
                                "name": name,
                            })
                except Exception as de:
                    logger.debug(f"Error checking drive {drive_letter}: {de}")
                    continue
    except ImportError:
        logger.error("win32api/win32file not available. For best results, install pywin32.")
    except Exception as e:
        logger.error(f"win32api/win32file error: {e}")
    logger.debug(f"Final drives list: {drives}")
    return drives


if __name__ == "__main__":
    for drive in get_optical_drives():
        print(
            f"Drive: {drive['drive']}, Media Loaded: {drive['media_loaded']}, Name: {drive['name']}"
        )
