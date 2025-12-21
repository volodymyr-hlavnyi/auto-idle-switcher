import os
import shutil
import subprocess
import time

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon

from config.config import AUTOSTART_FILE, BASE_DIR, AUTOSTART_DIR, APP_EXEC, settings

# ---- Shared state ----
current_profile = None


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
    print("Autostart enabled")


def disable_autostart():
    if os.path.exists(AUTOSTART_FILE):
        os.remove(AUTOSTART_FILE)
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

    # # update tray icon
    # if tray:
    #     tray.setIcon(icon)
    #
    # # update app + window icons
    # app.setWindowIcon(icon)
    # window_settings.setWindowIcon(icon)

    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] Switched to {profile} (idle {idle}s)")

    set_keyboard_color_for_mode(profile)
    print("Keyboard color set for mode:", profile)


def set_keyboard_color_for_mode(mode):
    if not is_asusctl_available():
        return
    kbd_cfg = settings.keyboard.get(mode)
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
