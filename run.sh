#!/bin/bash

# Usage: ./create_and_burn_dvd.sh input_video.mp4 dvd.xml /dev/sr0

set -e

INPUT_VIDEO="$1"
DVD_XML="$2"
DVD_DEVICE="$3"

if [[ -z "$INPUT_VIDEO" || -z "$DVD_XML" ]]; then
    echo "Usage: $0 input_video.mp4 dvd.xml /dev/sr0"
    exit 1
fi

WORKDIR="dvd_workdir"
ISOFILE="dvd_image.iso"

# Ensure workdir exists and is clean
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

# Set VIDEO_FORMAT environment variable
export VIDEO_FORMAT="NTSC"

# Step 1: Convert video to NTSC DVD MPEG-2
echo "Converting video to NTSC DVD MPEG-2..."
ffmpeg -i "$INPUT_VIDEO" -target ntsc-dvd -b:v 1800k "$WORKDIR"/output.mpg

# Step 2: Author DVD structure
cp "$DVD_XML" "$WORKDIR"/dvd.xml
cd "$WORKDIR"
echo "Authoring DVD structure..."
dvdauthor -o . -x "../$DVD_XML"
cd - > /dev/null

# Step 3: Create ISO from DVD folder
echo "Creating ISO image..."
genisoimage -o "$ISOFILE" -dvd-video "$WORKDIR"

# Step 4: Preview with VLC if requested
if [[ "$4" == "--preview" ]]; then
    echo "Previewing output with VLC..."
    vlc "$WORKDIR/output.mpg"
fi

# Step 5: Burn ISO to DVD if device is specified
if [[ -n "$DVD_DEVICE" ]]; then
    echo "Burning ISO to DVD device $DVD_DEVICE..."
    growisofs -dvd-compat -Z "$DVD_DEVICE"="$ISOFILE"
    echo "DVD creation and burning complete."
else
    echo "No DVD device specified, skipping burn. DVD ISO is at $ISOFILE."
fi
