from gpiozero import MotionSensor
from signal import pause
import vlc
import time


def play_video(filename):
    # Create an instance
    instance = vlc.Instance()

    # Create a media player
    player = instance.media_player_new()

    # Load the video file
    media = instance.media_new(filename)
    player.set_media(media)

    # Play the video
    player.play()

    # Wait for video to finish (optional)
    while player.get_state() != vlc.State.Ended:
        time.sleep(0.5)
    print("Playback finished")




pir = MotionSensor(18)

def motion_function():
    print("BEVEGELSE!")
    play_video("/home/harald/test.mp4")

def no_motion_function():
    print("stopp")

pir.when_motion = motion_function
pir.when_no_motion = no_motion_function

pause()
