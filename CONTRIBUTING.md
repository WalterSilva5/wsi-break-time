# Contributing to Wsi Break Time

Thanks for your interest in contributing. Here's how to get started.

## Development Setup

1. Fork and clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/wsi-break-time.git
cd wsi-break-time
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run in development mode
```bash
python run.py
```

## Project Structure

```
wsi-break-time/
├── src/
│   ├── main.py          # Entry point
│   ├── app.py           # Main application logic
│   ├── settings.py      # Configuration management
│   ├── timer_manager.py # Break timer logic
│   ├── tray_icon.py     # System tray integration
│   └── overlay.py       # Fullscreen break overlay
├── resources/           # Icons and sounds
├── build.py             # Cross-platform build script
├── build.bat            # Windows build script
├── build.sh             # Linux/macOS build script
└── build.spec           # PyInstaller configuration
```

## Making Changes

1. Create a new branch
```bash
git checkout -b feature-name
```

2. Make your changes
   - Keep code simple and readable
   - Maintain existing code style
   - Test your changes

3. Build and test
```bash
python build.py --run
```

4. Commit with a clear message
```bash
git commit -m "Add: description of feature"
```

5. Push and create a pull request
```bash
git push origin feature-name
```

## Build Scripts

Three build scripts are available:

### `build.py` (Recommended)
Cross-platform Python script with the most features:
```bash
python build.py          # Standard build
python build.py --run    # Build and run immediately
```

### `build.bat` (Windows)
Batch script for Windows users:
```bash
build.bat
```

### `build.sh` (Linux/macOS)
Shell script for Unix systems:
```bash
chmod +x build.sh
./build.sh
```

All scripts will:
- Check Python version
- Install missing dependencies
- Clean old builds
- Run basic tests
- Build executable
- Report size and location

## Code Guidelines

- Use docstrings for classes and non-obvious functions
- Keep functions short and focused
- Avoid unnecessary comments (code should be self-explanatory)
- Use type hints where helpful
- Test on Windows 10/11

## Testing

Currently manual testing. Automated tests coming soon.

Test checklist:
- [ ] App starts and shows in system tray
- [ ] Settings dialog opens and saves
- [ ] Break overlay shows fullscreen
- [ ] Timer counts down correctly
- [ ] Skip/postpone work as expected
- [ ] Messages display randomly

## Release Process

Maintainers only:

1. Update version in `src/__init__.py`
2. Build executable: `python build.py`
3. Test the built executable
4. Create git tag: `git tag v1.x.x`
5. Push tag: `git push --tags`
6. Create GitHub release with executable

## Questions?

Open an issue or discussion on GitHub.
