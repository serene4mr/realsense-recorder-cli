# src/hardware/camera_manager.py
import logging
from typing import Dict, List, Optional
import pyrealsense2 as rs

from src.hardware.exceptions import (
    CameraConnectionError,
    CameraConfigError
)

logger = logging.getLogger(__name__)

class CameraManager:
    """
    Manages Intel RealSense D456 camera connection and configuration.
    Provides a clean interface for pipeline initialization and device management.
    """

    # Fixed stream configuration (class constants)
    RGB_WIDTH = 1280
    RGB_HEIGHT = 800
    RGB_FPS = 30
    RGB_FORMAT = rs.format.bgr8  # BGR for OpenCV compatibility
    
    DEPTH_WIDTH = 1280
    DEPTH_HEIGHT = 720
    DEPTH_FPS = 30
    DEPTH_FORMAT = rs.format.z16  # 16-bit depth

    def __init__(self):

        self.pipeline: Optional[rs.pipeline] = None
        self.config: Optional[rs.config] = None
        self.device: Optional[rs.device] = None

    def enumerate_devices(self) -> List[Dict[str, str]]:
        """
        Enumerate all connected RealSense devices.

        Returns:
            list: List of device info dictionaries

        Example:
            devices = camera_manager.enumerate_devices()
            # [
            #   {'name': 'Intel RealSense D456', 'serial': '123456', 'firmware': '5.12.5'},
            #   ...
            # ]
        """
        try:
            context = rs.context()
            devices = []

            for dev in context.devices:
                device_info = {
                    'name': dev.get_info(rs.camera_info.name),
                    'serial': dev.get_info(rs.camera_info.serial_number),
                    'firmware': dev.get_info(rs.camera_info.firmware_version),
                    'product_id': dev.get_info(rs.camera_info.product_id),
                }
                devices.append(device_info)

            logger.info(f"Found {len(devices)} RealSense device(s)")
            return devices


        except Exception as e:
            logger.error(f"Failed to enumerate devices: {e}")
            return []

    def connect(self, device_index: int = 0):
        """
        Connect to and initialize a RealSense device.


        Args:
            device_index (int): Index of device to connect (0 for first device)

        """
        try:
            # check if device exists
            devices = self.enumerate_devices()
            if not devices:
                raise CameraConnectionError("No RealSense devices detected")
            
            if device_index >= len(devices):
                raise CameraConnectionError(
                    f"Device index {device_index} out of range "
                    f"(found {len(devices)} device(s))"
                )
            
            # Initialize pipeline
            self.pipeline = rs.pipeline()
            self.config = rs.config()

            target_device = devices[device_index]
            self.config.enable_device(target_device["serial"])

            # Configure streams
            self._configure_streams()

            # Start pipeline
            profile = self.pipeline.start(self.config)

            # Get device and camera info
            self.device = profile.get_device()

        except Exception as e:
            logger.error(f"Camera connection failed: {e}")
            raise CameraConnectionError(f"Failed to connect: {str(e)}")
    
    def disconnect(self):
        """Disconnect from camera and release resources"""
        try:
            if self.pipeline:
                self.pipeline.stop()
            self.pipeline = None
            self.config = None
            self.device = None
            logger.info("Camera disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def is_connected(self):
        """Check if camera is connected"""
        return self.pipeline is not None

    def get_intrinsics(self):
        """Get camera intrinsic parameters"""
        if not self.is_connected():
            logger.warning("Camera not connected")
            return {}
        
        try:
            color_profile = self.pipeline.get_active_profile().get_stream(rs.stream.color)
            depth_profile = self.pipeline.get_active_profile().get_stream(rs.stream.depth)
            
            color_intr = color_profile.as_video_stream_profile().get_intrinsics()
            depth_intr = depth_profile.as_video_stream_profile().get_intrinsics()
            
            return {
                'color': {
                    'width': color_intr.width,
                    'height': color_intr.height,
                    'fx': color_intr.fx,
                    'fy': color_intr.fy,
                    'ppx': color_intr.ppx,
                    'ppy': color_intr.ppy,
                },
                'depth': {
                    'width': depth_intr.width,
                    'height': depth_intr.height,
                    'fx': depth_intr.fx,
                    'fy': depth_intr.fy,
                    'ppx': depth_intr.ppx,
                    'ppy': depth_intr.ppy,
                }
            }
        except Exception as e:
            logger.error(f"Failed to get intrinsics: {e}")
            return {}
    
    def _configure_streams(self):
        """Configure RGB and depth streams with fixed optimal settings"""
        try:
            self.config.enable_stream(
                rs.stream.color,
                self.RGB_WIDTH,
                self.RGB_HEIGHT,
                rs.format.bgr8,
                self.RGB_FPS
            )
            
            # Depth stream
            self.config.enable_stream(
                rs.stream.depth,
                self.DEPTH_WIDTH,
                self.DEPTH_HEIGHT,
                rs.format.z16,
                self.DEPTH_FPS
            )
            
            logger.info(
                f"Streams configured: "
                f"RGB {self.RGB_WIDTH}x{self.RGB_HEIGHT}@{self.RGB_FPS}fps, "
                f"Depth {self.DEPTH_WIDTH}x{self.DEPTH_HEIGHT}@{self.DEPTH_FPS}fps"
            )

        except Exception as e:
            logger.error("Stream configuration failed: %s", e)
            raise CameraConfigError(f"Stream configuration failed: {e}") from e

    def get_camera_info(self):
        """Get camera metadata"""
        if not self.is_connected() or self.device is None:
            logger.warning("Camera not connected")
            return {}
        try:
            return {
                'name': self.device.get_info(rs.camera_info.name),
                'serial': self.device.get_info(rs.camera_info.serial_number),
                'firmware': self.device.get_info(rs.camera_info.firmware_version),
                'product_id': self.device.get_info(rs.camera_info.product_id),
            }
        except Exception as e:
            logger.warning(f"Could not fetch full camera info: {e}")
            return {}

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False




            

        


        


    