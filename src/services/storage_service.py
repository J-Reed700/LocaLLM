import os
import shutil
import hashlib
import aiofiles
import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from websrc.config.settings import settings

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

    async def store_model(self, model_id: str, source_path: str) -> dict:
        try:
            # Create model directory
            model_dir = self.base_path / self._sanitize_path(model_id)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Calculate hash and encrypt model
            file_hash = await self._calculate_file_hash(source_path)
            dest_path = model_dir / "model.bin"
            
            async with aiofiles.open(source_path, 'rb') as sf:
                content = await sf.read()
                encrypted = self.fernet.encrypt(content)
                async with aiofiles.open(dest_path, 'wb') as df:
                    await df.write(encrypted)
            
            # Store metadata
            metadata = {
                "hash": file_hash,
                "path": str(dest_path),
                "size": os.path.getsize(source_path)
            }
            
            return metadata
        except Exception as e:
            self.logger.error(f"Error storing model: {str(e)}")
            raise
            
    async def load_model(self, model_id: str, dest_path: str) -> bool:
        try:
            source_path = self.base_path / self._sanitize_path(model_id) / "model.bin"
            if not source_path.exists():
                raise FileNotFoundError(f"Model {model_id} not found")
                
            # Decrypt and verify model
            async with aiofiles.open(source_path, 'rb') as sf:
                encrypted = await sf.read()
                decrypted = self.fernet.decrypt(encrypted)
                async with aiofiles.open(dest_path, 'wb') as df:
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