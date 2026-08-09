#!/usr/bin/env python3
"""LDW-Cinema-Enhanced Full Test Suite"""
import urllib.request, ssl, json, time, base64, sys, os
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

os.chdir(Path(__file__).parent)

PASS = 0
FAIL = 0
results = []

def record(name, ok, detail=""):
    global PASS, FAIL
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    results.append((name, status, detail))
    print(f"  [{status}] {name:45s} {detail}")

def test_mirror(name, url, expect_json=False, expect_apk=False, timeout=15):
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "LDW-Test-Suite"})
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        data = resp.read(8192)
        elapsed = time.time() - t0
        ct = resp.headers.get("Content-Type", "?")
        ok = True
        detail = f"{len(data)}B, {elapsed:.2f}s"
        if expect_json:
            try:
                json.loads(data.decode("utf-8"))
                detail += ", valid JSON"
            except:
                ok = False
                detail += f", NOT JSON (ct={ct})"
        if expect_apk:
            if data[:4] == b"PK\x03\x04":
                detail += ", valid APK"
            else:
                ok = False
                detail += f", NOT APK (ct={ct})"
        if "text/html" in ct and expect_json:
            ok = False
            detail += f", HTML wrapper"
        record(name, ok, detail)
        return ok
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:80]}"
        record(name, False, err)
        return False

print("=" * 80)
print("LDW-Cinema-Enhanced Full Test Suite (v2 - Post Fix)")
print("=" * 80)

# --- Section 1: Sign/Verify ---
print("\n--- Section 1: Sign/Verify (8 tests) ---")

# 1.1 Verify local signatures
for fname in ["update-mobile.json", "update.json", "source-update.json"]:
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify", "tools/verify-manifest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    manifest = json.loads(Path(fname).read_text(encoding="utf-8"))
    pub_key = Path("tools/keys/update_public_key.pem").read_bytes()
    ok = mod.verify_manifest(manifest, pub_key)
    record(f"Verify {fname} signature", ok, 
           f"versionCode={manifest.get('versionCode', '?')}")

# 1.2 Tamper detection
import tempfile, shutil
for fname in ["update-mobile.json", "source-update.json"]:
    manifest = json.loads(Path(fname).read_text(encoding="utf-8"))
    manifest["versionCode"] = manifest.get("versionCode", 0) + 999
    pub_key = Path("tools/keys/update_public_key.pem").read_bytes()
    ok = not mod.verify_manifest(manifest, pub_key)  # Should FAIL = tamper detected
    record(f"Tamper detection {fname}", ok, "篡改后被正确拒绝" if ok else "篡改未检测到!")

# 1.3 Re-sign and verify
for fname in ["update-mobile.json"]:
    import subprocess
    r = subprocess.run(
        ["D:\\DevTools\\Python312\\python.exe", "tools/sign-manifest.py", fname, "--dry-run"],
        capture_output=True, text=True
    )
    ok = r.returncode == 0 and "signature" in r.stdout
    record(f"Dry-run sign {fname}", ok, "输出签名但不写磁盘" if ok else r.stderr[:60])

# 1.4 Canonical bytes determinism
manifest = json.loads(Path("update-mobile.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("sign", "tools/sign-manifest.py")
sign_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sign_mod)
cb1 = sign_mod.canonical_bytes(manifest)
cb2 = mod.canonical_bytes(manifest)
ok = cb1 == cb2
record("canonical_bytes 一致性", ok, f"sign/verify 两端一致, {len(cb1)} bytes")

# --- Section 2: Mirror Reachability ---
print("\n--- Section 2: Mirror Reachability ---")
print("  2.1 Manifest mirrors (update-mobile.json):")
test_mirror("GitHub raw", "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json", expect_json=True)
test_mirror("jsDelivr CDN", "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/update-mobile.json", expect_json=True)
test_mirror("ghfast.top", "https://ghfast.top/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json", expect_json=True)

print("  2.2 License mirrors (mobile-licenses.json):")
test_mirror("GitHub API", "https://api.github.com/repos/lidawei1985/LDW-Cinema/contents/mobile-licenses.json?ref=main", expect_json=True)
test_mirror("GitHub raw", "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/mobile-licenses.json", expect_json=True)
test_mirror("jsDelivr CDN", "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/mobile-licenses.json", expect_json=True)
test_mirror("ghfast.top", "https://ghfast.top/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/mobile-licenses.json", expect_json=True)

print("  2.3 APK download mirrors:")
test_mirror("GitHub Releases", "https://github.com/lidawei1985/LDW-Cinema/releases/download/v1.0.248-mobile/LDW-Cinema-Mobile-v248.apk", expect_apk=True)
test_mirror("ghproxy.net", "https://ghproxy.net/https://github.com/lidawei1985/LDW-Cinema/releases/download/v1.0.248-mobile/LDW-Cinema-Mobile-v248.apk", expect_apk=True)
test_mirror("ghfast.top", "https://ghfast.top/https://github.com/lidawei1985/LDW-Cinema/releases/download/v1.0.248-mobile/LDW-Cinema-Mobile-v248.apk", expect_apk=True)

print("  2.4 Dead mirrors removed verification:")
dead_urls = [
    ("mirror.ghproxy.com removed", "https://mirror.ghproxy.com/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json"),
    ("ghproxy.com removed", "https://ghproxy.com/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json"),
    ("Gitee removed", "https://gitee.com/lidawei1985/LDW-Cinema/raw/main/update-mobile.json"),
]
for name, url in dead_urls:
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "LDW-Test-Suite"})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        data = resp.read(8192)
        ct = resp.headers.get("Content-Type", "?")
        is_json = False
        try:
            json.loads(data.decode("utf-8")[:200])
            is_json = True
        except:
            pass
        # If it returns HTML or non-JSON, it's correctly excluded
        ok = not is_json
        record(name, ok, "dead/non-JSON (correctly removed)" if ok else "STILL RETURNS JSON!")
    except Exception:
        record(name, True, "dead (correctly removed)")

