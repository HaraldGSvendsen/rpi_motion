#!/usr/bin/env python3
import time
import pathlib
import logging
import sys
import subprocess

from gpiozero import MotionSensor

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

def main():
    pir = MotionSensor(18)
    video_list = get_videos("/home/harald/Videos", filetype="mp4")
    
    if video_list is None:
        logger.critical("No videos found. Exiting.")
        sys.exit(1)
    
    logger.info(f"Found {len(video_list)} videos. Starting...")
    
    counter = 0
    last_play_time = 0
    is_playing = False
    MIN_DELAY = 2
    POLL_INTERVAL = 0.1

    try:
        while True:
            current_time = time.time()
            
            if pir.motion_detected and not is_playing:
                if current_time - last_play_time >= MIN_DELAY:
                    logger.info("Motion detected! Starting video...")
                    is_playing = True
                    
                    video_file = video_list[counter]
                    logger.info(f"Playing: {video_file.name}")
                    
                    cmd = [
                        "mpv",
                        "--fs", 
                        "--hwdec=auto", 
                        "--vo=drm",  
                        "--profile=fast",   
                        "--vd-lavc-threads=1",  
                        "--ao=alsa", 
                        "--sync=audio", 
                        str(video_file)
                    ]
#                        "mpv",
#                        "--fs",
#                        "--hwdec=auto", # v4l2m2m or auto
#                        "--profile=fast",
#                        "--vo=drm",
#                        #"--gpu-api=opengl",
#                        #"--gpu-context=wayland",
#                        str(video_file)
#                    ]
                    
                    # Run mpv
                    subprocess.run(cmd)
                    
                    last_play_time = time.time()
                    counter = (counter + 1) % len(video_list)
                    is_playing = False
            
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        # CRITICAL: Kill mpv if it's still running
        logger.info("Cleaning up mpv...")
        subprocess.run(["pkill", "-f", "mpv"], check=False)
        logger.info("Done.")

if __name__ == "__main__":
    main()