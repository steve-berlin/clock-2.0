import subprocess as sp

h = input("Provide hour: ")
m = input("Provide minute: ")
day = input("Today or tomorrow (t/tm): ")
if day == "t":
    # sudo rtcwake -m mem -l -t $(date +%s -d 'today 12:00')
    sp.call(
        ["sudo", "rtcwake", "-m", "mem", "-l", "-t", f"$(date +%s -d 'today {h}:{m}')"]
    )
elif day == "tm":
    # sudo rtcwake -m mem -l -t $(date +%s -d 'tomorrow 12:00')
    sp.call(
        [
            "sudo",
            "rtcwake",
            "-m",
            "mem",
            "-l",
            "-t",
            f"$(date +%s -d 'tomorrow {h}:{m}')",
        ]
    )
