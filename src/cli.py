# src/cli.py
from pathlib import Path
import argparse
import logging
from datetime import datetime, timezone

import cv2
import numpy as np

from src.hardware.camera_manager import CameraManager
from src.hardware.exceptions import CameraError, FrameCaptureError
from src.hardware.frame_capture import FrameCapturer
from src.recorder import DataRecorder

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device-index",
        type=int,
        default=0,
        help="Index of the RealSense device to use (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path.cwd() / "recorded_sessions"),
        help="Directory where session folders will be created (default: %(default)s)",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Disable OpenCV preview windows while recording",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()

def _configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _render_depth_preview(depth_array: np.ndarray) -> np.ndarray:
    depth_clipped = np.clip(depth_array, 0, np.percentile(depth_array, 99))
    depth_normalized = cv2.normalize(
        depth_clipped, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U
    )
    return cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)


def main() -> int:
    args = parse_args()
    _configure_logging(args.log_level)

    logger.info("Starting RealSense camera recording session")
    logger.info("Using device index: %s", args.device_index)
    logger.info("Output directory: %s", args.output_dir)
    logger.info("Preview: %s", "enabled" if not args.no_preview else "disabled")
    logger.info("Log level: %s", args.log_level)

    camera_manager = CameraManager()

    try:
        camera_manager.connect(args.device_index)
    except CameraError as exc:
        logger.error("Camera initialization failed: %s", exc)
        return 1

    frame_capturer = FrameCapturer(camera_manager)
    recorder = DataRecorder()

    session_dir = recorder.create_session_directory(args.output_dir)
    logger.info("Recording to session directory: %s", session_dir)

    metadata = {
        "session_start": datetime.now(timezone.utc).isoformat(),
        "device_index": args.device_index,
        "camera_info": camera_manager.get_camera_info(),
        "log_level": args.log_level,
        "preview_enabled": not args.no_preview,
    }

    frame_idx = 0
    captured_frames = 0

    try:
        while True:
            rgb_frame, depth_frame = frame_capturer.capture_frame()
            recorder.save_frame_pair(frame_idx, rgb_frame, depth_frame, session_dir)

            captured_frames += 1
            frame_idx += 1

            if not args.no_preview:
                cv2.imshow("RealSense RGB", rgb_frame)
                cv2.imshow("RealSense Depth", _render_depth_preview(depth_frame))
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    logger.info("Preview exit key detected, stopping recording")
                    break

    except KeyboardInterrupt:
        logger.info("Recording interrupted by user")
    except FrameCaptureError as exc:
        logger.error("Frame capture error: %s", exc)
    finally:
        if not args.no_preview:
            cv2.destroyAllWindows()

        metadata["session_end"] = datetime.now(timezone.utc).isoformat()
        metadata["frame_count"] = captured_frames
        try:
            metadata["depth_scale"] = frame_capturer.get_depth_scale()
        except FrameCaptureError as exc:
            logger.warning("Failed to obtain depth scale: %s", exc)

        recorder.save_metadata(session_dir, metadata)
        camera_manager.disconnect()

    logger.info("Recording session complete - frames captured: %s", captured_frames)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())