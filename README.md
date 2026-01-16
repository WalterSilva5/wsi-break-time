# Wsi Break Time

Windows app that reminds you to take breaks while working on your computer. Simple, effective, and lives in your system tray.

## Why?

Extended screen time causes eye strain, back pain, and fatigue. This tool interrupts you at regular intervals with a fullscreen overlay forcing you to actually take a break.

## Features

- Configurable break intervals (default: every 20 minutes)
- Fullscreen dark overlay with countdown
- Multiple random break messages
- Water drinking reminders
- Skip or postpone breaks when needed
- System tray integration
- Pre-break notifications
- Lightweight (~35MB)

## Download

Get the latest release from the [Releases](../../releases) page. No installation needed - just run `WsiBreakTime.exe`.

## Usage

1. Run `WsiBreakTime.exe`
2. Look for the "W" icon in your system tray
3. Right-click the icon to:
   - Pause/resume the timer
   - Take a break immediately
   - Open settings
   - Exit

### Settings

Double-click the tray icon or right-click → Settings to configure:

- **Break interval**: How often to pause (minutes)
- **Break duration**: How long each break lasts (seconds)
- **Messages**: Add/edit/remove break messages shown during pauses
- **Notifications**: Enable warnings before breaks start
- **Controls**: Allow skipping or postponing breaks
- **Water reminders**: Optional hydration alerts

### Keyboard Shortcuts

- `ESC` during a break: Skip the current break (if enabled)

## Building from Source

### Development

Requirements:
- Python 3.9+
- PyQt6

```bash
pip install -r requirements.txt
python run.py
```

### Building Executable

**Automated (Recommended):**

Windows:
```bash
build.bat
```

Linux/macOS:
```bash
chmod +x build.sh
./build.sh
```

Cross-platform (Python):
```bash
python build.py
python build.py --run  # Build and run
```

**Manual:**
```bash
pyinstaller build.spec
```

The executable will be in the `dist/` folder.

The automated scripts will:
- Check and install dependencies
- Clean previous builds
- Run basic tests
- Build the executable
- Verify the output

## Configuration

Settings are saved to `%APPDATA%\WsiBreakTime\config.json`. Delete this file to reset to defaults.

## License

MIT

## Contributing

Pull requests welcome. Keep it simple.
