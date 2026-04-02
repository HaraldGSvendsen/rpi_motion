#!/usr/bin/env python3
import time
import pathlib
import logging
import sys
import subprocess
from gpiozero import MotionSensor

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.info("Starting python script.")

# -----------------------------
# Configuration
# -----------------------------
VIDEO_FOLDER = "/home/harald/Videos"
VIDEO_EXT = "mp4"
IDLE_IMAGE = "/home/harald/Videos/idle.jpg"
PIR_PIN = 18
VIDEO_END_BUFFER = 5  # seconds before video end to queue next
POLL_INTERVAL = 0.1   # loop sleep interval



# -----------------------------
# Motion setup
# -----------------------------
pir = MotionSensor(PIR_PIN)
last_motion_time = 0

def motion_detected():
    global last_motion_time
    last_motion_time = time.time()
    logger.info("Motion detected!")

pir.when_motion = motion_detected

# -----------------------------
# Video management
# -----------------------------
def get_videos(folder_path=VIDEO_FOLDER, ext=VIDEO_EXT):
    folder = pathlib.Path(folder_path)
    if not folder.exists():
        logger.error(f"Folder '{folder_path}' does not exist")
        return []
    files = sorted(folder.glob(f"*.{ext}"))
    if not files:
        logger.warning(f"No .{ext} files found in '{folder_path}'")
    return files

def play_video(video_file):
    logger.info(f"Playing video: {video_file.name}")
    # Non-blocking VLC process
    return subprocess.Popen([
        "cvlc",
        "--fullscreen",
        "--no-osd",
        "--play-and-exit",
        str(video_file)
    ])


# -----------------------------
# Main loop
# -----------------------------
def main():
    global last_motion_time
    video_list = get_videos()
    if not video_list:
        logger.critical("No videos found. Exiting.")
        sys.exit(1)

    logger.info(f"Found {len(video_list)} videos")
    counter = 0

    try:
        while True:
            # Wait for motion to start first video
            while last_motion_time == 0:
                time.sleep(POLL_INTERVAL)

            video_file = video_list[counter]
            video_proc = play_video(video_file)
            video_start_time = time.time()

            # Monitor video while updating motion detection
            while video_proc.poll() is None:  # video still playing
                time.sleep(POLL_INTERVAL)
                # last_motion_time is updated by PIR callbacks in real-time

            video_end_time = time.time()

            # Check if motion occurred during last VIDEO_END_BUFFER seconds of the video
            if last_motion_time >= (video_end_time - VIDEO_END_BUFFER):
                logger.info("Motion in last 5s → queue next video")
                counter = (counter + 1) % len(video_list)
                continue  # play next video immediately
            else:
                logger.info("Waiting for motion detection. No video output")
                # No recent motion → wait until motion
                while last_motion_time < (time.time() - VIDEO_END_BUFFER):
                    time.sleep(POLL_INTERVAL)

            # Move to next video
            counter = (counter + 1) % len(video_list)

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        # Cleanup VLC processes
        logger.info("Cleaning up processes...")
        subprocess.run(["pkill", "-f", "cvlc"], check=False)
        logger.info("Done.")

if __name__ == "__main__":
    main()