from pathlib import Path
import logging
import os
import json
import numpy as np
import cv2
from datetime import datetime

logger = logging.getLogger(__name__)

class DataRecorder:
    """
    Records RGB-depth frame pairs to disk.
    """
    
    def __init__(self):
        """Initialize data recorder."""
        logger.info("DataRecorder initialized")

    def create_session_directory(self, base_dir):
        """
        Create timestamped session directory.
        
        Args:
            base_dir: str or Path, base output directory
        
        Returns:
            str, path to created session directory
        
        Example:
            session_dir = storage.create_session_directory("data/recorded_sessions")
            # Returns: "data/recorded_sessions/session_20251110_015430"
        """
        base_path = Path(base_dir).expanduser()
        base_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"session_{timestamp}"
        session_dir = base_path / session_name

        # Create subdirectories
        rgb_dir = session_dir / "rgb"
        depth_dir = session_dir / "depth"

        rgb_dir.mkdir(parents=True, exist_ok=True)
        depth_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created session directory: {session_dir}")
        return str(session_dir)
    
    def save_frame_pair(self, frame_idx, rgb_array, depth_array, session_dir):
        """
        Save aligned RGB-depth frame pair.
        
        Args:
            frame_idx: int, frame index (0-based)
            rgb_array: numpy array (H, W, 3), uint8
            depth_array: numpy array (H, W), uint16
            session_dir: str or Path, session directory path
        
        Returns:
            dict: paths to saved files
        
        Example:
            paths = storage.save_frame_pair(0, rgb, depth, "./session_001")
            print(paths['rgb'])    # "./session_001/rgb/frame_000000_rgb.png"
            print(paths['depth'])  # "./session_001/depth/frame_000000_depth.npy"
        """
        session_path = Path(session_dir)
        rgb_dir = session_path / "rgb"
        depth_dir = session_path / "depth"

        if rgb_array.dtype != np.uint8 or rgb_array.ndim != 3 or rgb_array.shape[2] != 3:
            raise ValueError("rgb_array must be an HxWx3 uint8 array.")

        if depth_array.dtype != np.uint16 or depth_array.ndim != 2:
            raise ValueError("depth_array must be an HxW uint16 array.")

        rgb_dir.mkdir(parents=True, exist_ok=True)
        depth_dir.mkdir(parents=True, exist_ok=True)

        # Generate filenames
        rgb_filename = f"frame_{frame_idx:06d}_rgb.png"
        depth_filename = f"frame_{frame_idx:06d}_depth.npy"

        rgb_path = rgb_dir / rgb_filename
        depth_path = depth_dir / depth_filename

        # Save RGB as PNG
        if not cv2.imwrite(str(rgb_path), rgb_array):
            raise IOError(f"Failed to write RGB frame to {rgb_path}")

        # Save depth as NPY (preserves uint16, millimeter precision)
        np.save(str(depth_path), depth_array)

        logger.debug(f"Saved frame {frame_idx}: RGB={rgb_filename}, Depth={depth_filename}")

        return {
            'rgb': str(rgb_path),
            'depth': str(depth_path)
        }
    
    def save_metadata(self, session_dir, metadata):
        """
        Save session metadata as JSON.
        
        Args:
            session_dir: str or Path, session directory
            metadata: dict, metadata to save
        
        Example:
            metadata = {
                'frame_count': 150,
                'camera_serial': '123456',
                'timestamp': '2025-11-10T01:54:30',
                'fps': 30
            }
            storage.save_metadata(session_dir, metadata)
        """
        metadata_path = Path(session_dir) / "metadata.json"

        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        except TypeError:
            logger.exception("Failed to serialize session metadata")
            raise

        logger.info(f"Saved metadata to {metadata_path}")