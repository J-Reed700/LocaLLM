import platform
import torch
import psutil
import logging
from dataclasses import dataclass

@dataclass
class SystemCapabilities:
    device_type: str  # cuda, mps, cpu
    architecture: str  # arm64, x86_64
    total_memory_gb: float
    platform_name: str  # Darwin, Linux, Windows
    supports_half_precision: bool

class SystemInfo:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_capabilities(self) -> SystemCapabilities:
        try:
            # Determine device type
            if torch.cuda.is_available():
                device_type = "cuda"
                supports_half = True
            elif torch.backends.mps.is_available():
                device_type = "mps"
                supports_half = True
            else:
                device_type = "cpu"
                supports_half = False

            # Get system architecture
            architecture = platform.machine()
            
            # Get total system memory in GB
            total_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
            
            # Get platform
            platform_name = platform.system()

            return SystemCapabilities(
                device_type=device_type,
                architecture=architecture,
                total_memory_gb=total_memory_gb,
                platform_name=platform_name,
                supports_half_precision=supports_half
            )
        except Exception as e:
            self.logger.error(f"Error getting system capabilities: {e}")
            return None 