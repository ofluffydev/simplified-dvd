# Simplified DVD Creator

A cross-platform tool to easily convert MP4 videos to DVD format, create ISO images, and optionally burn them to a DVD disc. Features both a graphical user interface (GUI) and a command-line interface (CLI).

## Features
- **Convert MP4 to DVD**: Transcodes your video to NTSC DVD MPEG-2 format.
- **Create ISO Image**: Authors a DVD structure and generates a DVD-video ISO file.
- **Burn to DVD**: Burns the ISO to a physical DVD drive (if available).
- **Cross-platform**: Works on Linux and Windows (with WSL fallback for DVD tools on Windows).
- **Simple GUI**: User-friendly interface for non-technical users.
- **CLI Support**: Advanced users can automate or script DVD creation.

## Requirements

### Linux
- Python 3.7+
- [ffmpeg](https://ffmpeg.org/)
- [dvdauthor](http://dvdauthor.sourceforge.net/)
- [genisoimage](https://wiki.archlinux.org/title/Genisoimage) (or `mkisofs`)
- [growisofs](http://linux.die.net/man/1/growisofs) (for burning DVDs)
- [loguru](https://github.com/Delgan/loguru) (`pip install loguru`)
- [typer](https://typer.tiangolo.com/) (`pip install typer`)

### Windows
- Python 3.7+
- [ffmpeg](https://ffmpeg.org/)
- [dvdauthor](http://dvdauthor.sourceforge.net/)
- [genisoimage](https://wiki.archlinux.org/title/Genisoimage) (or `mkisofs`)
- [growisofs](http://linux.die.net/man/1/growisofs) (for burning DVDs)
- [wmi](https://pypi.org/project/WMI/) (`pip install WMI`) (for drive detection)
- [loguru](https://github.com/Delgan/loguru`)
- [typer](https://typer.tiangolo.com/)
- **Note:** If native tools are not found, the app will attempt to use WSL (Windows Subsystem for Linux).

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/ofluffydev/simplified-dvd.git
   cd simplified-dvd
   ```
2. Install Python dependencies:
   ```sh
   pip install typer loguru
   # On Windows, also:
   pip install WMI
   ```
3. Install required system tools (see Requirements above).

## Usage

### GUI Mode
Just run the script without arguments:
```sh
python main.py
```
- Select your input MP4 file.
- Choose whether to create an ISO, burn to DVD, or both.
- Select output paths and DVD drive as needed.
- Click **Continue** to start the process.

### CLI Mode
You can also use the command line for automation or scripting:
```sh
python main.py --file-path <input.mp4> [--iso] [--burn] [--iso-output <output.iso>] [--preview]
```
- `--file-path`: Path to the input MP4 file (required for CLI mode)
- `--iso`: Create an ISO image
- `--burn`: Burn the ISO to a DVD device
- `--iso-output`: Output path for the ISO file (optional)
- `--preview`: Preview the output with VLC (not yet implemented)

#### Example
Create an ISO and burn it to DVD:
```sh
python main.py --file-path myvideo.mp4 --iso --burn --iso-output dvd_image.iso
```

## How It Works
- **Video Conversion**: Uses `ffmpeg` to convert your MP4 to DVD-compliant MPEG-2.
- **DVD Authoring**: Uses `dvdauthor` to create the DVD structure.
- **ISO Creation**: Uses `genisoimage` to package the DVD folder into an ISO.
- **Burning**: Uses `growisofs` to burn the ISO to a DVD drive.

## File Structure
- `main.py` — Main entry point, GUI and CLI logic.
- `linux.py` — Linux-specific DVD creation logic.
- `windows.py` — Windows-specific logic, including WSL fallback.
- `dvd.xml` — Example DVD XML file (auto-generated as needed).
- `dvd_workdir/` — Temporary working directory for DVD build process.

## Troubleshooting
- Ensure all required system tools are installed and available in your PATH.
- On Windows, WSL is used if native tools are missing. Make sure WSL is installed and configured.
- For burning, insert a blank DVD and select the correct drive.
- If you encounter permission errors, try running as administrator/root.

## License
MIT License or Apache License 2.0

## Credits
- [ffmpeg](https://ffmpeg.org/)
- [dvdauthor](http://dvdauthor.sourceforge.net/)
- [genisoimage](https://wiki.archlinux.org/title/Genisoimage)
- [growisofs](http://linux.die.net/man/1/growisofs)
- [typer](https://typer.tiangolo.com/)
- [loguru](https://github.com/Delgan/loguru)

---

*Simplified DVD Creator — Make DVDs from your videos, the easy way!*
