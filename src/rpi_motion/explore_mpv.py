from gpiozero import MotionSensor
from signal import pause
import subprocess
import time
import pathlib
import logging
import sys
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def get_videos(folder_path="/home/harald/Videos", filetype="mp4"):
    folder = pathlib.Path(folder_path)
    if not folder.exists():
        logger.error(f"Error: Folder '{folder_path}' does not exist")
        return None
    
    all_files = list(folder.glob(f"*.{filetype}"))
    all_files = sorted(set(all_files))
    
    if not all_files:
        logger.warning(f"No .{filetype} files found in '{folder_path}'")
        return None
    
    return all_files

def signal_handler(signum, frame):
    logger.info("Shutdown signal received. Stopping player...")
    subprocess.run(["pkill", "-f", "mpv"])
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    pir = MotionSensor(18)
    video_list = get_videos("/home/harald/Videos", filetype="mp4")
    
    if video_list is None:
        logger.critical("No videos found or folder missing. Exiting.")
        sys.exit(1)
    
    # Verify mpv is installed
    try:
        subprocess.run(["mpv", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        logger.critical("mpv is not installed. Please run: sudo apt install mpv")
        sys.exit(1)
    
    logger.info(f"Found {len(video_list)} videos. Starting motion detection...")
    
    # Initialize function attributes
    motion_function.counter = 0
    motion_function.last_play_time = 0
    motion_function.is_playing = False  # <-- NEW: Lock flag
    MIN_DELAY_BETWEEN_VIDEOS = 2

    def no_motion_function():
        pass

    def motion_function():
        # Check if already playing (prevent recursion)
        if motion_function.is_playing:
            logger.debug("Motion ignored: video already playing")
            return
        
        current_time = time.time()
        
        # Check cooldown period
        if current_time - motion_function.last_play_time < MIN_DELAY_BETWEEN_VIDEOS:
            logger.debug("Motion ignored: too soon after last video")
            return
        
        # Set lock flag
        motion_function.is_playing = True
        
        try:
            video_file = video_list[motion_function.counter]
            logger.info(f"Motion detected! Playing: {video_file.name}")
            
            cmd = [
                "mpv",
                "--fs",
                "--no-osd",
                "--hwdec", "auto",
                "--vo", "drm",
                "--profile", "fast",
                str(video_file)
            ]
            
            process = subprocess.run(cmd)
            
            if process.returncode == 0:
                logger.info("Video finished successfully.")
            else:
                logger.warning(f"Video exited with code {process.returncode}")
            
            motion_function.last_play_time = time.time()
            motion_function.counter = (motion_function.counter + 1) % len(video_list)
            
        except Exception as e:
            logger.error(f"Error playing video: {e}")
            motion_function.counter = 0
        finally:
            # Release lock flag (CRITICAL!)
            motion_function.is_playing = False

    pir.when_motion = motion_function
    pir.when_no_motion = no_motion_function
    
    pause()

except KeyboardInterrupt:
    logger.info("Interrupted by user")
except Exception as e:
    logger.critical(f"Fatal error: {e}")
    subprocess.run(["pkill", "-f", "mpv"])
    raise
finally:
    logger.info("Cleanup complete")