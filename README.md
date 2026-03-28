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