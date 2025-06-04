import platform
from tkinter import messagebox, filedialog, ttk
import tkinter as tk
import typer
from typing import Optional
from loguru import logger
import glob

from linux import run_for_linux
from windows import get_optical_drives, run_for_windows

app = typer.Typer()

@app.command()
def main(
    burn: bool = typer.Option(False, "--burn", help="Burn the ISO to DVD device"),
    iso: bool = typer.Option(False, "--iso", help="Create an ISO image from the DVD folder"),
    preview: bool = typer.Option(False, "--preview", help="Preview the output with VLC"),
    file_path: Optional[str] = typer.Option(None, "--file-path", help="Optional file path for the input video"),
    iso_output: Optional[str] = typer.Option(None, "--iso-output", help="Optional output path for the ISO image")
):
    logger.info("Welcome!")
    if file_path is None:
        logger.info("No file path provided, all other flags will be ignored.")
        gui_opts = run_with_gui()
        run_with_cli(
            burn=gui_opts['burn'],
            iso=gui_opts['iso'],
            preview=False,  # GUI does not support preview yet
            file_path=None,  # GUI does not select input file yet
            iso_output=gui_opts['iso_output']
        )
        return
    else:
        logger.info(f"File path provided: {file_path}")
        run_with_cli(
            burn=burn,
            iso=iso,
            preview=preview,
            file_path=file_path,
            iso_output=iso_output
        )

