import os
import shutil
import subprocess
import time

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMessageBox

from config.config import AUTOSTART_FILE, BASE_DIR, AUTOSTART_DIR, APP_EXEC, settings

last_kbd_mode = None
current_profile = None
last_temp_color = None


def is_autostart_enabled():
    return os.path.exists(AUTOSTART_FILE)


def is_asusctl_available():
    return shutil.which("asusctl") is not None


def icon_path_for_mode(mode):
    ICON_GREEN = os.path.join(BASE_DIR, "icons", "battery_green.svg")
    ICON_YELLOW = os.path.join(BASE_DIR, "icons", "battery_yellow.svg")
    ICON_RED = os.path.join(BASE_DIR, "icons", "battery_red.svg")

    icons_path = {
        "power-saver": ICON_GREEN,
        "balanced": ICON_YELLOW,
        "performance": ICON_RED,
    }
    return icons_path.get(mode)


def icon_for_mode(mode):
    path = icon_path_for_mode(mode)
    if path and os.path.exists(path):
        return QIcon(path)
    return QIcon()


def enable_autostart():
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    with open(AUTOSTART_FILE, "w") as f:
        f.write(
            f"""[Desktop Entry]
            Type=Application
            Name=Auto Idle Power Switcher
            Comment=Automatically switch power profiles based on idle time
            Exec={APP_EXEC}
            Icon={icon_path_for_mode("balanced")}
            Terminal=false
            X-GNOME-Autostart-enabled=true
            """)
    # QMessageBox.information(
    #     None,
    #     "Autostart enabled",
    #     "Auto Idle Power Switcher will start automatically on login."
    # )
    print("Autostart enabled")


def disable_autostart():
    if os.path.exists(AUTOSTART_FILE):
        os.remove(AUTOSTART_FILE)
        # QMessageBox.information(
        #     None,
        #     "Autostart disabled",
        #     "Auto Idle Power Switcher will not start automatically on login."
        # )
        print("Autostart disabled")


def format_tooltip(profile, idle_seconds):
    mins = idle_seconds // 60
    return (
        "Auto Idle Power Switcher\n"
        f"Mode: {profile}\n"
        f"Idle: {mins} min"
    )


def show_status_message(tray):
    profile = get_current_profile() or "unknown"
    mins = settings.last_idle_seconds // 60

    tray.showMessage(
        "Auto Idle Power Switcher",
        f"Mode: {profile}\nIdle: {mins} min",
        QSystemTrayIcon.Information,
        3000
    )


def get_status_message():
    profile = get_current_profile() or "unknown"

    return f"Mode: {profile}"


def get_current_profile():
    try:
        out = subprocess.check_output(
            ["powerprofilesctl", "get"],
            text=True
        ).strip()
        return out
    except Exception as e:
        print("Failed to get current profile:", e)
        return None


# ---- System helpers ----
def get_idle_seconds():
    try:
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
        # expected format like "(uint64 12345,)"
        parts = out.split()
        if len(parts) >= 2:
            ms = int(parts[1].strip(",)"))
            return ms // 1000
    except Exception as e:
        print("get_idle_seconds failed:", e)
    return 0


def set_profile(profile, idle):
    global current_profile
    if current_profile == profile:
        return

    try:
        subprocess.run(
            ["powerprofilesctl", "set", profile],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Failed to set profile:", e)
        return

    current_profile = profile

    icon = icon_for_mode(profile)

    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] Switched to {profile} (idle {idle}s)")

    set_keyboard_color_for_mode(profile)
    print("Keyboard color set for mode:", profile)


def set_keyboard_color_for_mode(mode):
    global last_kbd_mode

    if not is_asusctl_available():
        return
    if not settings.keyboard.get("enabled", True):
        return
    if last_kbd_mode == mode:
        return  # ← STOP reapplying every 5 seconds

    kbd_cfg = settings.keyboard["modes"].get(mode)
    if not kbd_cfg:
        return

    color = kbd_cfg.get("color", "").lower()
    brightness = kbd_cfg.get("brightness", "med")

    # basic validation: 6 hex chars
    if len(color) != 7 or not all(c in "#0123456789abcdef" for c in color):
        print(f"Invalid HEX color for {mode}: {color}")
        return

    try:
        # set color
        subprocess.run(
            ["asusctl", "aura", "static", "-c", color.replace("#", "")],
            check=True
        )

        # set brightness
        subprocess.run(
            ["asusctl", "-k", brightness],
            check=True
        )

        print(
            f"Keyboard set for {mode}: "
            f"{color.upper()}, brightness={brightness}"
        )

    except Exception as e:
        print("Failed to set keyboard RGB:", e)


def get_keyboard_color_by_cpu_temp() -> str | None:
    """
    Returns HEX color (with #) based on current CPU temperature,
    or None if temperature RGB is disabled.
    """
    if not settings.temperature_rgb.get("enabled"):
        return None

    try:
        temp_c = read_cpu_temperature()
        print("Current CPU temperature:", temp_c)
    except Exception as e:
        print("Failed to read CPU temperature:", e)
        return None

    points = settings.temperature_rgb["points"]

    # keys are strings like "30", "40", ...
    thresholds = sorted(int(t) for t in points.keys())

    selected = thresholds[0]
    for t in thresholds:
        if temp_c >= t:
            selected = t
        else:
            break

    return points[str(selected)]


def apply_temperature_keyboard_rgb():
    global last_temp_color

    color = get_keyboard_color_by_cpu_temp()
    if not color:
        last_temp_color = None
        return

    if color == last_temp_color:
        return  # nothing changed, do not spam asusctl

    try:
        subprocess.run(
            ["asusctl", "aura", "static", "-c", color.replace("#", "")],
            check=True
        )
        last_temp_color = color
    except Exception as e:
        print("Failed to apply temperature RGB:", e)


def read_cpu_temperature() -> int | None:
    base = "/sys/class/thermal"

    for zone in os.listdir(base):
        type_path = os.path.join(base, zone, "type")
        temp_path = os.path.join(base, zone, "temp")

        try:
            with open(type_path) as f:
                if f.read().strip() == "x86_pkg_temp":
                    with open(temp_path) as tf:
                        return int(tf.read().strip()) // 1000
        except OSError:
            continue

    return None
