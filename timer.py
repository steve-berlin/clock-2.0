from time import sleep
import subprocess

hrs = input("Hours: ")
mins = input("Minutes: ")
secs = input("Seconds: ")
# if mins
# Timer
# Convert to seconds
total_secs = int(hrs) * 3600 + int(mins) * 60 + int(secs)
while total_secs > 0:
    # Calculate hours, minutes, seconds
    hrs = total_secs // 3600
    mins = (total_secs % 3600) // 60
    secs = total_secs % 60
    # Display the timer
    print(f"{hrs:02}:{mins:02}:{secs:02}", end="\r")
    sleep(1)
    total_secs -= 1
print("Time's up!")
subprocess.call(["notify-send", "Time's up!"])
while True:
    try:
        subprocess.call(["mpv", "--loop", "alarm.mp3"])
    except FileNotFoundError:
        print(
            "SFX not found, please add an alarm.mp3 file in the same directory as this script."
        )
        break
    except KeyboardInterrupt:
        print("Timer stopped by user.")
        break
    # SFX not found
