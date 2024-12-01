from src.utils.system_capabilities import SystemInfo
from huggingface_hub import HfApi, ModelCardData
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
from src.models.enum import ModelType
from websrc.config.settings import settings
import os
from typing import Any
import shutil
from huggingface_hub import snapshot_download
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import datetime
from src.services.database_context import DatabaseContext
from src.services.storage_service import SecureStorageService
from pathlib import Path
from src.repositories.model_repository import ModelRepository
from src.models.database import ModelInfo
from exceptions.exceptions import NotFoundError
from src.models.dto import ModelInfoDTO
from datetime import timezone
from exceptions.exceptions import NotEnoughDiskSpaceError, ModelDownloadError


class ModelDiscoveryService:
    def __init__(self, db_context: DatabaseContext, storage: SecureStorageService):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.hf_api = HfApi(token=False)
        self.system_info = SystemInfo()
        self.capabilities = self.system_info.get_capabilities()
        self.storage = storage
        self.db_context = db_context
        self._executor = ThreadPoolExecutor(max_workers=1)
        self.model_cache_dir = os.getenv("MODEL_CACHE_DIR", "/src/cache/models")

    def _check_model_compatibility(self, model_info: ModelCardData) -> bool:
        try:
            if not model_info or not hasattr(model_info, 'model_dump'):
                self.logger.debug("No model card data available, assuming compatible")
                return True
                
            card_data = model_info.model_dump()
            
            # Check memory requirements
            if "memory_requirements" in card_data:
                try:
                    required_memory = float(card_data["memory_requirements"].replace("GB", ""))
                    if required_memory > self.capabilities.total_memory_gb:
                        return False
                except (ValueError, AttributeError):
                    self.logger.debug("Invalid memory requirement format, skipping check")
                    
            # More lenient architecture check for ARM
            if "architectures" in card_data:
                if self.capabilities.architecture == "arm64":
                    if "arm64_incompatible" in card_data.get("tags", []):
                        return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking model compatibility: {e}")
            return True  # Be permissive on errors

    async def get_available_models(self, model_type: ModelType) -> List[dict]:
        try:
            # Get models from both local and remote sources
            remote_models = await self._get_remote_models(model_type)
            
            # Convert DTOs to dictionaries before returning
            return [model.to_dict() for model in remote_models]
            
        except Exception as e:
            self.logger.error(f"Failed to fetch models: {str(e)}")
            raise

    async def _get_remote_models(self, model_type: ModelType) -> List[ModelInfoDTO]:
        try:
            # Define search parameters
            tags = ["text-generation"] if model_type == ModelType.TEXT else ["image-generation"]
            
            # Get models from HuggingFace using run_in_executor
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(
                self._executor,
                lambda: self.hf_api.list_models(
                    filter=tags,
                    sort="downloads",
                    direction=-1,
                    limit=20
                )
            )
            
            available_models = []
            for model in models:
                # Store the compatibility check result
                is_compatible = self._check_model_compatibility(model.card_data)
                
                model_info = ModelInfoDTO.from_huggingface(model)
                # Add the compatibility status to the model info
                model_info.compatible = is_compatible
                available_models.append(model_info)
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"Error fetching remote models: {str(e)}")
            raise

    def _get_model_requirements(self, card_data: Optional[ModelCardData]) -> Dict[str, str]:
        """Extract model requirements from card data"""
        if not card_data:
            return {
                "memory": "Unknown",
                "gpu": "Unknown",
                "disk": "Unknown"
            }
        
        return {
            "memory": card_data.get("memory_requirements", "Unknown"),
            "gpu": card_data.get("gpu_requirements", "Unknown"),
            "disk": card_data.get("disk_requirements", "Unknown")
        }

    async def download_model(self, model_id: str, model_type: ModelType) -> None:
        try:
            # Create temporary directory if it doesn't exist
            temp_dir = Path("data/models") 
            temp_dir.mkdir(parents=True, exist_ok=True)
            # Download to temporary location
            temp_path = temp_dir / f"{model_id}"
            await self._download_model_files(model_id, str(temp_path))
            
            # Store securely
            metadata = await self.storage.store_model(model_id, str(temp_path))
            
            # Create database record
            local_model = ModelInfo(
                model_id=model_id,
                type=model_type,
                local_path=metadata["path"],
                file_hash=metadata["hash"],
                file_size=metadata["size"],
                is_active=False,
                size_mb=metadata["size"] / (1024 * 1024)
            )
            
            await self.db_context.models.add_with_retry(local_model)
                
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()
                
        except Exception as e:
            self.logger.error(f"Failed to download model: {str(e)}")
            raise

    async def delete_model(self, model_id: str) -> None:
        try:
            # Get model from database
            model = await self.db_context.models.get_by_id(model_id)
            if not model:
                raise NotFoundError(f"Model {model_id} not found in database", source_class=self.__class__.__name__)

            # Delete from secure storage
            await self.storage.delete_model(model_id)

            # Delete from database
            await self.db_context.models.delete(model)

            # Remove metadata
            self._delete_model_metadata(model_id)

        except Exception as e:
            self.logger.error(f"Failed to delete model: {str(e)}")
            raise

    async def select_model(self, model_id: str, model_type: ModelType) -> None:
        try:
            await self.db_context.models.set_active(model_id, model_type)
        except Exception as e:
            self.logger.error(f"Failed to select model: {str(e)}")
            raise

    async def _download_model_files(self, model_id: str, model_path: str) -> None:
        """Download model files from Hugging Face"""
        try:
            # Check available disk space before downloading
            if not self._check_disk_space(model_id):
                raise RuntimeError("Insufficient disk space for model download")

            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                lambda: self._download_model_sync(model_id, model_path)
            )

        except Exception as e:
            self.logger.error(f"Failed to download model files: {str(e)}")
            if os.path.exists(model_path):
                try:
                    shutil.rmtree(model_path)  # Ensure memory is released
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to clean up model files: {cleanup_error}")
            raise

    def _download_model_sync(self, model_id: str, model_path: str) -> None:
        """Synchronous model download implementation with memory management"""
        try:
            # Download model files in chunks to control memory usage
            snapshot_download(
                repo_id=model_id,
                local_dir=model_path,
                token=False,
                local_files_only=False,
                resume_download=True,  # Resume interrupted downloads
                max_workers=1  # Limit concurrent downloads
            )

            # Verify download integrity
            if not self._verify_download(model_path):
                raise RuntimeError("Model download verification failed")

        except Exception as e:
            # Clean up on failure
            if os.path.exists(model_path):
                try:
                    shutil.rmtree(model_path)  # Ensure memory is released
                    self.logger.info(f"Cleaned up incomplete download at {model_path}")
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to clean up model files: {cleanup_error}")
            raise

    def _save_model_metadata(self, model_id: str, model_type: ModelType) -> None:
        """Save model metadata to track installed models"""
        metadata_path = os.path.join(self.model_cache_dir, "metadata.json")
        metadata = self._load_metadata()
        metadata[model_id] = {
            "type": model_type.value,
            "installed_at": datetime.datetime.now().isoformat()
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

    def _delete_model_metadata(self, model_id: str) -> None:
        """Remove model from metadata"""
        metadata_path = os.path.join(self.model_cache_dir, "metadata.json")
        metadata = self._load_metadata()
        metadata.pop(model_id, None)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

    def _load_metadata(self) -> dict:
        """Load metadata file or create if not exists"""
        metadata_path = os.path.join(self.model_cache_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                return json.load(f)
        return {}

    def _get_model_path(self, model_id: str) -> str:
        """Get the local path for a model"""
        sanitized_id = model_id.replace('/', '_')
        return os.path.join(settings.MODEL_STORAGE_DIR, sanitized_id)

    def _get_model_size(self, model_id: str) -> Optional[float]:
        """Get the size of a downloaded model in MB"""
        try:
            path = self._get_model_path(model_id)
            if not os.path.exists(path):
                return None
            total_size = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            self.logger.error(f"Error calculating model size: {e}")
            return None

    def _is_model_downloaded(self, model_id: str) -> bool:
        """Check if a model is already downloaded"""
        try:
            metadata = self._load_metadata()
            return model_id in metadata
        except Exception as e:
            self.logger.error(f"Error checking model download status: {e}")
            return False

    async def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Get current status of a model"""
        try:
            async with self.db_context as db:
                model = await db.models.get_by_id(model_id)
                if not model:
                    return {
                        "downloaded": False,
                        "active": False,
                        "last_used": None,
                        "size_mb": None
                    }
                
                return {
                    "downloaded": True,
                    "active": model.is_active,
                    "last_used": model.last_used,
                    "size_mb": model.size_mb
                }
        except Exception as e:
            self.logger.error(f"Error getting model status: {str(e)}")
            raise

    async def load_model(self, model_id: str) -> str:
        """Load a model from secure storage into a temporary location for use"""
        try:
            # Get model from database
            async with self.db_context as db:
                model = await db.models.get_by_id(model_id)
                if not model:
                    raise NotFoundError(f"Model {model_id} not found in database", source_class=self.__class__.__name__)

            # Create temporary directory for model
            temp_dir = Path("/tmp") / f"model_{model_id}_{datetime.datetime.now().timestamp()}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Load model from secure storage
            success = await self.storage.load_model(model_id, str(temp_dir / "model.bin"))
            if not success:
                raise

            # Update last used timestamp
            model.last_used = datetime.datetime.now(timezone.utc)
            await self.db_context.models.add_with_retry(model)

            # Return path to loaded model
            return str(temp_dir)

        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {str(e)}")

    async def is_model_downloaded(self, model_id: str) -> bool:
        """Check if a model is downloaded by checking the database"""
        try:
            async with self.db_context as db:
                model = await db.models.get_by_id(model_id)
                return model is not None
        except Exception as e:
            self.logger.error(f"Error checking if model is downloaded: {str(e)}")
            return False

    def _check_disk_space(self, model_id: str) -> bool:
        """
        Check if there's sufficient disk space for downloading the model
        Returns True if enough space available, False otherwise
        """
        try:
            # Get model card data to check size requirements
            model_info = self.hf_api.model_info(model_id)
            
            # Get available disk space in bytes
            storage_path = Path(settings.MODEL_STORAGE_DIR)
            storage_path.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
            
            # Get disk usage stats
            total, used, free_space = shutil.disk_usage(storage_path)
            self.logger.info(f"Disk space - Total: {total/1024/1024/1024:.2f}GB, "
                           f"Used: {used/1024/1024/1024:.2f}GB, "
                           f"Free: {free_space/1024/1024/1024:.2f}GB")
            
            # Check card data for size information
            if model_info.card_data:
                card_data = model_info.card_data.dict() if hasattr(model_info.card_data, 'dict') else vars(model_info.card_data)
                if "disk_requirements" in card_data:
                    try:
                        # Convert requirement string (e.g., "5GB") to bytes
                        required_str = str(card_data["disk_requirements"]).lower()
                        if "gb" in required_str:
                            required = float(required_str.replace("gb", "")) * 1024 * 1024 * 1024
                        elif "mb" in required_str:
                            required = float(required_str.replace("mb", "")) * 1024 * 1024
                        else:
                            required = float(required_str) * 1024 * 1024 * 1024  # Assume GB if no unit
                        
                        # Add 20% buffer for safety
                        required = required * 1.2
                        
                        self.logger.info(f"Required space (with buffer): {required/1024/1024/1024:.2f}GB")
                        return free_space >= required
                        
                    except (ValueError, AttributeError) as e:
                        self.logger.warning(f"Invalid disk requirement format in model card: {e}")
            
            # If no specific requirements found, ensure at least 5GB free space
            min_required = 5 * 1024 * 1024 * 1024  # 5GB in bytes
            self.logger.info(f"Using default minimum requirement: 5GB")
            return free_space >= min_required
            
        except Exception as e:
            self.logger.error(f"Error checking disk space: {e}")
            raise NotEnoughDiskSpaceError(f"Error checking disk space: {e}")

    def _verify_download(self, model_path: str) -> bool:
        """
        Verify the integrity of downloaded model files
        Returns True if verification passes, False otherwise
        """
        try:
            path = Path(model_path)
            
            # Check if directory exists and is not empty
            if not path.exists() or not path.is_dir():
                self.logger.error("Model directory does not exist or is not a directory")
                return False
                
            # List all files recursively
            found_files = list(path.glob("**/*"))
            self.logger.info(f"Found {len(found_files)} files in model directory")
            
            if not found_files:
                self.logger.error("No files found in model directory")
                return False
            
            # Look for common model files (at least one should exist)
            model_extensions = ('.bin', '.ckpt', '.pt', '.pth', '.safetensors', '.onnx', '.model')
            config_files = ('config.json', 'pytorch_model.bin.index.json', 'model.safetensors.index.json')
            
            model_files = [f for f in found_files if f.is_file() and f.name.endswith(model_extensions)]
            config_exists = any(f for f in found_files if f.is_file() and f.name in config_files)
            
            self.logger.info(f"Found {len(model_files)} model weight files")
            self.logger.info(f"Configuration file exists: {config_exists}")
            
            # Check for at least one model file
            if not model_files:
                self.logger.error("No model weight files found")
                # List all files for debugging
                self.logger.error(f"Available files: {[f.name for f in found_files if f.is_file()]}")
                return False
                
            # Check file sizes are non-zero
            for file in found_files:
                if file.is_file():
                    size = file.stat().st_size
                    if size == 0:
                        self.logger.error(f"Empty file found: {file}")
                        return False
                    self.logger.debug(f"File {file.name}: {size/1024/1024:.2f}MB")
                    
            self.logger.info("Model verification completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying download: {e}")
            raise ModelDownloadError(f"Failed to verify model download: {str(e)}")
