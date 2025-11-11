# src/hardware/frame_capture.py
import logging

import numpy as np
import pyrealsense2 as rs

from src.hardware.camera_manager import CameraManager
from src.hardware.exceptions import FrameCaptureError

logger = logging.getLogger(__name__)

class FrameCapturer:
    """
    Captures and aligns RGB and depth frames from RealSense camera.
    
    Handles:
    - Frame acquisition from pipeline
    - Depth-to-RGB alignment
    - Data conversion to numpy arrays
    - Frame timing and counting
    """

    DEFAULT_DEPTH_SCALE = 0.001

    def __init__(self, camera_manager: CameraManager):
        """
        Initialize frame capturer.
        
        Args:
            camera_manager: Connected CameraManager instance

        """
        if not camera_manager.is_connected():
            raise ValueError("CameraManager must be connected before FrameCapturer")
        
        self.camera_manager = camera_manager
        self.pipeline = camera_manager.pipeline

        # Initialize alignment (align depth to color frame)
        self.align = rs.align(rs.stream.color)

        self.frame_count = 0
        self._depth_scale: float | None = None
        logger.info("FrameCapturer initialized")

    def capture_frame(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Capture one aligned RGB-depth frame pair.
        
        Returns:
            tuple: (rgb_frame, depth_frame) as numpy arrays
                - rgb_frame: shape (H, W, 3), dtype uint8, BGR format
                - depth_frame: shape (H, W), dtype uint16, mm

        """

        try:

            # Wait for frames (timeout prevents hanging)
            frames = self.pipeline.wait_for_frames(timeout_ms=1000)

            if not frames:
                raise FrameCaptureError("Received empty frameset")
            
            # Apply alignment (depth → color coordinate system)
            aligned_frames = self.align.process(frames)

            # Extract aligned frames
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
            
            # Validate frames exist
            if not color_frame or not depth_frame:
                raise FrameCaptureError("Missing aligned frames")
            
            # Convert to numpy arrays
            # Copy buffers so data persists after RealSense frame objects are released
            rgb_array = np.asanyarray(color_frame.get_data()).copy()  # (H, W, 3)
            depth_array = np.asanyarray(depth_frame.get_data()).copy()  # (H, W)
            
            # Increment counter
            self.frame_count += 1
            
            return rgb_array, depth_array


        except RuntimeError as e:
            # Timeout or SDK error
            if "timeout" in str(e).lower():
                raise FrameCaptureError(f"Frame capture timeout: {e}")
            else:
                raise FrameCaptureError(f"Frame capture failed: {e}")

        except Exception as e:
            raise FrameCaptureError(f"Unexpected error capturing frame: {e}")

    def get_frame_count(self):
        """
        Get total frames captured since initialization.
        
        Returns:
            int: Frame count
        """
        return self.frame_count
    
    def get_depth_scale(self):
        """
        Get depth scale factor for converting depth values to meters.
        
        Returns:
            float: Depth scale (typically 0.001 for millimeter sensor)
        
        Example:
            depth_in_meters = depth_array * capturer.get_depth_scale()
        """
        if self._depth_scale is not None:
            return self._depth_scale

        try:
            depth_sensor = self.camera_manager.device.first_depth_sensor()
            self._depth_scale = float(depth_sensor.get_depth_scale())
            return self._depth_scale
        except Exception as e:
            message = f"Could not get depth scale: {e}"
            if self.DEFAULT_DEPTH_SCALE is None:
                logger.error(message)
                raise FrameCaptureError(message) from e

            logger.warning(
                f"{message}. Falling back to default value {self.DEFAULT_DEPTH_SCALE}"
            )
            self._depth_scale = self.DEFAULT_DEPTH_SCALE
            return self._depth_scale
    
    def get_depth_intrinsics(self):
        """
        Get depth camera intrinsic parameters.
        
        Returns:
            dict: Intrinsics (fx, fy, cx, cy, width, height)
        """
        try:
            depth_profile = self.pipeline.get_active_profile().get_stream(rs.stream.depth)
            intr = depth_profile.as_video_stream_profile().get_intrinsics()
            
            return {
                'fx': intr.fx,
                'fy': intr.fy,
                'cx': intr.ppx,
                'cy': intr.ppy,
                'width': intr.width,
                'height': intr.height,
            }
        except Exception as e:
            logger.error(f"Could not get depth intrinsics: {e}")
            return {}
    
    def get_rgb_intrinsics(self):
        """
        Get RGB camera intrinsic parameters.
        
        Returns:
            dict: Intrinsics (fx, fy, cx, cy, width, height)
        """
        try:
            color_profile = self.pipeline.get_active_profile().get_stream(rs.stream.color)
            intr = color_profile.as_video_stream_profile().get_intrinsics()
            
            return {
                'fx': intr.fx,
                'fy': intr.fy,
                'cx': intr.ppx,
                'cy': intr.ppy,
                'width': intr.width,
                'height': intr.height,
            }
        except Exception as e:
            logger.error(f"Could not get RGB intrinsics: {e}")
            return {}




        

