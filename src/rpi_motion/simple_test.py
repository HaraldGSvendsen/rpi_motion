from gpiozero import MotionSensor
from signal import pause
import vlc
import time


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
    print("Playback finished")

    # To close the window: Stop playback and release resources
    player.stop() 
    del player
    del media
    del instance
    
    print("Window closed.")



pir = MotionSensor(18)

def motion_function():
    print("BEVEGELSE!")
    play_video("/home/harald/test.mp4")

def no_motion_function():
    print("stopp")

pir.when_motion = motion_function
pir.when_no_motion = no_motion_function

pause()
