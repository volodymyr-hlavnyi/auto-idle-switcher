import subprocess
import time

IDLE_LIMIT = 20 * 60  # seconds
current_profile = "balanced"


def set_profile(profile, idle_seconds):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run(
        ["powerprofilesctl", "set", profile],
        check=True
    )
    print(f"[{ts}] Switched to {profile} (idle: {idle_seconds}s)")


def get_idle_seconds():
    out = subprocess.check_output(
        [
            "gdbus", "call",
            "--session",
            "--dest", "org.gnome.Mutter.IdleMonitor",
            "--object-path", "/org/gnome/Mutter/IdleMonitor/Core",
            "--method", "org.gnome.Mutter.IdleMonitor.GetIdletime"
        ],
        text=True
    ).strip()

    # output looks like: (uint64 12345,)
    ms = int(out.split()[1].strip(",)"))
    return ms // 1000


while True:
    idle = get_idle_seconds()

    if idle >= IDLE_LIMIT and current_profile != "power-saver":
        set_profile("power-saver", idle)
        current_profile = "power-saver"

    elif idle < 5 and current_profile != "balanced":
        set_profile("balanced", idle)
        current_profile = "balanced"

    time.sleep(5)
