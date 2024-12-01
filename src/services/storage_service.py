import os
import shutil
import hashlib
import aiofiles
import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from websrc.config.settings import settings
import datetime
from datetime import timezone
from src.models.pydantic import ModelMetadata

class SecureStorageService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(settings.MODEL_STORAGE_DIR)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption key
        key_path = self.base_path / ".key"
        if not key_path.exists():
            key = Fernet.generate_key()
            key_path.write_bytes(key)
        self.fernet = Fernet(key_path.read_bytes())

    async def store_model(self, model_id: str, source_path: str) -> ModelMetadata:
        try:
            # Create model directory
            model_dir = self.base_path / self._sanitize_path(model_id)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            source_path = Path(source_path)
            if source_path.is_dir():
                # Handle directory-based models
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(source_path)
                        dest_path = model_dir / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        async with aiofiles.open(file_path, 'rb') as sf:
                            content = await sf.read()
                            encrypted = self.fernet.encrypt(content)
                            async with aiofiles.open(dest_path, 'wb') as df:
                                await df.write(encrypted)
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                
                return ModelMetadata(
                    id=model_id,
                    size_bytes=total_size,
                    created_at=datetime.datetime.now(timezone.utc)
                )
            else:
                # Handle single file models (existing logic)
                dest_path = model_dir / "model.bin"
                async with aiofiles.open(source_path, 'rb') as sf:
                    content = await sf.read()
                    encrypted = self.fernet.encrypt(content)
                    async with aiofiles.open(dest_path, 'wb') as df:
                        await df.write(encrypted)
                
                return ModelMetadata(
                    id=model_id,
                    size_bytes=dest_path.stat().st_size,
                    created_at=datetime.datetime.now(timezone.utc)
                )
                
        except Exception as e:
            self.logger.error(f"Error storing model: {str(e)}")
            raise

    async def load_model(self, model_id: str, dest_path: str) -> bool:
        try:
            source_dir = self.base_path / self._sanitize_path(model_id)
            dest_path = Path(dest_path)
            
            if not source_dir.exists():
                raise FileNotFoundError(f"Model {model_id} not found")
            
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle both single file and directory cases
            if (source_dir / "model.bin").exists():
                # Single file case
                source_path = source_dir / "model.bin"
                async with aiofiles.open(source_path, 'rb') as sf:
                    encrypted = await sf.read()
                    decrypted = self.fernet.decrypt(encrypted)
                    async with aiofiles.open(dest_path, 'wb') as df:
                        await df.write(decrypted)
            else:
                # Directory case
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(source_dir)
                        target_path = dest_path / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        async with aiofiles.open(file_path, 'rb') as sf:
                            encrypted = await sf.read()
                            decrypted = self.fernet.decrypt(encrypted)
                            async with aiofiles.open(target_path, 'wb') as df:
                                await df.write(decrypted)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model {model_id}: {str(e)}")
            raise

    async def delete_model(self, model_id: str) -> bool:
        try:
            model_dir = self.base_path / self._sanitize_path(model_id)
            if model_dir.exists():
                shutil.rmtree(model_dir)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting model {model_id}: {str(e)}")
            raise

    async def _calculate_file_hash(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def _sanitize_path(self, path: str) -> str:
        return "".join(c for c in path if c.isalnum() or c in "._-") 