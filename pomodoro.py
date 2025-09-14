from time import sleep
import subprocess


def play_alarm():
    try:
        subprocess.call(["mpv", "--loop=inf", "alarm.mp3"])
    except FileNotFoundError:
        print("SFX not found, please add an alarm.mp3 file.")
    except Exception:
        print("Alarm couldn't be played.")
    except KeyboardInterrupt:
        print("Timer stopped by user")
        return


def timer(hrs, mins, secs, label):
    total_secs = int(hrs) * 3600 + int(mins) * 60 + int(secs)
    while total_secs > 0:
        cur_hrs = total_secs // 3600
        cur_mins = (total_secs % 3600) // 60
        cur_secs = total_secs % 60
        print(f"{label}: {cur_hrs:02}:{cur_mins:02}:{cur_secs:02}", end="\r")
        sleep(1)
        total_secs -= 1
    print(f"{label} time's up!            ")
    try:
        subprocess.call(["notify-send", f"{label} time's up!"])
    except Exception:
        print("Notification couldn't be sent.")
    play_alarm()


def pomodoro(
    work_hrs=input("Work hours: "),
    work_mins=input("Work minutes: "),
    rest_hrs=input("Rest hours: "),
    rest_mins=input("Rest minutes: "),
    repeat=input("Repeat: "),
):
    for cycle in range(int(repeat)):
        timer(work_hrs, work_mins, 0, "Work")
        timer(rest_hrs, rest_mins, 0, "Rest")


# Example usage
pomodoro()
