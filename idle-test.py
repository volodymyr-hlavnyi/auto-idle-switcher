import subprocess
import time

SESSION_ID = "5"  # your session ID

def get_idle_seconds():
    out = subprocess.check_output(
        ["loginctl", "show-session", SESSION_ID, "-p", "IdleSinceHint"],
        text=True
    ).strip()

    idle_us = int(out.split("=")[1])
    now_us = int(time.time() * 1_000_000)

    return max(0, (now_us - idle_us) // 1_000_000)

while True:
    idle = get_idle_seconds()
    print(f"Idle for {idle} seconds")
    time.sleep(5)
