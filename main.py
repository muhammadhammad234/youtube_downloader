import os
import threading
import tkinter as tk
from tkinter import filedialog
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import ttkbootstrap as ttk
from yt_dlp import YoutubeDL

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 YouTube Video Downloader")
        self.root.geometry("620x540")
        self.root.resizable(False, False)

        self.style = Style("flatly")
        self.theme_toggle = "flatly"

        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar(value="best")
        self.folder_path = tk.StringVar(value=os.path.expanduser("~"))
        self.error_var = tk.StringVar()

        self.downloading = False
        self.stop_download_flag = False
        self.total_videos = 0
        self.downloaded_videos = 0

        self.build_ui()

    def build_ui(self):
        padding = {"padx": 10, "pady": 5}

        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=15, pady=10)

        ttk.Label(frame, text="YouTube URL:", font=('Helvetica', 11)).pack(**padding)
        self.url_entry = ttk.Entry(frame, textvariable=self.url_var, width=70)
        self.url_entry.pack(**padding)

        ttk.Label(frame, text="Select Quality:", font=('Helvetica', 11)).pack(**padding)
        self.quality_combo = ttk.Combobox(frame, textvariable=self.quality_var, values=["best", "worst", "audio", "720p", "480p"])
        self.quality_combo.pack()

        ttk.Label(frame, text="Save To:", font=('Helvetica', 11)).pack(**padding)
        ttk.Button(frame, text="Choose Folder", command=self.select_folder).pack()
        ttk.Label(frame, textvariable=self.folder_path, font=('Helvetica', 9)).pack()

        ttk.Label(frame, text="📹 Current Video Progress", font=('Helvetica', 10, 'bold')).pack(pady=(15, 0))
        self.progress = ttk.Progressbar(frame, maximum=100, length=500)
        self.progress.pack(pady=(2, 10))

        ttk.Label(frame, text="📂 Total Playlist/Channel Progress", font=('Helvetica', 10, 'bold')).pack(pady=(5, 0))
        self.total_progress = ttk.Progressbar(frame, maximum=100, length=500)
        self.total_progress.pack(pady=(2, 10))

        self.download_btn = ttk.Button(frame, text="⬇ Download", bootstyle=SUCCESS, command=self.start_download)
        self.download_btn.pack(pady=10)

        self.stop_btn = ttk.Button(frame, text="⛔ Stop", bootstyle=DANGER, command=self.stop_download, state=DISABLED)
        self.stop_btn.pack(pady=(0, 10))

        ttk.Button(frame, text="🌗 Toggle Theme", bootstyle=INFO, command=self.toggle_theme).pack()

        self.error_label = ttk.Label(frame, textvariable=self.error_var, foreground="red", wraplength=500)
        self.error_label.pack()

        ttk.Label(frame, text="Log:", font=('Helvetica', 11)).pack(pady=(10, 5))
        self.log_output = ScrolledText(frame, height=8, wrap=tk.WORD, font=("Courier", 9))
        self.log_output.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_output.insert(tk.END, msg + "\n")
        self.log_output.see(tk.END)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def toggle_theme(self):
        new_theme = "darkly" if self.theme_toggle == "flatly" else "flatly"
        self.style.theme_use(new_theme)
        self.theme_toggle = new_theme

    def set_ui_state(self, enabled):
        state = NORMAL if enabled else DISABLED
        for widget in [self.url_entry, self.quality_combo, self.download_btn]:
            widget.configure(state=state)
        self.stop_btn.configure(state=NORMAL if not enabled else DISABLED)

    def start_download(self):
        self.error_var.set("")
        self.stop_download_flag = False
        self.progress['value'] = 0
        self.total_progress['value'] = 0
        self.log_output.delete("1.0", tk.END)
        self.set_ui_state(False)
        threading.Thread(target=self.download_video).start()

    def stop_download(self):
        self.stop_download_flag = True
        self.log("⛔ Stopping download...")

    def progress_hook(self, d):
        if self.stop_download_flag:
            raise Exception("Download Stopped by User")

        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
            self.progress['value'] = float(percent_str)
            self.log(f"⬇ Downloading: {percent_str}%")
        elif d['status'] == 'finished':
            self.log("✅ Download Finished!")
            self.progress['value'] = 100
            if self.total_videos:
                self.downloaded_videos += 1
                overall = (self.downloaded_videos / self.total_videos) * 100
                self.total_progress['value'] = overall

    def download_video(self):
        url = self.url_var.get().strip()
        quality = self.quality_var.get().strip()
        path = self.folder_path.get()

        if not url:
            self.error_var.set("⚠️ Please enter a YouTube URL.")
            self.set_ui_state(True)
            return

        self.log(f"📥 Preparing download from: {url}")
        try:
            # Get playlist count first
            ydl_precheck = YoutubeDL({'quiet': True})
            info = ydl_precheck.extract_info(url, download=False)
            entries = info.get("entries")
            self.total_videos = len(entries) if entries else 1
            self.downloaded_videos = 0

            ydl_opts = {
                'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                'format': (
                    'bestaudio' if quality == 'audio'
                    else f'bestvideo[height<={quality[:-1]}]+bestaudio' if quality in ['720p', '480p']
                    else quality
                ),
                'progress_hooks': [self.progress_hook],
                'quiet': True,
                'ignoreerrors': True,
                'noplaylist': False,
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                self.log("🎉 All downloads complete!")
        except Exception as e:
            self.error_var.set(f"❌ {str(e)}")
            self.log(f"❌ Error: {str(e)}")
        finally:
            self.set_ui_state(True)

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = YouTubeDownloaderApp(root)
    root.mainloop()
