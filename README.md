# RPI Motion

Program for Raspberry Pi to play a random video file from a specified folder when motion is detected by a PIR sensor


## Make it a system service
- add shebang line at the very top of the script (`#!/usr/bin/env python3`)
- make it executable `chmod +x play_on_motion.py`
- copy `rpi_motion.service` to `/etc/systemd/system/` (modify if needed)
- reload the systemd daemon to recognise the service `sudo systemctl daemon-reload`
- enable service to start on boot: `sudo systemctl enable rpi_motion.service`
- start the service (without rebooting): `sudo systemctl start rpi_motion.service`

- disable automatic start of service: `sudo systemctl disable rpi_motion.service`

- view logs: `sudo journalctl -u rpi_motion.service -f`

## Make video work when run as a service
Summary Checklist for Your Service File
- User: Set to pi (or your desktop user).
- Target: `After=graphical.target` and `Requires=graphical.target`.
- Env: `Environment="DISPLAY=:0"`.
- Permissions: Ensure user is in video group (`sudo usermod -aG video pi`).
- Player: Use a hardware-accelerated player (mpv or vlc).

## Service file

### Running in graphical mode
rpi_motion.service - when running in graphical mode:

```
[Unit]
Description=Harald: Play on motion
After=network.target
After=graphical.target

[Service]
User=harald
Environment="DISPLAY=:0"
ExecStartPre=/bin/sleep 30
WorkingDirectory=/home/harald/code/rpi_motion
ExecStart=/home/harald/code/rpi_motion/env/bin/python /home/harald/code/rpi_motion/src/rpi_motion/play_on_motion.py

# Restart policy: always restart if the process exits (crashes)
Restart=always
RestartSec=5

# Optional: Capture logs to a file or journal
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
```
### Running from console mode (TTY)

It seems that a service playing videos with cvlc combined with  image displayed via this command may work:  
`sudo fbi -T 1 -d /dev/fb0 -noverbose -a /home/harald/Videos/idle.jpg`

trying to show the image from within the python script hasn't worked.

with fbi from the terminal, the video seems to be played on top, and when the video ends, the image comes back. Exactly as wanted. 

=>

Add this to `.profile` to show the background image after boot (and user harald auto login):  
`sudo fbi -T 1 -d /dev/fb0 -noverbose -a /home/harald/Videos/idle.jpg`