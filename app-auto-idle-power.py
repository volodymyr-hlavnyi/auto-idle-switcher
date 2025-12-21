import sys

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer

from config.config_service import load_settings, save_settings
from gui.base_app import APP_ICON, MainWindowAppGUI
from gui.helpers import icon_for_mode, get_idle_seconds, set_profile, get_current_profile, format_tooltip, \
    get_status_message, show_status_message, get_keyboard_color_by_cpu_temp, apply_temperature_keyboard_rgb, \
    set_keyboard_color_for_mode
from gui.tabs import ui_setup_tray_menu

settings = load_settings()

# ---- Shared state ----
is_idle_state = False

# ---- App ----
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
if APP_ICON:
    app.setWindowIcon(QIcon(APP_ICON))

window_settings = MainWindowAppGUI()
window_settings.update_current_mode(settings.active_mode)

# tray = QSystemTrayIcon(QIcon.fromTheme("battery"))
# tray = QSystemTrayIcon(icon_for_mode(config["active_mode"]))
tray = QSystemTrayIcon(QIcon(APP_ICON) if APP_ICON else icon_for_mode(settings.active_mode))
tray.setToolTip("Auto Idle Power Switcher")

# menu = QMenu()
# status_action = QAction(get_status_message())
# menu.addAction(get_status_message(), window_settings.show)
# menu.addSeparator()
# menu.addAction("Settings", window_settings.show)
# menu.addAction("Quit", app.quit)
#
# tray.setContextMenu(menu)
# tray.activated.connect(
#     lambda reason: show_status_message(tray)
#     if reason == QSystemTrayIcon.Trigger else None
# )

ui_setup_tray_menu(window_settings, tray, app)

tray.show()


# ---- Background timer ----
def tick():
    global last_idle_seconds
    global is_idle_state

    idle = get_idle_seconds()
    last_idle_seconds = idle
    limit = settings.idle_minutes * 60

    if idle >= limit and not is_idle_state:
        set_profile(settings.idle_mode, idle)
        is_idle_state = True

    elif idle < limit and is_idle_state:
        set_profile(settings.active_mode, idle)
        is_idle_state = False

    # keep UI in sync with real system state
    window_settings.refresh_current_mode_from_system()

    current = get_current_profile()
    if current:
        tray.setIcon(icon_for_mode(current))
        tray.setToolTip(get_status_message())

    window_settings.update_current_mode(get_current_profile())

    print(f"idle={idle}s limit={limit}s is_idle_state={is_idle_state}")



timer = QTimer()
timer.timeout.connect(tick)
timer.start(5000)  # every 5 seconds

sys.exit(app.exec())
