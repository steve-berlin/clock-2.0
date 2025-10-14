from time import sleep
import subprocess
from wakepy import keep

with keep.running():
    title = input("Title: ")
    caption = input("Caption: ")
    sfx = input("Sound effect: ")
    hrs = input("Hours: ")
    mins = input("Minutes: ")
    secs = input("Seconds: ")
    if hrs == "":
        hrs = 0
    if mins == "":
        mins = 0
    if secs == "":
        secs = 0

    total_secs = int(hrs) * 3600 + int(mins) * 60 + int(secs)
    # Play sound effect with fallback
    sound_to_play = sfx if sfx else "start.mp3"

    retcode = subprocess.call(["mpv", "--no-terminal", sound_to_play])
    if retcode != 0:
        print(f"Failed to play {sound_to_play}, trying default start.mp3")
        subprocess.call(["mpv", "--loop", "start.mp3"])

    while total_secs > 0:
        hrs = total_secs // 3600
        mins = (total_secs % 3600) // 60
        secs = total_secs % 60
        print(f"{hrs:02}:{mins:02}:{secs:02}", end="\r")
        sleep(1)
        total_secs -= 1

    print("Time's up!")
    if not title and not caption:
        subprocess.call(["notify-send", "Time's up!"])
    else:
        subprocess.call(["notify-send", title, caption])

    # Play sound effect with fallback
    sound_to_play = sfx if sfx else "alarm.mp3"

    try:
        retcode = subprocess.call(["mpv", "--no-terminal", "--loop", sound_to_play])
        if retcode != 0:
            print(f"Failed to play {sound_to_play}, trying default alarm.mp3")
            subprocess.call(["mpv", "--loop", "--no-terminal", "alarm.mp3"])
    except KeyboardInterrupt:
        print("Timer stopped by user.")
