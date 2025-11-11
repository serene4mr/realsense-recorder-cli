# RealSense Recorder CLI

Intel RealSense recording helper for RGB + depth sessions.

## Features
- Auto-discovers a RealSense camera and applies the fixed capture profile.
- Saves aligned RGB/depth frames plus metadata in timestamped session directories.
- Optional live preview with depth colormap for quick sanity checks.

## Requirements
- Python 3.10+
- Intel RealSense SDK (`pyrealsense2`)
- `opencv-python`, `numpy`

Install dependencies:
```
pip install -r requirements.txt
```
*(Or install the packages manually if you already have the RealSense SDK set up.)*

## Usage
From the repo root:
```
python -m src.cli
```

Useful flags:
- `--device-index` RealSense device to use (default `0`)
- `--output-dir` Base dir for session folders (default `./recorded_sessions`)
- `--no-preview` Disable OpenCV preview windows
- `--log-level` Logging verbosity (`DEBUG`..`CRITICAL`)

`Ctrl+C`, `q`, or `Esc` stops the session. Captured data lives in the session folder the CLI prints.

## Structure
- `src/hardware/`: camera management, frame capture, custom exceptions
- `src/recorder.py`: disk persistence for frames/metadata
- `src/cli.py`: command-line entry point and control loop

## Troubleshooting
- **Cannot import `pyrealsense2`**: ensure the RealSense SDK is installed and Python bindings are in your environment.
- **No devices found**: confirm the camera is plugged in and accessible (check `rs-enumerate-devices`).
- **Permission denied**: set up udev rules for RealSense or run with appropriate permissions.
# realsense-recorder-cli
