#!/usr/bin/env python3

import subprocess
import datetime

# Configuration
WAKEUP_HOUR = input("Hour (in 24h format): ")  # Set desired hour (24-hour format)
WAKEUP_MINUTE = input("Minute (in 24h format): ")  # Set desired minute
MUSIC_FILE = "music.mp3"  # Path to your music file

# Calculate current and target time
now = datetime.datetime.now()
wakeup = now.replace(
    hour=int(WAKEUP_HOUR), minute=int(WAKEUP_MINUTE), second=0, microsecond=0
)

# If the wake-up time is earlier than current time, set it for tomorrow
if wakeup < now:
    wakeup += datetime.timedelta(days=1)

# Calculate sleep duration in seconds
sleep_duration = int((wakeup - now).total_seconds())

# Command to wake up and play music
command = f"vlc {MUSIC_FILE} --play-and-exit"  # Using VLC; install with 'sudo apt install vlc'
rtcwake_cmd = f"rtcwake -m disk -s {sleep_duration} && sleep 5 && {command}"

# Execute the command
subprocess.run(["sudo", "/bin/bash", "-c", rtcwake_cmd])
