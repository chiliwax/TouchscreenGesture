# TouchGesture

A lightweight Python-based daemon for detecting and responding to touchscreen gestures on X11/Linux systems. TouchGesture enables users to define custom gestures such as hold, pinch, or swipe and bind them to actions like right-click, keyboard shortcuts, or shell commands.

## Features

- 🔧 **Configurable Gestures**
  - Hold (e.g., one-finger hold = right-click)
  - Pinch (in/out detection)
  - Customizable number of fingers, duration, and thresholds

- 🎯 **Action Support**
  - Mouse event simulation (clicks, scrolling)
  - Keyboard shortcut simulation
  - Shell command execution

- 📱 **Device Support**
  - Automatic touchscreen detection
  - Support for multiple input devices
  - Configurable device selection

- ⚙️ **Configuration**
  - System-wide and per-user configuration
  - YAML-based configuration format
  - Debug logging support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/touchgesture.git
cd touchgesture
```

2. Run the installation script as root:
```bash
sudo ./install.sh
```

3. Log out and log back in for group changes to take effect.

## Usage

Start the daemon:
```bash
touchgesture
```

### Configuration

The default configuration is installed at `/etc/touchgesture/default.yaml`. You can create a user-specific configuration at `~/.config/touchgesture/config.yaml`.

Example configuration:
```yaml
# Device configuration
devices:
  - name: "touchscreen"  # Will match any device with "touchscreen" in its name
  # - event_id: 5  # Alternative: specific event ID

# Gesture configurations
gestures:
  hold:
    enabled: true
    fingers: 1
    duration: 0.5  # seconds
    action: "right_click"
  
  pinch:
    enabled: true
    action: "zoom"

# Action mappings
actions:
  right_click:
    type: "mouse"
    button: "right"
    event: "click"
  
  zoom:
    type: "keyboard"
    in: "ctrl+plus"
    out: "ctrl+minus"
```

## Project Structure

```
├── config/
│   ├── default.yaml                # System-wide configuration
│   └── users/                      # User-specific configurations
├── gestures/
│   ├── base.py                     # Base gesture detection class
│   ├── hold.py                     # Hold gesture implementation
│   └── pinch.py                    # Pinch gesture implementation
├── input/
│   └── listener.py                 # Input event monitoring
├── touchgesture.py                 # Main executable
├── install.sh                      # Installation script
└── requirements.txt                # Python dependencies
```

## Dependencies

- Python 3.6+
- python-evdev
- xdotool
- PyYAML
- python-xlib

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [python-evdev](https://github.com/gvalkov/python-evdev) for input device handling
- [xdotool](https://github.com/jordansissel/xdotool) for X11 automation
