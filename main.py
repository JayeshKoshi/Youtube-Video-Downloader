import argparse
import os
import subprocess
import logging
import re
from pytubefix import YouTube


def setup_logging(title, save_path):
    """Configure logging for each video using its title as the log file name."""
    # Remove special characters from the title to create a valid filename
    safe_title = re.sub(r'[^\w\s-]', '', title).replace(" ", "_")
    log_filename = os.path.join(save_path, f"{safe_title}.log")

    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return log_filename


def downloadVideos(link, save_path):
    try:
        youtube = YouTube(link)
        title = youtube.title
        print("Connection Successful")
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    # Set up logging for this specific video
    log_file = setup_logging(title, "E:\Youtube Video Downloader\Logs")
    logging.info(f"🔗 Downloading Video from: {link}")

    print(f"Logging to: {log_file}")

    # Get highest resolution video (1080p or highest available)
    video_res = youtube.streams.filter(
        file_extension="mp4", adaptive=True, res="1080p"
    ).first()
    audio_res = youtube.streams.filter(
        only_audio=True, file_extension="mp4").first()

    if video_res and audio_res:
        try:
            # print(f"Downloading Video: {video_res}")
            video_path = os.path.join(save_path, "video.mp4")
            video_res.download(output_path=save_path, filename="video.mp4")
            logging.info(f"✅ Downloaded Video: {video_res}")

            # print(f"Downloading Audio: {audio_res}")
            audio_path = os.path.join(save_path, "audio.mp4")
            audio_res.download(output_path=save_path, filename="audio.mp4")
            logging.info(f"✅ Downloaded Audio: {audio_res}")

            # print("Both video and audio downloaded! Now merging...")sss
            logging.info(f"🔄 Merging video and audio for: {title}")

            # Merge using ffmpeg
            final_output = os.path.join(
                save_path, f"{title.replace(' ', '_')}.mp4")

            ffmpeg_cmd = [
                "ffmpeg",
                "-i", video_path,  # Input video
                "-i", audio_path,  # Input audio
                "-c:v", "copy",  # Copy video codec
                "-c:a", "aac",  # Convert audio to AAC
                "-strict", "experimental",
                final_output,  # Output file
            ]

            subprocess.run(ffmpeg_cmd, check=True)
            logging.info(f"🎉 Final video saved: {final_output}")
            print("✅ Video saved as:", final_output)

            # Cleanup: Delete temporary files
            if os.path.exists(video_path):
                os.remove(video_path)
                logging.info(f"🗑️ Deleted temporary file: {video_path}")
                # print("🗑️ Deleted:", video_path)

            if os.path.exists(audio_path):
                os.remove(audio_path)
                logging.info(f"🗑️ Deleted temporary file: {audio_path}")
                # print("🗑️ Deleted:", audio_path)

        except Exception as e:
            logging.error(f"❌ Error while processing: {e}")
            print(f"❌ Error while processing: {e}")
    else:
        logging.warning(f"⚠️ No suitable video/audio stream found for {link}")
        print("⚠️ No suitable video/audio stream found!")


def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video details and download.")
    parser.add_argument("url", help="YouTube video URL")

    # Parse arguments
    args = parser.parse_args()
    link = args.url

    save_path = "E:/Youtube Video Downloader/Downloaded Videos"
    downloadVideos(link, save_path)


if __name__ == "__main__":
    main()
