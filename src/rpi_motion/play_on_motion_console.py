#!/usr/bin/env python3
import pathlib
import logging
import sys
import subprocess
from gpiozero import MotionSensor
from signal import pause

# ----- Logging -----
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ----- Config -----
VIDEO_FOLDER = "/home/harald/Videos"
VIDEO_TYPE = "mp4"
PIR_PIN = 18
IDLE_IMAGE = "/home/harald/Videos/idle.jpg"

# ----- Load Videos -----
def get_videos(folder_path=VIDEO_FOLDER, filetype=VIDEO_TYPE):
    folder = pathlib.Path(folder_path)
    if not folder.exists():
        logger.error(f"Folder '{folder_path}' does not exist")
        return None
    all_files = sorted(set(folder.glob(f"*.{filetype}")))
    if not all_files:
        logger.warning(f"No .{filetype} files found in '{folder_path}'")
        return None
    return all_files

video_list = get_videos()
if video_list is None:
    logger.critical("No videos found. Exiting.")
    sys.exit(1)

video_counter = 0
idle_proc = None
video_playing = False  # flag to indicate a video is running

# ----- Functions -----
def show_idle_image():
    """Display the idle fullscreen image if no video is playing."""
    global idle_proc, video_playing
    if video_playing:
        # Don't show image while video is running
        return
    if idle_proc:
        idle_proc.terminate()
        idle_proc.wait()
    idle_proc = subprocess.Popen([
        "sudo", "fbi",
        "-T", "1",
        "-noverbose",
        "-a",
        IDLE_IMAGE
    ])
    logger.info("Idle image displayed.")

def play_next_video():
    """Play next video fully, then return to idle image."""
    global video_counter, idle_proc, video_playing
    if video_playing:
        # Already playing a video, ignore additional triggers
        logger.info("Video already playing, ignoring motion.")
        return

    video_playing = True

    # Kill idle image if running
    if idle_proc:
        idle_proc.terminate()
        idle_proc.wait()
        idle_proc = None

    video_file = video_list[video_counter]
    logger.info(f"Motion detected! Playing: {video_file.name}")

    # Play video to the end
    subprocess.run([
        "cvlc",
        "--fullscreen",
        "--no-osd",
        "--play-and-exit",
        str(video_file)
    ])

    # Update counter
    video_counter = (video_counter + 1) % len(video_list)
    video_playing = False

    # After video completes, show idle image
    show_idle_image()

# ----- Setup PIR -----
pir = MotionSensor(PIR_PIN)
pir.when_motion = play_next_video
# No need to use when_no_motion here, image is only shown after video ends

# ----- Main -----
try:
    show_idle_image()  # display image initially
    pause()            # wait for PIR events
except KeyboardInterrupt:
    logger.info("Exiting...")
finally:
    # Cleanup
    subprocess.run(["pkill", "-f", "cvlc"], check=False)
    if idle_proc:
        idle_proc.terminate()
        idle_proc.wait()
    logger.info("Cleanup complete.")