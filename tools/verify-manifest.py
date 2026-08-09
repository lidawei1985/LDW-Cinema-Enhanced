#!/usr/bin/env python3
"""Verify the RSA-SHA256 signature of a signed update manifest.

Usage:
  python tools/verify-manifest.py update-mobile.json
  python tools/verify-manifest.py update-mobile.json --key tools/keys/update_public_key.pem
  python tools/verify-manifest.py update-mobile.json --remote   # fetch & verify from GitHub
"""

import argparse
import base64
import json
import sys
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

DEFAULT_KEY = Path(__file__).resolve().parent / "keys" / "update_public_key.pem"
KEY_ID = "update-key-v1"

REMOTE_URLS = {
    "update-mobile.json": [
        "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json",
        "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/update-mobile.json",
        "https://ghfast.top/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json",
    ],
    "source-update.json": [
        "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/source-update.json",
        "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/source-update.json",
        "https://ghfast.top/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/source-update.json",
    ],
    "update.json": [
        "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update.json",
        "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/update.json",
        "https://ghfast.top/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update.json",
    ],
}


def canonical_bytes(manifest: dict) -> bytes:
    payload = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def verify_manifest(manifest: dict, public_key_pem: bytes) -> bool:
    sig_block = manifest.get("signature")
    if not sig_block:
        print("FAIL: no signature field found", file=sys.stderr)
        return False

    algorithm = sig_block.get("algorithm", "")
    if algorithm != "SHA256withRSA":
        print(f"FAIL: unsupported algorithm '{algorithm}'", file=sys.stderr)
        return False

    key_id = sig_block.get("keyId", "")
    if key_id != KEY_ID:
        print(f"FAIL: unknown keyId '{key_id}'", file=sys.stderr)
        return False

    signature = base64.b64decode(sig_block.get("value", ""))
    data = canonical_bytes(manifest)

    key = serialization.load_pem_public_key(public_key_pem)
    try:
        key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception as e:
        print(f"FAIL: signature verification error: {e}", file=sys.stderr)
        return False


def fetch_remote(filename: str) -> bytes:
    urls = REMOTE_URLS.get(filename, [])
    if not urls:
        print(f"Error: no remote URLs configured for {filename}", file=sys.stderr)
        sys.exit(1)
    last_error = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LDW-Verify-Tool"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            last_error = e
            print(f"  retry: {url} -> {e}", file=sys.stderr)
    print(f"Error: all mirrors failed. Last: {last_error}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Verify update manifest signature")
    parser.add_argument("file", help="Manifest JSON filename (local or basename for --remote)")
    parser.add_argument("--key", default=str(DEFAULT_KEY), help="Public key PEM path")
    parser.add_argument("--remote", action="store_true", help="Fetch from GitHub/mirrors instead of local file")
    args = parser.parse_args()

    key_path = Path(args.key)
    if not key_path.exists():
        print(f"Error: public key {key_path} not found", file=sys.stderr)
        sys.exit(1)

    if args.remote:
        filename = Path(args.file).name
        raw = fetch_remote(filename)
        manifest = json.loads(raw.decode("utf-8"))
        print(f"Fetched: {filename}")
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)
        manifest = json.loads(path.read_text(encoding="utf-8"))

    if verify_manifest(manifest, key_path.read_bytes()):
        print(f"OK: signature valid")
        print(f"  versionCode: {manifest.get('versionCode', '?')}")
        print(f"  versionName: {manifest.get('versionName', '?')}")
        if "sha256" in manifest:
            print(f"  apkSha256:   {manifest['sha256'][:32]}...")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