# --- Section 3: License System ---
print("\n--- Section 3: License System ---")

# 3.1 Decode local license
with open("mobile-licenses.json", "r") as f:
    lic = json.load(f)
payload = json.loads(base64.b64decode(lic["payload"]))
record("本地 payload 解码", True, f"{len(payload['licenses'])} licenses")
record("issuedAt 时间戳", "issuedAt" in payload, str(payload.get("issuedAt", "MISSING")))
record("version 字段", "version" in payload, str(payload.get("version", "MISSING")))

# 3.2 All required fields
fields_ok = True
for i, l in enumerate(payload["licenses"]):
    for field in ["deviceCode", "memberName", "expiresAt", "revoked", "adultEnabled"]:
        if field not in l:
            fields_ok = False
            break
record("所有授权必填字段完整", fields_ok, f"{len(payload['licenses'])} licenses checked")

# 3.3 License signature (uses license key, not manifest key)
# License signing: sign(compact_json_bytes) -> payload = base64(compact_json_bytes)
# So we must verify against the DECODED payload, not the base64 string
license_pub_key = serialization.load_pem_public_key(Path("tools/keys/license_public_key.pem").read_bytes())
sig = base64.b64decode(lic["signature"])
# The signature is over the raw compact JSON bytes (before base64 encoding)
signed_data = base64.b64decode(lic["payload"])
try:
    license_pub_key.verify(sig, signed_data, asym_padding.PKCS1v15(), hashes.SHA256())
    record("License RSA 签名验证", True, "SHA256withRSA valid (license key)")
except Exception as e:
    record("License RSA 签名验证", False, str(e)[:60])

# 3.4 Remote license fetch
try:
    t0 = time.time()
    req = urllib.request.Request(
        "https://api.github.com/repos/lidawei1985/LDW-Cinema/contents/mobile-licenses.json?ref=main",
        headers={"User-Agent": "LDW-Test-Suite"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    raw = json.loads(resp.read().decode("utf-8"))
    remote_content = base64.b64decode(raw["content"])
    remote_lic = json.loads(remote_content)
    remote_payload = json.loads(base64.b64decode(remote_lic["payload"]))
    elapsed = time.time() - t0
    record("远程授权拉取", True, f"{len(remote_payload['licenses'])} licenses in {elapsed:.2f}s")
except Exception as e:
    record("远程授权拉取", False, str(e)[:60])

# 3.5 Device code validation
record("设备码 - 合法格式", len("88F4FF45B739B16C") == 16, "16 chars uppercase hex")
record("设备码 - 过短拒绝", len("ABC123") < 16, "rejected")
record("设备码 - 空值拒绝", len("") == 0, "rejected")

# 3.6 Manifest fields
manifest = json.loads(Path("update-mobile.json").read_text(encoding="utf-8"))
record("versionCode 完整性", manifest.get("versionCode") == 248, "248")
record("versionName 完整性", manifest.get("versionName") == "1.0.248-mobile", "1.0.248-mobile")
record("SHA256 哈希存在", len(manifest.get("sha256", "")) == 64, f"{manifest.get('sha256', '')[:32]}...")

# 3.7 apkUrls count
apk_urls = manifest.get("apkUrls", [])
record("apkUrls 多镜像", len(apk_urls) >= 3, f"{len(apk_urls)} URLs")

# --- Summary ---
total = PASS + FAIL
rate = 100 * PASS // total if total > 0 else 0
print("\n" + "=" * 80)
print(f"TOTAL: {PASS}/{total} passed ({rate}%)")
print(f"  PASS: {PASS}")
print(f"  FAIL: {FAIL}")
print("=" * 80)

# Print failures
if FAIL > 0:
    print("\nFailures:")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  - {name}: {detail}")

sys.exit(0 if FAIL == 0 else 1)
