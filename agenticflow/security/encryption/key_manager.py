"""
Key Manager

Secure key storage and management for encryption operations.
"""

import os
import json
import tempfile
from typing import Dict, Optional, Any, Set
from pathlib import Path
from .encryption_manager import EncryptionManager, EncryptionError


class KeyManager:
    """
    Manages encryption keys and secure storage of sensitive data.

    Provides secure key generation, storage, rotation, and access control.
    """

    def __init__(self, key_storage_path: Optional[str] = None,
                 master_password: Optional[str] = None):
        """
        Initialize key manager.

        Args:
            key_storage_path: Path to store encrypted keys
            master_password: Master password for key encryption
        """
        self.key_storage_path = Path(key_storage_path) if key_storage_path else Path(tempfile.gettempdir()) / "agenticflow_keys"
        self.key_storage_path.mkdir(exist_ok=True, mode=0o700)  # Secure permissions

        self._encryption_manager = EncryptionManager()
        self._master_key = None
        self._loaded_keys: Dict[str, bytes] = {}
        self._key_metadata: Dict[str, Dict[str, Any]] = {}

        if master_password:
            self._initialize_master_key(master_password)

    def _initialize_master_key(self, master_password: str) -> None:
        """Initialize master key from password."""
        salt_file = self.key_storage_path / "master.salt"

        if salt_file.exists():
            # Load existing salt
            salt = salt_file.read_bytes()
        else:
            # Generate new salt
            salt = os.urandom(32)
            salt_file.write_bytes(salt)
            salt_file.chmod(0o600)

        self._master_key = self._encryption_manager.generate_key_from_password(
            master_password, salt
        )
        self._master_encryption = EncryptionManager(self._master_key)

    def generate_key(self, key_name: str, key_type: str = "symmetric",
                    key_size: Optional[int] = None, metadata: Optional[Dict] = None) -> str:
        """
        Generate and store a new encryption key.

        Args:
            key_name: Unique name for the key
            key_type: Type of key ("symmetric" or "asymmetric")
            key_size: Key size (for asymmetric keys)
            metadata: Additional metadata to store with key

        Returns:
            str: Key identifier

        Raises:
            EncryptionError: If key generation fails
        """
        if key_name in self._loaded_keys:
            raise EncryptionError(f"Key '{key_name}' already exists")

        try:
            if key_type == "symmetric":
                from cryptography.fernet import Fernet
                key_data = Fernet.generate_key()
                self._loaded_keys[key_name] = key_data

            elif key_type == "asymmetric":
                key_size = key_size or 2048
                key_pair = self._encryption_manager.generate_asymmetric_keypair(
                    key_name, key_size
                )
                # Store both keys
                self._loaded_keys[f"{key_name}_private"] = key_pair["private_key"]
                self._loaded_keys[f"{key_name}_public"] = key_pair["public_key"]
                key_data = key_pair["private_key"]  # Store private key as main

            else:
                raise EncryptionError(f"Unsupported key type: {key_type}")

            # Store metadata
            self._key_metadata[key_name] = {
                "type": key_type,
                "size": key_size,
                "created_at": self._encryption_manager.hash_data(str(os.urandom(16))),
                "metadata": metadata or {}
            }

            # Persist key to storage
            self._store_key(key_name, key_data)

            return key_name

        except Exception as e:
            raise EncryptionError(f"Key generation failed: {e}")

    def load_key(self, key_name: str) -> Optional[bytes]:
        """
        Load key from storage.

        Args:
            key_name: Name of key to load

        Returns:
            bytes: Key data if found, None otherwise
        """
        if key_name in self._loaded_keys:
            return self._loaded_keys[key_name]

        try:
            key_data = self._load_key(key_name)
            if key_data:
                self._loaded_keys[key_name] = key_data
            return key_data
        except Exception:
            return None

    def delete_key(self, key_name: str) -> bool:
        """
        Delete key from storage.

        Args:
            key_name: Name of key to delete

        Returns:
            bool: True if key was deleted
        """
        try:
            # Remove from memory
            if key_name in self._loaded_keys:
                del self._loaded_keys[key_name]

            # Remove asymmetric key components
            for suffix in ["_private", "_public"]:
                full_name = f"{key_name}{suffix}"
                if full_name in self._loaded_keys:
                    del self._loaded_keys[full_name]

            # Remove metadata
            if key_name in self._key_metadata:
                del self._key_metadata[key_name]

            # Remove from storage
            key_file = self.key_storage_path / f"{key_name}.key"
            if key_file.exists():
                key_file.unlink()

            return True

        except Exception:
            return False

    def list_keys(self) -> Set[str]:
        """
        List available keys.

        Returns:
            Set[str]: Set of key names
        """
        keys = set(self._loaded_keys.keys())

        # Add keys from storage
        try:
            for key_file in self.key_storage_path.glob("*.key"):
                key_name = key_file.stem
                keys.add(key_name)
        except Exception:
            pass

        return keys

    def get_key_metadata(self, key_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a key.

        Args:
            key_name: Name of key

        Returns:
            Dict with key metadata if found
        """
        return self._key_metadata.get(key_name)

    def rotate_key(self, key_name: str) -> str:
        """
        Rotate an existing key (generate new key with same name).

        Args:
            key_name: Name of key to rotate

        Returns:
            str: New key identifier

        Raises:
            EncryptionError: If rotation fails
        """
        # Get existing key metadata
        metadata = self._key_metadata.get(key_name)
        if not metadata:
            raise EncryptionError(f"Key '{key_name}' not found for rotation")

        # Backup old key
        old_key_name = f"{key_name}_backup_{self._encryption_manager.generate_secure_token(8)}"
        if key_name in self._loaded_keys:
            self._loaded_keys[old_key_name] = self._loaded_keys[key_name]

        # Delete current key
        self.delete_key(key_name)

        # Generate new key with same parameters
        return self.generate_key(
            key_name,
            metadata["type"],
            metadata.get("size"),
            metadata.get("metadata")
        )

    def _store_key(self, key_name: str, key_data: bytes) -> None:
        """Store key data to file."""
        key_file = self.key_storage_path / f"{key_name}.key"

        if self._master_key and hasattr(self, '_master_encryption'):
            # Encrypt key data with master key
            encrypted_data = self._master_encryption.encrypt_symmetric(key_data)
            key_file.write_bytes(encrypted_data)
        else:
            # Store unencrypted (not recommended for production)
            key_file.write_bytes(key_data)

        # Set secure permissions
        key_file.chmod(0o600)

    def _load_key(self, key_name: str) -> Optional[bytes]:
        """Load key data from file."""
        key_file = self.key_storage_path / f"{key_name}.key"

        if not key_file.exists():
            return None

        try:
            encrypted_data = key_file.read_bytes()

            if self._master_key and hasattr(self, '_master_encryption'):
                # Decrypt key data
                return self._master_encryption.decrypt_symmetric(encrypted_data)
            else:
                # Return unencrypted data
                return encrypted_data

        except Exception:
            return None

    def export_key(self, key_name: str, export_password: Optional[str] = None) -> Optional[bytes]:
        """
        Export key in encrypted format.

        Args:
            key_name: Name of key to export
            export_password: Password to encrypt export (optional)

        Returns:
            bytes: Encrypted key export
        """
        key_data = self.load_key(key_name)
        if not key_data:
            return None

        if export_password:
            # Encrypt with export password
            export_manager = EncryptionManager()
            export_key = export_manager.generate_key_from_password(export_password)
            export_encryption = EncryptionManager(export_key)
            return export_encryption.encrypt_symmetric(key_data)
        else:
            return key_data

    def import_key(self, key_name: str, key_data: bytes,
                   import_password: Optional[str] = None, overwrite: bool = False) -> bool:
        """
        Import key from encrypted format.

        Args:
            key_name: Name to assign to imported key
            key_data: Encrypted key data
            import_password: Password to decrypt import (optional)
            overwrite: Whether to overwrite existing key

        Returns:
            bool: True if import successful
        """
        if key_name in self._loaded_keys and not overwrite:
            return False

        try:
            if import_password:
                # Decrypt with import password
                import_manager = EncryptionManager()
                import_key = import_manager.generate_key_from_password(import_password)
                import_encryption = EncryptionManager(import_key)
                decrypted_data = import_encryption.decrypt_symmetric(key_data)
            else:
                decrypted_data = key_data

            # Store the imported key
            self._loaded_keys[key_name] = decrypted_data
            self._store_key(key_name, decrypted_data)

            return True

        except Exception:
            return False