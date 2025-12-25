## 📦 Download

**auto-idle_0.1.3.deb**

Direct download:
https://github.com/volodymyr-hlavnyi/auto-idle-switcher/releases/download/v0.1.3/auto-idle_0.1.3.deb

Install on Ubuntu / Debian:
```bash
sudo dpkg -i auto-idle_0.1.3.deb
sudo apt -f install
```

Run:
```bash
auto-idle
```

---

## ✨ Auto Idle Power Switcher v0.1.3

A stable release of **Auto Idle Power Switcher** for GNOME-based systems, designed primarily for **ASUS ROG laptops**.

### Features
- Automatic power profile switching based on user idle time
- GNOME system tray application with settings UI
- ASUS ROG keyboard RGB synchronization  
  - Power mode–based colors  
  - Temperature-based RGB mode
- Autostart support

### Technical details
- Built with **PyQt6** (single Qt binding)
- Uses **system Python** and **apt-managed dependencies**
- Debian/Ubuntu–compatible `.deb` package
- No virtualenv, no pip installs at runtime
- Compatible with **Ubuntu 24.04 (Noble)**

### Dependencies (installed automatically)
- `python3`
- `python3-pyqt6`
- `python3-pydantic`
- `power-profiles-daemon`
- `libglib2.0-bin`

### Notes
- Tested on Ubuntu 24.04 GNOME
- Requires `power-profiles-daemon` to be enabled
- Targeted at laptops with supported ASUS ROG keyboards

---

If you encounter issues, please report them via GitHub Issues.
