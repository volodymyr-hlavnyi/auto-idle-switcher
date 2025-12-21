import sys

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer

from config.config import AUTOSTART_FILE, AUTOSTART_DIR, BASE_DIR, APP_EXEC
from config.config_service import load_settings, save_settings
from gui.base_app import APP_ICON, MainWindowAppGUI
from gui.helpers import icon_for_mode, get_idle_seconds, set_profile, get_current_profile, format_tooltip, \
    get_status_message, show_status_message

settings = load_settings()

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

menu = QMenu()
status_action = QAction(get_status_message())
menu.addAction(get_status_message(), window_settings.show)
menu.addSeparator()
menu.addAction("Settings", window_settings.show)
menu.addAction("Quit", app.quit)

tray.setContextMenu(menu)
tray.activated.connect(
    lambda reason: show_status_message(tray)
    if reason == QSystemTrayIcon.Trigger else None
)

tray.show()


# ---- Background timer ----
def tick():
    global last_idle_seconds

    idle = get_idle_seconds()
    last_idle_seconds = idle
    limit = settings.idle_minutes * 60

    if idle >= limit:
        set_profile(settings.idle_mode, idle)
    else:
        set_profile(settings.active_mode, idle)

    # keep UI in sync with real system state
    window_settings.refresh_current_mode_from_system()

    # update tray tooltip from real state
    current = get_current_profile()
    if current:
        tray.setToolTip(format_tooltip(current, idle))

    status_action.setText(get_status_message())


timer = QTimer()
timer.timeout.connect(tick)
timer.start(5000)  # every 5 seconds

sys.exit(app.exec())
