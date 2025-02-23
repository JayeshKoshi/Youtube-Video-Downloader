import os
import subprocess
import re
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from pytubefix import YouTube


# Worker Thread for Downloading Video
class DownloadThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    done_signal = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            yt = YouTube(self.url, on_progress_callback=self.update_progress)
            title = yt.title
            self.log_signal.emit(f"🔹 Video Title: {title}")

            # Clean title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).replace(" ", "_")

            # Auto-detect best quality
            video_res = yt.streams.filter(adaptive=True, file_extension="mp4").order_by(
                "resolution").desc().first()
            audio_res = yt.streams.filter(
                only_audio=True, file_extension="mp4").order_by("abr").desc().first()

            if video_res and audio_res:
                video_path = os.path.join(self.save_path, "video.mp4")
                audio_path = os.path.join(self.save_path, "audio.mp4")

                self.log_signal.emit(
                    f"📥 Downloading Video: {video_res.resolution}")
                video_res.download(
                    output_path=self.save_path, filename="video.mp4")

                self.log_signal.emit(f"📥 Downloading Audio: {audio_res.abr}")
                audio_res.download(
                    output_path=self.save_path, filename="audio.mp4")

                self.log_signal.emit("🔄 Merging Video & Audio...")

                # Merge using ffmpeg
                final_output = os.path.join(
                    self.save_path, f"{safe_title}.mp4")
                ffmpeg_cmd = [
                    "ffmpeg", "-i", video_path, "-i", audio_path,
                    "-c:v", "copy", "-c:a", "aac", "-strict", "experimental",
                    final_output
                ]
                subprocess.run(ffmpeg_cmd, check=True)

                # Cleanup
                os.remove(video_path)
                os.remove(audio_path)
                self.log_signal.emit("🗑️ Deleted temporary files.")

                self.done_signal.emit(
                    f"✅ Download Completed! Saved as: {final_output}")
            else:
                self.log_signal.emit(
                    "⚠️ No suitable video/audio stream found.")

        except Exception as e:
            self.done_signal.emit(f"❌ Error: {str(e)}")

    def update_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        progress_percent = int((bytes_downloaded / total_size) * 100)
        self.progress_signal.emit(progress_percent)


# GUI Application
class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        """Initialize the PyQt GUI"""
        self.setWindowTitle("YouTube Video Downloader")
        self.setGeometry(300, 200, 500, 450)

        icon_path = "E:/Youtube Video Downloader/icons/video.png"
        self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()

        self.url_label = QLabel("Enter YouTube URL:")
        layout.addWidget(self.url_label)

        self.url_entry = QLineEdit(self)
        layout.addWidget(self.url_entry)

        self.folder_label = QLabel("Select Download Folder:")
        layout.addWidget(self.folder_label)

        self.folder_path = QLineEdit(self)
        self.folder_path.setText(os.getcwd())  # Default directory
        layout.addWidget(self.folder_path)

        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.select_folder)
        layout.addWidget(self.browse_button)

        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def log(self, message):
        """Update log display in the GUI."""
        self.log_text.append(message)

    def update_progress(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)

    def select_folder(self):
        """Open folder dialog to select download path."""
        folder_selected = QFileDialog.getExistingDirectory(
            self, "Select Download Folder")
        if folder_selected:
            self.folder_path.setText(folder_selected)

    def start_download(self):
        """Start downloading video using threading."""
        url = self.url_entry.text()
        save_path = self.folder_path.text()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL.")
            return

        self.log("🔗 Starting Download...")
        self.progress_bar.setValue(0)

        self.download_thread = DownloadThread(url, save_path)
        self.download_thread.log_signal.connect(self.log)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.done_signal.connect(self.download_finished)
        self.download_thread.start()

    def download_finished(self, message):
        """Handle when download is finished."""
        self.log(message)
        QMessageBox.information(self, "Download Completed", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())
