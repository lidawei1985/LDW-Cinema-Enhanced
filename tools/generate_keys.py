#!/usr/bin/env python3
"""Generate RSA key pair for signing update manifests.

Produces:
  tools/keys/update_private_key.pem  (KEEP SECRET - never commit to public repo)
  tools/keys/update_public_key.pem   (safe to publish, APP uses this to verify)

Usage:
  python tools/generate_keys.py
"""

import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

KEYS_DIR = Path(__file__).resolve().parent / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "update_private_key.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "update_public_key.pem"


def generate():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    PRIVATE_KEY_PATH.write_bytes(private_pem)

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    PUBLIC_KEY_PATH.write_bytes(public_pem)

    print(f"Private key: {PRIVATE_KEY_PATH}")
    print(f"Public key:  {PUBLIC_KEY_PATH}")
    print()
    print("IMPORTANT: Keep update_private_key.pem secret!")
    print("           Commit only update_public_key.pem to the repository.")


if __name__ == "__main__":
    generate()
