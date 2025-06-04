import os
import shutil
import subprocess

from loguru import logger


def run_for_linux(burn, iso, burn_drive, iso_output, file_path):
    """
    burn: Boolean, whether to burn to DVD device
    iso: Path to DVD XML file (e.g., 'dvd.xml')
    burn_drive: DVD device path (e.g., '/dev/sr0'), or None to skip burning
    iso_output: Path for the output ISO file (e.g., 'dvd_image.iso')
    file_path: Path to input video file (e.g., 'input_video.mp4')
    """
    WORKDIR = "dvd_workdir"
    OUTPUT_MPG = os.path.join(WORKDIR, "output.mpg")

    # Ensure workdir exists and is clean
    if os.path.exists(WORKDIR):
        shutil.rmtree(WORKDIR)
    os.makedirs(WORKDIR, exist_ok=True)

    # Ensure VIDEO_FORMAT is set to NTSC for dvdauthor compatibility
    os.environ["VIDEO_FORMAT"] = "NTSC"

    # Step 1: Convert video to NTSC DVD MPEG-2
    logger.info("Converting video to NTSC DVD MPEG-2...")
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
    ffmpeg_result = subprocess.run(ffmpeg_cmd)
    if ffmpeg_result.returncode != 0:
        logger.error("ffmpeg failed to create output.mpg!")
        return
    if not os.path.exists(OUTPUT_MPG):
        logger.error(f"ERROR: {OUTPUT_MPG} was not created!")
        return

    # Step 1.5: Create DVD XML file directly in WORKDIR
    logger.info("Creating DVD XML file...")
    dvd_xml_path = os.path.join(WORKDIR, "dvd.xml")
    create_dvd_xml(dvd_xml_path, video_filename="output.mpg")

    # Create DVD output subfolder
    DVD_FOLDER = os.path.join(WORKDIR, "DVD")
    os.makedirs(DVD_FOLDER, exist_ok=True)

    # Step 2: Author DVD structure (run from WORKDIR)
    logger.info("Authoring DVD structure...")
    dvdauthor_cmd = ["dvdauthor", "-o", "DVD", "-x", "dvd.xml"]
    subprocess.run(dvdauthor_cmd, check=True, cwd=WORKDIR)

    # Step 3: Create ISO from DVD folder
    logger.info("Creating ISO image...")
    # Default iso_output if not provided
    if not iso_output:
        iso_output = "dvd.iso"
        logger.info(f"No ISO output path specified. Defaulting to {iso_output}")
    # If iso_output is an absolute path, use as is; otherwise, treat as relative to WORKDIR when running genisoimage
    genisoimage_output = iso_output if os.path.isabs(iso_output) else os.path.join(WORKDIR, iso_output)
    genisoimage_output = os.path.abspath(genisoimage_output)
    logger.info(f"Creating ISO at {genisoimage_output}")
    genisoimage_cmd = ["genisoimage", "-o", genisoimage_output, "-dvd-video", os.path.join("DVD")]
    subprocess.run(genisoimage_cmd, check=True, cwd=WORKDIR)

    # Step 5: Burn ISO to DVD if burn is True and device is specified
    if burn and burn_drive:
        # Use absolute path for ISO file
        iso_abspath = os.path.abspath(genisoimage_output)
        logger.info(f"Burning ISO to DVD device {burn_drive}...")
        growisofs_cmd = ["growisofs", "-dvd-compat", "-Z", f"{burn_drive}={iso_abspath}"]
        subprocess.run(growisofs_cmd, check=True)
        logger.info("DVD creation and burning complete.")
    else:
        logger.info(f"Burning skipped. DVD ISO is at {genisoimage_output}.")


def create_dvd_xml(xml_path, video_filename="output.mpg"):
    dvd_xml_content = f"""
<dvdauthor>
  <vmgm />
  <titleset>
    <titles>
      <pgc>
        <vob file=\"{video_filename}\" />
      </pgc>
    </titles>
  </titleset>
</dvdauthor>
"""
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(dvd_xml_content)
    logger.info(f"Created DVD XML at {xml_path}")