def run_with_gui():
    """Run the application in GUI mode."""
    selected_options = {
        'burn': False,
        'iso': False,
        'burn_drive': None,
        'iso_output': None
    }

    def on_burn_checked():
        if burn_var.get():
            burn_drive_combo.config(state="readonly")
        else:
            burn_drive_combo.config(state="disabled")
            burn_drive_var.set("")

    def on_iso_checked():
        if iso_var.get():
            iso_file_btn.config(state=tk.NORMAL)
        else:
            iso_file_btn.config(state=tk.DISABLED)
            iso_file_path.set("")

    def pick_iso_file():
        path = filedialog.asksaveasfilename(title="Select ISO output file", defaultextension=".iso", filetypes=[("ISO files", "*.iso")])
        if path:
            iso_file_path.set(path)

    def pick_video_file():
        path = filedialog.askopenfilename(title="Select input video file", filetypes=[("MP4 files", "*.mp4")])
        if path:
            video_file_path.set(path)

    root = tk.Tk()
    root.title("Simplified DVD GUI")
    root.geometry("850x300")
    root.resizable(False, False)
    root.configure(bg="#f4f4f4")

    # Style configuration
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TButton', font=('Segoe UI', 11), padding=6)
    style.configure('TCheckbutton', font=('Segoe UI', 11), background="#f4f4f4")
    style.configure('TEntry', font=('Segoe UI', 11))
    style.configure('TLabel', font=('Segoe UI', 11), background="#f4f4f4")

    # Title label (should be at the very top)
    title_label = ttk.Label(root, text="Simplified DVD Creator", font=("Segoe UI", 16, "bold"), background="#f4f4f4")
    title_label.grid(row=0, column=0, columnspan=3, pady=(10, 15))

    # Video file selection (required, now row 1)
    video_file_path = tk.StringVar()

    video_label = ttk.Label(root, text="Input Video (.mp4):")
    video_label.grid(row=1, column=0, padx=18, pady=(5, 5), sticky="w")
    video_entry = ttk.Entry(root, textvariable=video_file_path, width=38, state="readonly")
    video_entry.grid(row=1, column=1, padx=10, pady=(5, 5))
    video_btn = ttk.Button(root, text="Browse", command=pick_video_file)
    video_btn.grid(row=1, column=2, padx=10, pady=(5, 5))

    burn_var = tk.BooleanVar()
    iso_var = tk.BooleanVar()
    burn_file_path = tk.StringVar()
    iso_file_path = tk.StringVar()

    burn_cb = ttk.Checkbutton(root, text="Burn to DVD", variable=burn_var, command=on_burn_checked)
    burn_cb.grid(row=2, column=0, sticky="w", padx=18, pady=5)
    burn_drive_label = ttk.Label(root, text="Select DVD drive:")
    burn_drive_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    burn_drive_var = tk.StringVar()
    burn_drive_combo = ttk.Combobox(root, textvariable=burn_drive_var, state="disabled", width=35)
    burn_drive_combo.grid(row=2, column=2, padx=10, pady=5)

    iso_cb = ttk.Checkbutton(root, text="Create ISO", variable=iso_var, command=on_iso_checked)
    iso_cb.grid(row=3, column=0, sticky="w", padx=18, pady=5)
    iso_file_btn = ttk.Button(root, text="Select ISO output", command=pick_iso_file, state=tk.DISABLED)
    iso_file_btn.grid(row=3, column=1, padx=10, pady=5)
    iso_file_entry = ttk.Entry(root, textvariable=iso_file_path, width=38, state="readonly")
    iso_file_entry.grid(row=3, column=2, padx=10, pady=5)

    # Add a quit button for convenience
    quit_btn = ttk.Button(root, text="Quit", command=root.quit)
    quit_btn.grid(row=4, column=1, sticky="e", padx=10, pady=18)

    # Add a continue button
    def on_continue():
        # Disable continue button and show running status
        continue_btn.config(state=tk.DISABLED)
        continue_btn.config(text="Running...")
        root.update_idletasks()
        if not video_file_path.get():
            messagebox.showwarning("No video selected", "Please select an input .mp4 video file.")
            continue_btn.config(state=tk.NORMAL)
            continue_btn.config(text="Continue")
            return
        if not burn_var.get() and not iso_var.get():
            messagebox.showwarning("No action selected", "No action selected")
            continue_btn.config(state=tk.NORMAL)
            continue_btn.config(text="Continue")
            return
        selected_options['burn'] = burn_var.get()
        selected_options['iso'] = iso_var.get()
        selected_options['burn_drive'] = burn_drive_var.get() if burn_var.get() else None
        selected_options['iso_output'] = iso_file_path.get() if iso_var.get() else None
        selected_options['file_path'] = video_file_path.get()
        dvd_xml_path = "dvd.xml"  # Always use the correct XML path
        try:
            if platform.system() == "Windows":
                run_for_windows(
                    burn=selected_options['burn'],
                    iso=dvd_xml_path,
                    burn_drive=selected_options['burn_drive'],
                    iso_output=selected_options['iso_output'],
                    file_path=selected_options['file_path']
                )
            elif platform.system() == "Linux":
                run_for_linux(
                    burn=selected_options['burn'],
                    iso=dvd_xml_path,
                    burn_drive=selected_options['burn_drive'],
                    iso_output=selected_options['iso_output'],
                    file_path=selected_options['file_path']
                )
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        root.quit()

    continue_btn = ttk.Button(root, text="Continue", command=on_continue)
    continue_btn.grid(row=4, column=2, sticky="e", padx=10, pady=18)

    # Add some spacing
    root.grid_rowconfigure(0, minsize=10)
    root.grid_rowconfigure(4, minsize=20)
    root.grid_columnconfigure(0, minsize=140)
    root.grid_columnconfigure(1, minsize=160)
    root.grid_columnconfigure(2, minsize=320)

    # Populate DVD drives (Linux example: /dev/sr*, /dev/cdrom, /dev/dvd)
    if platform.system() == "Windows":
        drives = get_optical_drives()
    elif platform.system() == "Linux":
        drives = glob.glob("/dev/sr*") + glob.glob("/dev/cdrom*") + glob.glob("/dev/dvd*")
        if not drives:
            drives = ["No DVD drives found"]
        burn_drive_combo['values'] = drives
    else:
        drives = ["No DVD drives found, invalid platform"]
        

    root.mainloop()
    return selected_options

def run_with_cli(burn: bool, iso: bool, preview: bool, file_path: str, iso_output: Optional[str]):
    """Run the application in CLI mode with the provided options."""
    pass

if __name__ == "__main__":
    app()
