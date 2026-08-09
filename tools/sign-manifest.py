#!/usr/bin/env python3
"""Sign an update manifest JSON file with RSA-SHA256.

The script reads a manifest JSON, computes a canonical signature over all
fields *except* the ``signature`` block, and writes the signed manifest back.

The signed manifest keeps full backward compatibility: old APP builds that
do not know about the ``signature`` field simply ignore it. New builds can
verify the signature before applying the update.

Usage:
  python tools/sign-manifest.py update-mobile.json
  python tools/sign-manifest.py update-mobile.json --key tools/keys/update_private_key.pem
  python tools/sign-manifest.py update-mobile.json --dry-run   # print only, do not write
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

DEFAULT_KEY = Path(__file__).resolve().parent / "keys" / "update_private_key.pem"
KEY_ID = "update-key-v1"


def canonical_bytes(manifest: dict) -> bytes:
    """Serialize manifest without the ``signature`` field, sorted keys, compact."""
    payload = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_manifest(manifest: dict, private_key_pem: bytes) -> dict:
    """Return a copy of *manifest* with a ``signature`` block added."""
    key = serialization.load_pem_private_key(private_key_pem, password=None)
    data = canonical_bytes(manifest)
    signature = key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    result = dict(manifest)
    result["signature"] = {
        "algorithm": "SHA256withRSA",
        "keyId": KEY_ID,
        "value": base64.b64encode(signature).decode("ascii"),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Sign an update manifest JSON")
    parser.add_argument("file", help="Path to the manifest JSON file")
    parser.add_argument("--key", default=str(DEFAULT_KEY), help="Private key PEM path")
    parser.add_argument("--dry-run", action="store_true", help="Print signed JSON without writing")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    key_path = Path(args.key)
    if not key_path.exists():
        print(f"Error: private key {key_path} not found", file=sys.stderr)
        print("Run: python tools/generate_keys.py first", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(path.read_text(encoding="utf-8"))
    signed = sign_manifest(manifest, key_path.read_bytes())

    output = json.dumps(signed, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print(output)
    else:
        path.write_text(output, encoding="utf-8")
        print(f"Signed: {path}")
        print(f"  algorithm: {signed['signature']['algorithm']}")
        print(f"  keyId:     {signed['signature']['keyId']}")
        print(f"  signature: {signed['signature']['value'][:48]}...")


if __name__ == "__main__":
    main()
