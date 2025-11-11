# hardware/exceptions.py

class CameraError(Exception):
    """
    Base exception for all camera-related errors.
    Allows catching any camera error with a single except block.
    """
    pass


class CameraConnectionError(CameraError):
    """
    Raised when camera connection fails.
    
    Examples:
    - No device found
    - Device unplugged during operation
    - USB permission denied
    - Incompatible device connected
    """
    pass


class CameraConfigError(CameraError):
    """
    Raised when camera configuration fails.
    
    Examples:
    - Invalid stream resolution
    - Unsupported FPS
    - Stream format not available
    """
    pass


class FrameCaptureError(CameraError):
    """
    Raised when frame capture fails.
    
    Examples:
    - Timeout waiting for frames
    - Corrupted frame data
    - Alignment failure
    """
    pass
