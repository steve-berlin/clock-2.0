#!/usr/bin/env python3
"""Unified clock app: timer, pomodoro, stopwatch, and alarm."""

import argparse
import sys
import os
import subprocess
import termios
import tty
import select
import datetime as dt
from time import sleep, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALARM_SFX = os.path.join(SCRIPT_DIR, "alarm.mp3")
START_SFX = os.path.join(SCRIPT_DIR, "start.mp3")


# ── Input helpers ──────────────────────────────────────────────────────────


def get_int(prompt, min_val=0, max_val=None, default=0):
    """Prompt for an integer with validation and a default value."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        if raw.isdigit():
            val = int(raw)
            if val >= min_val and (max_val is None or val <= max_val):
                return val
        ceiling = f" and {max_val}" if max_val is not None else ""
        print(f"  Enter a number between {min_val}{ceiling}.")


def get_key_nonblocking():
    """Return a keypress character if available, else None (non-blocking)."""
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


# ── Audio & notification ──────────────────────────────────────────────────


def play_sfx(path, loop=False):
    """Play an audio file via mpv. Returns the Popen handle if looping."""
    args = ["mpv", "--no-terminal"]
    if loop:
        args.append("--loop=inf")
    args.append(path)
    try:
        if loop:
            return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("mpv not found – install it for audio support.")
    return None


def notify(title, body=""):
    """Send a desktop notification via notify-send."""
    try:
        cmd = ["notify-send", title] + ([body] if body else [])
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass


# ── Raw-mode context manager ─────────────────────────────────────────────


class RawMode:
    """Switch stdin to raw/non-blocking mode for keypress detection."""

    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, *_):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


# ── Countdown (shared by timer & pomodoro) ────────────────────────────────


def fmt_time(total_secs):
    h = total_secs // 3600
    m = (total_secs % 3600) // 60
    s = total_secs % 60
    return f"{h:02}:{m:02}:{s:02}"


def countdown(total_secs, label="Timer"):
    """Count down with pause (space/p) and cancel (q/Ctrl-C) support."""
    paused = False
    with RawMode():
        while total_secs > 0:
            key = get_key_nonblocking()
            if key in ("p", " "):
                paused = not paused
                status = "PAUSED" if paused else label
                print(f"\r{status}: {fmt_time(total_secs)}   ", end="", flush=True)
            elif key == "q":
                print(f"\r{label} cancelled.          ")
                return False

            if paused:
                sleep(0.1)
                continue

            print(f"\r{label}: {fmt_time(total_secs)}   ", end="", flush=True)
            sleep(1)
            total_secs -= 1

    print(f"\r{label}: 00:00:00 — done!     ")
    return True


# ── Timer ─────────────────────────────────────────────────────────────────


def run_timer(title=None, caption=None, sfx=None, hours=None, minutes=None, seconds=None):
    title = title if title is not None else input("Title (enter to skip): ").strip()
    caption = caption if caption is not None else input("Caption (enter to skip): ").strip()
    sfx = sfx if sfx is not None else input("Sound effect file (enter for default): ").strip()
    hrs = hours if hours is not None else get_int("Hours [0]: ")
    mins = minutes if minutes is not None else get_int("Minutes [0]: ")
    secs = seconds if seconds is not None else get_int("Seconds [0]: ")

    total = hrs * 3600 + mins * 60 + secs
    if total == 0:
        print("Nothing to time.")
        return

    play_sfx(START_SFX)
    label = title or "Timer"

    print("  [space/p] pause  [q] cancel")
    finished = countdown(total, label)

    if finished:
        notify(title or "Time's up!", caption or "")
        sfx_path = sfx if sfx else ALARM_SFX
        proc = play_sfx(sfx_path, loop=True)
        if proc:
            print("  Press Enter to stop alarm...")
            input()
            proc.terminate()
            proc.wait()


# ── Pomodoro ──────────────────────────────────────────────────────────────


def run_pomodoro(work=None, rest=None, cycles=None):
    work_mins = work if work is not None else get_int("Work minutes [25]: ", default=25)
    rest_mins = rest if rest is not None else get_int("Rest minutes [5]: ", default=5)
    cycles = cycles if cycles is not None else get_int("Cycles [4]: ", min_val=1, default=4)

    print("  [space/p] pause  [q] cancel")
    for i in range(1, cycles + 1):
        print(f"\n── Cycle {i}/{cycles} ──")
        if not countdown(work_mins * 60, "Work"):
            return
        notify("Work done!", "Time to rest.")
        proc = play_sfx(ALARM_SFX, loop=True)
        if proc:
            print("  Press Enter to start rest...")
            with RawMode():
                pass  # exit raw mode first
            input()
            proc.terminate()
            proc.wait()

        if not countdown(rest_mins * 60, "Rest"):
            return
        notify("Rest over!", "Back to work." if i < cycles else "All done!")
        proc = play_sfx(ALARM_SFX, loop=True)
        if proc:
            print("  Press Enter to continue...")
            input()
            proc.terminate()
            proc.wait()

    print("Pomodoro complete!")


# ── Stopwatch ─────────────────────────────────────────────────────────────


def run_stopwatch():
    print("  [space/p] pause  [l] lap  [q] quit")
    elapsed = 0.0
    lap_num = 0
    paused = False

    with RawMode():
        last = time()
        while True:
            key = get_key_nonblocking()
            if key in ("p", " "):
                paused = not paused
                if not paused:
                    last = time()  # reset tick reference after unpause
            elif key == "l" and not paused:
                lap_num += 1
                print(f"\r  Lap {lap_num}: {fmt_time(int(elapsed))}          ")
            elif key == "q":
                break

            now = time()
            if not paused:
                elapsed += now - last
            last = now

            tag = "PAUSED" if paused else "Stopwatch"
            print(f"\r{tag}: {fmt_time(int(elapsed))}   ", end="", flush=True)
            sleep(0.1)

    print(f"\rStopped at {fmt_time(int(elapsed))}          ")


# ── Alarm ─────────────────────────────────────────────────────────────────


def run_alarm(title=None, caption=None, hour=None, minute=None, second=None):
    title = title if title is not None else input("Title (enter to skip): ").strip()
    caption = caption if caption is not None else input("Caption (enter to skip): ").strip()
    hour = hour if hour is not None else get_int("Hour (0-23): ", max_val=23)
    minute = minute if minute is not None else get_int("Minute (0-59): ", max_val=59)
    second = second if second is not None else get_int("Second (0-59): ", max_val=59)

    target = f"{hour:02}:{minute:02}:{second:02}"
    print(f"Alarm set for {target}. Waiting...")

    try:
        while True:
            now = dt.datetime.now()
            if (now.hour, now.minute, now.second) == (hour, minute, second):
                break
            sleep(0.5)
    except KeyboardInterrupt:
        print("\nAlarm cancelled.")
        return

    notify(title or "Alarm!", caption or target)
    print(f"Alarm! {target}")
    proc = play_sfx(ALARM_SFX, loop=True)
    if proc:
        print("  Press Enter to stop alarm...")
        input()
        proc.terminate()
        proc.wait()


# ── CLI ───────────────────────────────────────────────────────────────────


def build_parser():
    parser = argparse.ArgumentParser(prog="clock", description="Timer, pomodoro, stopwatch & alarm.")
    sub = parser.add_subparsers(dest="mode")

    # timer
    t = sub.add_parser("timer", aliases=["t"], help="Countdown timer")
    t.add_argument("-H", "--hours", type=int, default=None)
    t.add_argument("-m", "--minutes", type=int, default=None)
    t.add_argument("-s", "--seconds", type=int, default=None)
    t.add_argument("-t", "--title", default=None)
    t.add_argument("-c", "--caption", default=None)
    t.add_argument("--sfx", default=None, help="Path to alarm sound file")

    # pomodoro
    p = sub.add_parser("pomodoro", aliases=["p"], help="Work/rest cycles")
    p.add_argument("-w", "--work", type=int, default=None, help="Work minutes")
    p.add_argument("-r", "--rest", type=int, default=None, help="Rest minutes")
    p.add_argument("-n", "--cycles", type=int, default=None)

    # stopwatch
    sub.add_parser("stopwatch", aliases=["sw"], help="Stopwatch with laps")

    # alarm
    a = sub.add_parser("alarm", aliases=["a"], help="Time-of-day alarm")
    a.add_argument("-H", "--hour", type=int, default=None)
    a.add_argument("-m", "--minute", type=int, default=None)
    a.add_argument("-s", "--second", type=int, default=None)
    a.add_argument("-t", "--title", default=None)
    a.add_argument("-c", "--caption", default=None)

    return parser


def interactive_menu():
    modes = {"1": ("Timer", run_timer), "2": ("Pomodoro", run_pomodoro),
             "3": ("Stopwatch", run_stopwatch), "4": ("Alarm", run_alarm)}
    print("── Clock ──")
    for key, (name, _) in modes.items():
        print(f"  {key}. {name}")
    choice = input("Select: ").strip()
    if choice in modes:
        modes[choice][1]()
    else:
        print("Invalid choice.")
        sys.exit(1)


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.mode is None:
            interactive_menu()
        elif args.mode in ("timer", "t"):
            run_timer(title=args.title, caption=args.caption, sfx=args.sfx,
                      hours=args.hours, minutes=args.minutes, seconds=args.seconds)
        elif args.mode in ("pomodoro", "p"):
            run_pomodoro(work=args.work, rest=args.rest, cycles=args.cycles)
        elif args.mode in ("stopwatch", "sw"):
            run_stopwatch()
        elif args.mode in ("alarm", "a"):
            run_alarm(title=args.title, caption=args.caption,
                      hour=args.hour, minute=args.minute, second=args.second)
    except KeyboardInterrupt:
        print("\nBye.")


if __name__ == "__main__":
    main()
