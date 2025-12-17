# Auto Idle Power Switcher

A lightweight GNOME tray application for Ubuntu that automatically switches
power profiles based on user idle time.

## Features

- Automatic power profile switching based on idle time
- GNOME tray icon with live status
- Manual override detection (syncs with system power settings)
- Configurable idle timeout
- Autostart toggle
- Clean uninstall
- Native `.deb` installer for Ubuntu 24.04

## Screenshots

### Tray icon and status
![Tray icon](screenshots/tray.png)

### Settings window
![Settings window](screenshots/settings.png)

### About tab
![About tab](screenshots/about.png)

## Installation

Download the latest `.deb` from **GitHub Releases** and install:

```bash
sudo dpkg -i auto-idle_0.1.0.deb
sudo apt -f install
```

## Usage

Launch from Applications menu or run:
```bash
auto-idle
```

## Settings are available from the tray icon.

Requirements

 - Ubuntu 24.04 (GNOME, Wayland)
 - power-profiles-daemon

## Author

Volodymyr Hlavnyi (2025)
https://github.com/volodymyr-hlavnyi

## License

MIT
