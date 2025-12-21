from __future__ import annotations

import asyncio
import base64

import pyotp
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

hasher = PasswordHash((Argon2Hasher(),))
backup_code_hasher = PasswordHash.recommended()


def get_encryption_key(secret: str) -> bytes:
    """Get Encryption Key.

    Args:
        secret (str): Secret key used for encryption

    Returns:
        bytes: a URL safe encoded version of secret
    """
    if len(secret) <= 32:
        secret = f"{secret:<32}"[:32]
    return base64.urlsafe_b64encode(secret.encode())


async def get_password_hash(password: str | bytes) -> str:
    """Get password hash.

    Args:
        password: Plain password

    Returns:
        str: Hashed password
    """
    return await asyncio.get_running_loop().run_in_executor(None, hasher.hash, password)


async def verify_password(plain_password: str | bytes, hashed_password: str) -> bool:
    """Verify Password.

    Args:
        plain_password (str | bytes): The string or byte password
        hashed_password (str): the hash of the password

    Returns:
        bool: True if password matches hash.
    """
    valid, _ = await asyncio.get_running_loop().run_in_executor(
        None, hasher.verify_and_update, plain_password, hashed_password
    )
    return bool(valid)


def _verify_totp_code_sync(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


async def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code against the secret.

    Runs in thread executor to avoid blocking the event loop.

    Args:
        secret: The TOTP secret key.
        code: The TOTP code to verify.

    Returns:
        True if the code is valid, False otherwise.
    """
    return await asyncio.get_running_loop().run_in_executor(None, _verify_totp_code_sync, secret, code)


def _verify_backup_code_sync(code: str, hashed_codes: list[str]) -> int | None:
    for i, hashed_code in enumerate(hashed_codes):
        if backup_code_hasher.verify(code.upper(), hashed_code):
            return i
    return None


async def verify_backup_code(code: str, hashed_codes: list[str]) -> int | None:
    """Verify a backup code and return its index if valid.

    Runs in thread executor to avoid blocking the event loop
    (Argon2 verification is CPU-intensive).

    Args:
        code: The plain backup code to verify.
        hashed_codes: List of hashed backup codes to check against.

    Returns:
        Index of the used code, or None if invalid.
    """
    return await asyncio.get_running_loop().run_in_executor(None, _verify_backup_code_sync, code, hashed_codes)
