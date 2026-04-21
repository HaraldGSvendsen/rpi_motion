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
        logging.StreamHandler(sys.stdout) # Sends to systemd journal
    ]
)


logger = logging.getLogger(__name__)

def find_random_file(folder_path="movies/",filetype="mp4"):
    """
    Find all .mp4 files in the specified folder and return a random one.
    
    Args:
        folder_path: Path to the folder containing video files
        
    Returns:
        Path object of a random mp4 file, or None if no files found
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
    
    # Select a random file
    random_file = random.choice(all_files)
    return random_file

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

def play_video(filename,fullscreen=True):
    
    # Create an instance
    instance = vlc.Instance()

    # Create a media player
    player = instance.media_player_new()

    # Load the video file
    media = instance.media_new(filename)
    player.set_media(media)

    # Play the video
    player.play()

    if fullscreen:
        # Give VLC a moment to initialize the window before switching to fullscreen
        time.sleep(0.5)
        player.set_fullscreen(True)

    # Wait for video to finish (optional)
    while player.get_state() != vlc.State.Ended:
        time.sleep(0.5)
  
    # To close the window: Stop playback and release resources
    player.stop() 
    del player
    del media
    del instance



# MAIN SCRIPT -------------------------------
pir = MotionSensor(18)
video_list = get_videos("/home/harald/Videos",filetype="mp4")


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


def motion_function_OLD():
    logger.info("BEVEGELSE!")
    video_file = find_random_file("/home/harald/Videos",filetype="mp4")
    play_video(video_file,fullscreen=True)

def no_motion_function():
    #logger.info("stopp")
    pass

def motion_function():
    logger.info("BEVEGELSE!")
    video_file = video_list[motion_function.counter]

    media = instance.media_new(video_file)
    player.set_media(media)
    time.sleep(0.5)  # time to start before going fullscreen
    player.set_fullscreen(True)
    # Wait for video to finish:
    while player.get_state() != vlc.State.Ended:
        time.sleep(0.5)
    player.stop()

    motion_function.counter +=1 
    if motion_function.counter >= len(video_list):
        motion_function.counter = 0


motion_function.counter = 0 #initialise
pir.when_motion = motion_function
pir.when_no_motion = no_motion_function

pause()
