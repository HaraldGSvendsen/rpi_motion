import time
import pathlib
import logging
import sys
import subprocess
import signal
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import gpiozero AFTER logging setup to avoid issues
from gpiozero import MotionSensor

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
    logger.info("Shutdown signal received. Exiting...")
    try:
        subprocess.run(["pkill", "-f", "mpv"], check=False)
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    try:
        # Initialize sensor
        pir = MotionSensor(18)
        video_list = get_videos("/home/harald/Videos", filetype="mp4")
        
        if video_list is None:
            logger.critical("No videos found. Exiting.")
            sys.exit(1)
        
        # Verify mpv
        try:
            subprocess.run(["mpv", "--version"], capture_output=True, check=True)
        except FileNotFoundError:
            logger.critical("mpv is not installed.")
            sys.exit(1)
        
        logger.info(f"Found {len(video_list)} videos. Starting polling loop...")
        
        # State
        counter = 0
        last_play_time = 0
        is_playing = False
        MIN_DELAY = 2
        POLL_INTERVAL = 0.1  # Check sensor every 100ms

        while True:
            # Check for shutdown
            # (We rely on signal_handler to exit, but we can add a flag if needed)
            
            current_time = time.time()
            
            # Check if motion is detected AND we are not playing AND cooldown passed
            if pir.motion_detected and not is_playing:
                if current_time - last_play_time >= MIN_DELAY:
                    logger.info("Motion detected! Starting video...")
                    is_playing = True
                    
                    video_file = video_list[counter]
                    logger.info(f"Playing: {video_file.name}")
                    
                    cmd = [
                        "mpv",
                        "--fs",
                        "--no-osd",
                        "--hwdec", "auto",
                        "--vo", "drm",
                        "--profile", "fast",
                        str(video_file)
                    ]
                    
                    try:
                        # Run mpv and WAIT for it to finish
                        process = subprocess.run(cmd)
                        
                        if process.returncode == 0:
                            logger.info("Video finished.")
                        else:
                            logger.warning(f"Video exited with code {process.returncode}")
                            
                    except Exception as e:
                        logger.error(f"Error running mpv: {e}")
                    
                    # Update state AFTER video finishes
                    last_play_time = time.time()
                    counter = (counter + 1) % len(video_list)
                    is_playing = False
                    logger.info("Ready for next motion.")
            
            # Sleep to prevent CPU hogging
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        try:
            subprocess.run(["pkill", "-f", "mpv"])
        except:
            pass
        raise
    finally:
        logger.info("Cleanup complete")

if __name__ == "__main__":
    main()