import os
import sys
import ctypes
import gc
import base64
from contextlib import contextmanager
from typing import Generator
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

ARGON_MEMORY_COST = 102400
ARGON_TIME_COST = 3
ARGON_PARALLELISM = 4
SALT_SIZE = 16

def _lock_memory(address: int, size: int) -> bool:
    """Invokes OS-level APIs to pin memory, preventing it from paging to disk."""
    try:
        if sys.platform.startswith("linux"):
            libc = ctypes.CDLL("libc.so.6")
    
            return libc.mlock(ctypes.c_void_p(address), ctypes.c_size_t(size)) == 0
        elif sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            
            return kernel32.VirtualLock(ctypes.c_void_p(address), ctypes.c_size_t(size)) != 0
    except Exception:
        pass
    return False

def _unlock_memory(address: int, size: int) -> None:
    """Releases the OS-level memory pin."""
    try:
        if sys.platform.startswith("linux"):
            libc = ctypes.CDLL("libc.so.6")
            libc.munlock(ctypes.c_void_p(address), ctypes.c_size_t(size))
        elif sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            kernel32.VirtualUnlock(ctypes.c_void_p(address), ctypes.c_size_t(size))
    except Exception:
        pass

@contextmanager
def secure_memory(data: bytearray) -> Generator[bytearray, None, None]:
    """
    Pins the array in RAM, yields it for cryptographic operations, 
    then forcefully zeroes the memory bits before unlocking.
    """

    c_buffer = (ctypes.c_char * len(data)).from_buffer(data)
    address = ctypes.addressof(c_buffer)
    size = len(data)
    
    _lock_memory(address, size)
    
    try:
        yield data
    finally:
    
        for i in range(size):
            data[i] = 0
            
        _unlock_memory(address, size)
        del data

class Vault:
    """Handles memory-hard key derivation and payload encryption."""
    
    @staticmethod
    def generate_salt() -> bytes:
        """Generates a 128-bit cryptographically secure pseudo-random salt."""
        return os.urandom(SALT_SIZE)

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Derives a raw 32-byte AES key using Argon2id."""
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=ARGON_TIME_COST,
            lanes=ARGON_PARALLELISM,
            memory_cost=ARGON_MEMORY_COST
        )
        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def encrypt(payload: str, password: str, salt: bytes) -> bytes:
        """Encrypts string payloads securely in a locked RAM state."""
        raw_key = bytearray(Vault._derive_key(password, salt))
        
        with secure_memory(raw_key) as safe_key:
            b64_key = base64.urlsafe_b64encode(safe_key)
            cipher = Fernet(b64_key)
            encrypted_data = cipher.encrypt(payload.encode('utf-8'))
            
        del b64_key
        del cipher
        gc.collect() 
        
        return encrypted_data

    @staticmethod
    def decrypt(encrypted_payload: bytes, password: str, salt: bytes) -> str:
        """Decrypts byte payloads inside a locked RAM state, trapping errors."""
        raw_key = bytearray(Vault._derive_key(password, salt))
        
        with secure_memory(raw_key) as safe_key:
            b64_key = base64.urlsafe_b64encode(safe_key)
            cipher = Fernet(b64_key)
            
            try:
                decrypted_bytes = cipher.decrypt(encrypted_payload)
                return decrypted_bytes.decode('utf-8')
            except InvalidToken:
                raise ValueError("Decryption failed: Integrity check failed or invalid password.")
            finally:
                del b64_key
                del cipher
                gc.collect()