from gpiozero import MotionSensor
from signal import pause
import vlc
import time
import pathlib
import random
import logging
import sys

# Configure logging to stdout (which systemd captures)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


logger = logging.getLogger(__name__)

def get_videos(folder_path="movies/",filetype="mp4"):
    """
    Find all .mp4 files in the specified folder.
    
    Args:
        folder_path: Path to the folder containing video files
        
    Returns:
        list of file names (paths)
    """
    # Create Path object for the folder
    folder = pathlib.Path(folder_path)
    
    # Check if folder exists
    if not folder.exists():
        logger.error(f"Error: Folder '{folder_path}' does not exist")
        return None
    
    all_files = list(folder.glob(f"*.{filetype}"))

    # Remove duplicates and sort for consistency
    all_files = sorted(set(all_files))
    
    if not all_files:
        logger.warn(f"No .{filetype} files found in '{folder_path}'")
        return None
    
    return all_files

def signal_handler(signum, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM"""
    logger.info("Received shutdown signal, cleaning up...")
    player.stop()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# MAIN SCRIPT -------------------------------
try:
    pir = MotionSensor(18)
    video_list = get_videos("/home/harald/Videos",filetype="mp4")

    if video_list is None:
        logger.critical("No videos found or folder missing. Exiting.")
        sys.exit(1)

    # Optimized for Pi 3B/3B+
    # v4l2m2m: Hardware decoding for VideoCore IV
    # fb: Framebuffer output (very stable on Pi 3)
    # fullscreen: Force fullscreen mode
    options = [
        '--avcodec-hw=v4l2m2m', 
        '--vout=fb', 
        '--fullscreen',
        '--no-video-title-show'
    ]    
    # Video player (re-using the same instance)
    instance = vlc.Instance(options)
    player = instance.media_player_new()

    global motion_counter
    motion_counter = 0



    def no_motion_function():
        #logger.info("stopp")
        pass

    def motion_function():
        global motion_counter
        try:
            logger.info("Motion detected! Playing video...")
            video_file = video_list[motion_function.counter]
            logger.info(f"Playing: {video_file}")

            media = instance.media_new(video_file)
            player.set_media(media)
            player.play()

            #time.sleep(0.5)  # time to start before going fullscreen
            #player.set_fullscreen(True)
            # Wait for video to finish:
            while player.get_state() != vlc.State.Ended:
                time.sleep(0.5)
            player.stop()

        except Exception as e:
            logger.error(f"Error playing video {video_file}: {str(e)}")
            # Reset counter on error to avoid getting stuck
            
        motion_counter = (motion_counter + 1) % len(video_list)

    #motion_function.counter = 0 #initialise
    pir.when_motion = motion_function
    pir.when_no_motion = no_motion_function

    pause()

except KeyboardInterrupt:
    logger.info("Script interrupted by user")
    player.stop()
except Exception as e:
    logger.critical(f"Unexpected error: {str(e)}")
    player.stop()
    raise
finally:
    logger.info("Cleanup complete")