"""
Secure Storage

High-level secure storage interface for sensitive agent data.
"""

import json
from typing import Any, Dict, Optional, Union
from pathlib import Path
from .encryption_manager import EncryptionManager, EncryptionError
from .key_manager import KeyManager


class SecureStorageError(Exception):
    """Exception raised for secure storage operations."""
    pass


class SecureStorage:
    """
    Secure storage for sensitive agent data.

    Provides encrypted storage with key management and access control.
    """

    def __init__(self, storage_path: Optional[str] = None,
                 master_password: Optional[str] = None):
        """
        Initialize secure storage.

        Args:
            storage_path: Path to store encrypted data
            master_password: Master password for encryption
        """
        self.storage_path = Path(storage_path) if storage_path else Path.cwd() / "secure_storage"
        self.storage_path.mkdir(exist_ok=True, mode=0o700)

        self.key_manager = KeyManager(
            str(self.storage_path / "keys"),
            master_password
        )
        self._encryption_manager = EncryptionManager()

        # Initialize default storage key
        self._storage_key_name = "default_storage"
        if self._storage_key_name not in self.key_manager.list_keys():
            self.key_manager.generate_key(self._storage_key_name, "symmetric")

    def store(self, key: str, data: Union[Dict, str, bytes],
              encrypt: bool = True) -> bool:
        """
        Store data securely.

        Args:
            key: Storage key identifier
            data: Data to store
            encrypt: Whether to encrypt the data

        Returns:
            bool: True if successful

        Raises:
            SecureStorageError: If storage fails
        """
        try:
            # Prepare data for storage
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            if encrypt:
                # Get storage key
                storage_key = self.key_manager.load_key(self._storage_key_name)
                if not storage_key:
                    raise SecureStorageError("Storage key not available")

                # Encrypt data
                encryptor = EncryptionManager(storage_key)
                encrypted_data = encryptor.encrypt_symmetric(data_bytes)
                storage_data = encrypted_data
            else:
                storage_data = data_bytes

            # Store to file
            storage_file = self.storage_path / f"{key}.dat"
            storage_file.write_bytes(storage_data)
            storage_file.chmod(0o600)

            # Store metadata
            metadata = {
                "encrypted": encrypt,
                "key_name": self._storage_key_name if encrypt else None,
                "type": type(data).__name__
            }
            metadata_file = self.storage_path / f"{key}.meta"
            metadata_file.write_text(json.dumps(metadata))
            metadata_file.chmod(0o600)

            return True

        except Exception as e:
            raise SecureStorageError(f"Failed to store data: {e}")

    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve stored data.

        Args:
            key: Storage key identifier

        Returns:
            Stored data if found, None otherwise

        Raises:
            SecureStorageError: If retrieval fails
        """
        try:
            storage_file = self.storage_path / f"{key}.dat"
            metadata_file = self.storage_path / f"{key}.meta"

            if not storage_file.exists() or not metadata_file.exists():
                return None

            # Load metadata
            metadata = json.loads(metadata_file.read_text())

            # Load data
            storage_data = storage_file.read_bytes()

            if metadata.get("encrypted", False):
                # Decrypt data
                key_name = metadata.get("key_name", self._storage_key_name)
                storage_key = self.key_manager.load_key(key_name)
                if not storage_key:
                    raise SecureStorageError("Decryption key not available")

                encryptor = EncryptionManager(storage_key)
                decrypted_data = encryptor.decrypt_symmetric(storage_data)
                data_bytes = decrypted_data
            else:
                data_bytes = storage_data

            # Convert back to original type
            data_type = metadata.get("type", "str")
            if data_type == "dict":
                return json.loads(data_bytes.decode('utf-8'))
            elif data_type == "str":
                return data_bytes.decode('utf-8')
            else:
                return data_bytes

        except Exception as e:
            raise SecureStorageError(f"Failed to retrieve data: {e}")

    def delete(self, key: str) -> bool:
        """
        Delete stored data.

        Args:
            key: Storage key identifier

        Returns:
            bool: True if successful
        """
        try:
            storage_file = self.storage_path / f"{key}.dat"
            metadata_file = self.storage_path / f"{key}.meta"

            deleted = False
            if storage_file.exists():
                storage_file.unlink()
                deleted = True

            if metadata_file.exists():
                metadata_file.unlink()
                deleted = True

            return deleted

        except Exception:
            return False

    def list_keys(self) -> list:
        """
        List all stored data keys.

        Returns:
            List of storage keys
        """
        keys = []
        try:
            for file_path in self.storage_path.glob("*.dat"):
                key = file_path.stem
                keys.append(key)
        except Exception:
            pass

        return sorted(keys)

    def rotate_storage_key(self) -> bool:
        """
        Rotate the storage encryption key.

        Returns:
            bool: True if successful
        """
        try:
            # Generate new storage key
            new_key_name = f"{self._storage_key_name}_new"
            self.key_manager.generate_key(new_key_name, "symmetric")

            # Re-encrypt all stored data with new key
            for key in self.list_keys():
                data = self.retrieve(key)
                if data is not None:
                    # Temporarily switch to new key
                    old_key_name = self._storage_key_name
                    self._storage_key_name = new_key_name
                    self.store(key, data, encrypt=True)
                    self._storage_key_name = old_key_name

            # Switch to new key permanently
            self.key_manager.delete_key(self._storage_key_name)
            self._storage_key_name = new_key_name

            return True

        except Exception:
            return False