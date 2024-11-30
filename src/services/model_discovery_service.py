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

    async def get_available_models(self, model_type: ModelType) -> List[ModelInfo]:
        try:
            # Get models from both local and remote sources
            local_models = await self._get_local_models(model_type)
            remote_models = await self._get_remote_models(model_type)
            
            # Merge and deduplicate
            return self._merge_models(local_models, remote_models)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch models: {str(e)}")
            raise

    async def _get_remote_models(self, model_type: ModelType) -> List[ModelInfo]:
        try:
            # Define search parameters
            tags = ["text-generation"] if model_type == ModelType.TEXT else ["image-generation"]
            
            # Get models from HuggingFace
            models = await self.hf_api.list_models(
                filter=tags,
                sort="downloads",
                direction=-1,
                limit=20
            )
            
            available_models = []
            for model in models:
                is_compatible = self._check_model_compatibility(model.card_data)
                
                model_info = ModelInfo(
                    id=model.id,
                    name=model.id.split('/')[-1],
                    type=model_type,
                    downloads=model.downloads,
                    likes=model.likes,
                    is_downloaded=await self.is_model_downloaded(model.id),
                    compatible=is_compatible,
                    requirements=self._get_model_requirements(model.card_data),
                    description=model.description,
                    tags=model.tags
                )
                available_models.append(model_info)
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"Error fetching remote models: {str(e)}")
            raise

    def _get_model_requirements(self, card_data: ModelCardData) -> Dict[str, Any]:
        """Extract model requirements from card data"""
        return {
            "memory": card_data.get("memory_requirements", "Unknown"),
            "architecture": card_data.get("architectures", []),
            "device": "gpu" if card_data.get("requires_gpu", False) else "any"
        }

    async def download_model(self, model_id: str, model_type: ModelType) -> None:
        try:
            # Download to temporary location
            temp_path = Path("/tmp") / f"{model_id}_temp"
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
        try:            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                lambda: self._download_model_sync(model_id, model_path)
            )
        except Exception as e:
            self.logger.error(f"Failed to download model files: {str(e)}")
            raise

    def _download_model_sync(self, model_id: str, model_path: str) -> None:
        """Synchronous model download implementation"""
        try:
            # Download model files
            snapshot_download(
                repo_id=model_id,
                local_dir=model_path,
                token=settings.HUGGINGFACE_TOKEN if hasattr(settings, 'HUGGINGFACE_TOKEN') else None,
                local_files_only=False
            )
        except Exception as e:
            # Clean up on failure
            if os.path.exists(model_path):
                shutil.rmtree(model_path)
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
            model.last_used = datetime.datetime.now(datetime.UTC)
            await self.db_context.models.add_with_retry(model)

            # Return path to loaded model
            return str(temp_dir)

        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {str(e)}")
