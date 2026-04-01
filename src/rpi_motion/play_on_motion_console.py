#!/usr/bin/env python3
import time
import pathlib
import logging
import sys
import subprocess
import pygame
import os
from gpiozero import MotionSensor

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
# Environment for framebuffer
# -----------------------------
os.putenv('SDL_VIDEODRIVER', 'fbcon')  # framebuffer console
os.putenv('SDL_FBDEV', '/dev/fb0')

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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

def OLD_show_idle_image():
    logger.info("Showing idle image")
    return subprocess.Popen([
        "fbi",
        "-T", "1",
        "-noverbose",
        "-a",
        IDLE_IMAGE
    ])

def show_idle_image(screen):
    """Display idle image fullscreen with pygame"""
    try:
        image = pygame.image.load(IDLE_IMAGE)
        image = pygame.transform.scale(image, screen.get_size())  # scale to fullscreen
        screen.blit(image, (0, 0))
        pygame.display.flip()
    except Exception as e:
        logger.error(f"Failed to load idle image: {e}")


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

    # Initialize pygame framebuffer
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    logger.info(f"Showing image on screen: {screen}")
    show_idle_image(screen)
    #idle_proc = show_idle_image()  # show idle image initially

    try:
        while True:
            # Wait for motion to start first video
            while last_motion_time == 0:
                time.sleep(POLL_INTERVAL)

            # Kill idle image before video
            #if idle_proc:
            #    idle_proc.terminate()
            #    idle_proc.wait()
            #    idle_proc = None

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
                logger.info("Showing image and waiting for motion.")
                # No recent motion → show idle image and wait until motion
                show_idle_image(screen)  # return to idle
                #idle_proc = show_idle_image()
                while last_motion_time < (time.time() - VIDEO_END_BUFFER):
                    time.sleep(POLL_INTERVAL)
                # Kill idle image when motion detected
                #if idle_proc:
                #    idle_proc.terminate()
                #    idle_proc.wait()
                #    idle_proc = None

            # Move to next video
            counter = (counter + 1) % len(video_list)

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        # Cleanup VLC and fbi processes
        logger.info("Cleaning up processes...")
        subprocess.run(["pkill", "-f", "cvlc"], check=False)
        #subprocess.run(["pkill", "-f", "fbi"], check=False)
        logger.info("Done.")

if __name__ == "__main__":
    main()