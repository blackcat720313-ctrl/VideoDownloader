import sys
import threading
from pathlib import Path
from urllib.parse import urlparse
import tkinter as tk
from tkinter import filedialog, messagebox

import yt_dlp


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ffmpeg_location() -> str | None:
    folder = app_dir() / "ffmpeg"
    if (folder / "ffmpeg.exe").exists():
        return str(folder)
    return None


class VideoDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("680x390")
        self.root.resizable(False, False)

        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar(value=str(Path.home() / "Downloads"))

        tk.Label(root, text="影片網址：", font=("Arial", 12)).pack(anchor="w", padx=20, pady=(20, 5))
        self.url_entry = tk.Entry(root, textvariable=self.url_var, font=("Arial", 11))
        self.url_entry.pack(fill="x", padx=20)

        tk.Label(root, text="儲存位置：", font=("Arial", 12)).pack(anchor="w", padx=20, pady=(15, 5))
        path_frame = tk.Frame(root)
        path_frame.pack(fill="x", padx=20)
        self.path_entry = tk.Entry(path_frame, textvariable=self.path_var, font=("Arial", 11))
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = tk.Button(path_frame, text="選擇資料夾", command=self.select_folder)
        self.browse_button.pack(side="left", padx=(10, 0))

        self.download_button = tk.Button(root, text="開始下載", font=("Arial", 12, "bold"), command=self.start_download)
        self.download_button.pack(pady=20)

        tk.Label(root, text="目前狀態：", font=("Arial", 12)).pack(anchor="w", padx=20)
        self.status_text = tk.Text(root, height=8, font=("Consolas", 10), state="disabled")
        self.status_text.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def select_folder(self):
        folder = filedialog.askdirectory(title="選擇影片儲存位置")
        if folder:
            self.path_var.set(folder)

    def update_status(self, message: str):
        self.status_text.config(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.config(state="disabled")

    def progress_hook(self, data):
        status = data.get("status")
        if status == "downloading":
            percent = data.get("_percent_str", "0%")
            speed = data.get("_speed_str", "未知")
            eta = data.get("_eta_str", "未知")
            self.root.after(0, self.update_status, f"下載中：{percent} | 速度：{speed} | 剩餘：{eta}")
        elif status == "finished":
            self.root.after(0, self.update_status, "串流下載完成，正在合併/處理檔案...")

    def start_download(self):
        url = self.url_var.get().strip()
        output_dir = self.path_var.get().strip()

        if not url:
            messagebox.showwarning("提醒", "請輸入影片網址。")
            return

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            messagebox.showerror("網址錯誤", "請輸入有效的影片網址。")
            return

        if not output_dir:
            messagebox.showwarning("提醒", "請選擇影片儲存位置。")
            return

        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            messagebox.showerror("錯誤", f"無法建立儲存資料夾：\n{e}")
            return

        self.download_button.config(state="disabled")
        self.browse_button.config(state="disabled")
        self.url_entry.config(state="disabled")
        self.update_status("準備下載...")
        self.update_status(f"網址：{url}")
        self.update_status(f"儲存位置：{output_dir}")

        threading.Thread(target=self.download_video, args=(url, output_dir), daemon=True).start()

    def download_video(self, url: str, output_dir: str):
        ffmpeg_dir = ffmpeg_location()
        if ffmpeg_dir is None:
            self.root.after(0, self.download_failed, "找不到 FFmpeg。\n請確認 VideoDownloader.exe 旁邊有 ffmpeg\\ffmpeg.exe。")
            return

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": str(Path(output_dir) / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": False,
            "ffmpeg_location": ffmpeg_dir,
            "progress_hooks": [self.progress_hook],
        }

        try:
            self.root.after(0, self.update_status, "正在解析影片...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise RuntimeError("無法取得影片資訊。")
                title = info.get("title", "未知影片")
                self.root.after(0, self.update_status, f"影片：{title}")
                self.root.after(0, self.update_status, "開始下載...")
                ydl.download([url])
            self.root.after(0, self.download_finished)
        except yt_dlp.utils.DownloadError as e:
            self.root.after(0, self.download_failed, f"下載失敗：\n{e}")
        except Exception as e:
            self.root.after(0, self.download_failed, f"發生錯誤：\n{e}")

    def set_controls(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.download_button.config(state=state)
        self.browse_button.config(state=state)
        self.url_entry.config(state=state)

    def download_finished(self):
        self.update_status("")
        self.update_status("================================")
        self.update_status("下載完成！")
        self.update_status(f"檔案位置：{self.path_var.get()}")
        self.update_status("================================")
        self.set_controls(True)
        messagebox.showinfo("下載完成", "影片已成功下載！")

    def download_failed(self, message: str):
        self.update_status("")
        self.update_status("❌ " + message)
        self.set_controls(True)
        messagebox.showerror("下載失敗", message)


if __name__ == "__main__":
    root = tk.Tk()
    VideoDownloaderApp(root)
    root.mainloop()
