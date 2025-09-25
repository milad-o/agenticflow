"""
Encryption Manager

Handles encryption and decryption of sensitive data in agent operations.
"""

import os
import base64
import hashlib
import secrets
from typing import Optional, Union, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionError(Exception):
    """Exception raised for encryption/decryption errors."""
    pass


class EncryptionManager:
    """
    Manages encryption and decryption operations for the framework.

    Supports both symmetric and asymmetric encryption methods.
    """

    def __init__(self, default_key: Optional[bytes] = None):
        """
        Initialize encryption manager.

        Args:
            default_key: Default encryption key (generates new if None)
        """
        self._symmetric_key = default_key or Fernet.generate_key()
        self._fernet = Fernet(self._symmetric_key)
        self._asymmetric_keys: Dict[str, Any] = {}

    @property
    def symmetric_key(self) -> bytes:
        """Get the symmetric encryption key."""
        return self._symmetric_key

    def generate_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Generate encryption key from password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generates random if None)

        Returns:
            bytes: Derived encryption key
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_symmetric(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data using symmetric encryption.

        Args:
            data: Data to encrypt

        Returns:
            bytes: Encrypted data

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            encrypted = self._fernet.encrypt(data)
            return encrypted
        except Exception as e:
            raise EncryptionError(f"Symmetric encryption failed: {e}")

    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data using symmetric encryption.

        Args:
            encrypted_data: Encrypted data to decrypt

        Returns:
            bytes: Decrypted data

        Raises:
            EncryptionError: If decryption fails
        """
        try:
            decrypted = self._fernet.decrypt(encrypted_data)
            return decrypted
        except Exception as e:
            raise EncryptionError(f"Symmetric decryption failed: {e}")

    def generate_asymmetric_keypair(self, key_name: str, key_size: int = 2048) -> Dict[str, bytes]:
        """
        Generate RSA asymmetric key pair.

        Args:
            key_name: Name to identify the key pair
            key_size: RSA key size in bits

        Returns:
            Dict containing public and private keys
        """
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size
            )
            public_key = private_key.public_key()

            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Store keys
            self._asymmetric_keys[key_name] = {
                'private': private_key,
                'public': public_key,
                'private_pem': private_pem,
                'public_pem': public_pem
            }

            return {
                'private_key': private_pem,
                'public_key': public_pem
            }

        except Exception as e:
            raise EncryptionError(f"Key generation failed: {e}")

    def encrypt_asymmetric(self, data: Union[str, bytes], key_name: str,
                          use_public_key: bool = True) -> bytes:
        """
        Encrypt data using asymmetric encryption.

        Args:
            data: Data to encrypt
            key_name: Name of key pair to use
            use_public_key: Whether to use public key for encryption

        Returns:
            bytes: Encrypted data

        Raises:
            EncryptionError: If encryption fails
        """
        if key_name not in self._asymmetric_keys:
            raise EncryptionError(f"Key pair '{key_name}' not found")

        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            key = (self._asymmetric_keys[key_name]['public'] if use_public_key
                   else self._asymmetric_keys[key_name]['private'])

            encrypted = key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted

        except Exception as e:
            raise EncryptionError(f"Asymmetric encryption failed: {e}")

    def decrypt_asymmetric(self, encrypted_data: bytes, key_name: str,
                          use_private_key: bool = True) -> bytes:
        """
        Decrypt data using asymmetric encryption.

        Args:
            encrypted_data: Encrypted data to decrypt
            key_name: Name of key pair to use
            use_private_key: Whether to use private key for decryption

        Returns:
            bytes: Decrypted data

        Raises:
            EncryptionError: If decryption fails
        """
        if key_name not in self._asymmetric_keys:
            raise EncryptionError(f"Key pair '{key_name}' not found")

        try:
            key = (self._asymmetric_keys[key_name]['private'] if use_private_key
                   else self._asymmetric_keys[key_name]['public'])

            decrypted = key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted

        except Exception as e:
            raise EncryptionError(f"Asymmetric decryption failed: {e}")

    def hash_data(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """
        Generate hash of data.

        Args:
            data: Data to hash
            algorithm: Hash algorithm to use

        Returns:
            str: Hexadecimal hash string

        Raises:
            EncryptionError: If hashing fails
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            if algorithm.lower() == 'sha256':
                hash_obj = hashlib.sha256()
            elif algorithm.lower() == 'sha512':
                hash_obj = hashlib.sha512()
            elif algorithm.lower() == 'md5':
                hash_obj = hashlib.md5()
            else:
                raise EncryptionError(f"Unsupported hash algorithm: {algorithm}")

            hash_obj.update(data)
            return hash_obj.hexdigest()

        except Exception as e:
            raise EncryptionError(f"Hashing failed: {e}")

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure random token.

        Args:
            length: Token length in bytes

        Returns:
            str: Base64-encoded secure token
        """
        token_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(token_bytes).decode('ascii')

    def constant_time_compare(self, a: Union[str, bytes], b: Union[str, bytes]) -> bool:
        """
        Compare two values in constant time to prevent timing attacks.

        Args:
            a: First value
            b: Second value

        Returns:
            bool: True if values are equal
        """
        if isinstance(a, str):
            a = a.encode('utf-8')
        if isinstance(b, str):
            b = b.encode('utf-8')

        return secrets.compare_digest(a, b)