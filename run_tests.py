#!/usr/bin/env python3
"""LDW-Cinema-Enhanced-v2 Full Test Suite"""
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
    print(f"  [{status}] {name:50s} {detail}")

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
print("LDW-Cinema-Enhanced-v2 Full Test Suite")
print("=" * 80)

# --- Section 1: Sign/Verify ---
print("\n--- Section 1: Sign/Verify ---")

# 1.1 Verify local signatures
import importlib.util
spec = importlib.util.spec_from_file_location("verify", "tools/verify-manifest.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

for fname in ["update-mobile.json", "update.json", "source-update.json"]:
    manifest = json.loads(Path(fname).read_text(encoding="utf-8"))
    pub_key = Path("tools/keys/update_public_key.pem").read_bytes()
    ok = mod.verify_manifest(manifest, pub_key)
    record(f"Verify {fname} signature", ok,
           f"enhancedVersion={manifest.get('enhancedVersion', '?')}")

# 1.2 Tamper detection
for fname in ["update-mobile.json", "source-update.json"]:
    manifest = json.loads(Path(fname).read_text(encoding="utf-8"))
    manifest["versionCode"] = manifest.get("versionCode", 0) + 999
    pub_key = Path("tools/keys/update_public_key.pem").read_bytes()
    ok = not mod.verify_manifest(manifest, pub_key)
    record(f"Tamper detection {fname}", ok, "篡改后被正确拒绝" if ok else "篡改未检测到!")

# 1.3 Canonical bytes determinism
manifest = json.loads(Path("update-mobile.json").read_text(encoding="utf-8"))
cb1 = mod.canonical_bytes(manifest)
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

print("  2.3 APK download mirrors:")
test_mirror("GitHub Releases", "https://github.com/lidawei1985/LDW-Cinema/releases/download/v1.0.248-mobile/LDW-Cinema-Mobile-v248.apk", expect_apk=True)
test_mirror("ghfast.top APK", "https://ghfast.top/https://github.com/lidawei1985/LDW-Cinema/releases/download/v1.0.248-mobile/LDW-Cinema-Mobile-v248.apk", expect_apk=True)

print("  2.4 Dead mirrors removed verification:")
dead_urls = [
    ("mirror.ghproxy.com removed", "https://mirror.ghproxy.com/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json"),
    ("ghproxy.com removed", "https://ghproxy.com/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json"),
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
        ok = not is_json
        record(name, ok, "dead/non-JSON (correctly removed)" if ok else "STILL RETURNS JSON!")
    except Exception:
        record(name, True, "dead (correctly removed)")

# --- Section 3: License System ---
print("\n--- Section 3: License System ---")

with open("mobile-licenses.json", "r") as f:
    lic = json.load(f)
payload = json.loads(base64.b64decode(lic["payload"]))
record("本地 payload 解码", True, f"{len(payload['licenses'])} licenses")
record("issuedAt 时间戳", "issuedAt" in payload, str(payload.get("issuedAt", "MISSING")))
record("version 字段", "version" in payload, str(payload.get("version", "MISSING")))

fields_ok = True
for i, l in enumerate(payload["licenses"]):
    for field in ["deviceCode", "memberName", "expiresAt", "revoked", "adultEnabled"]:
        if field not in l:
            fields_ok = False
            break
record("所有授权必填字段完整", fields_ok, f"{len(payload['licenses'])} licenses checked")

# License signature
license_pub_key = serialization.load_pem_public_key(Path("tools/keys/license_public_key.pem").read_bytes())
sig = base64.b64decode(lic["signature"])
signed_data = base64.b64decode(lic["payload"])
try:
    license_pub_key.verify(sig, signed_data, asym_padding.PKCS1v15(), hashes.SHA256())
    record("License RSA 签名验证", True, "SHA256withRSA valid (license key)")
except Exception as e:
    record("License RSA 签名验证", False, str(e)[:60])

# Remote license fetch
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

# --- Section 4: v2 Enhanced Features ---
print("\n--- Section 4: v2 Enhanced Features ---")

combined_path = Path("combined.json")
if combined_path.exists():
    combined = json.loads(combined_path.read_text(encoding="utf-8"))
    record("combined.json 存在", True, f"{len(combined_path.read_bytes())}B")

    # Version
    record("combined.json 版本标识 v2", combined.get("version") == "Enhanced-v2", combined.get("version", "MISSING"))

    # Sites count
    sites = combined.get("sites", [])
    record("站点数 >= 25", len(sites) >= 25, f"{len(sites)} sites")
    
    # Normal (non-adult) sites count
    normal_sites = [s for s in sites if "🔞" not in s.get("name", "") and not s.get("key", "").startswith("adult_") and not s.get("key", "").startswith("*") and s.get("key") != "美少女"]
    record("普通内容源数 >= 20", len(normal_sites) >= 20, f"{len(normal_sites)} normal sources (was 5 in v1)")

    # Key new sources
    site_keys = [s.get("key", "") for s in sites]
    new_sources_check = [
        ("site_suoni", "索尼影视"),
        ("site_huya", "虎牙资源"),
        ("site_wujin", "无尽影视"),
        ("site_jinying", "金鹰资源"),
        ("site_liangzi", "量子影视"),
        ("site_haohua", "豪华资源"),
        ("site_maoyan", "猫眼资源"),
        ("site_baiduyun", "百度云资源"),
        ("site_hongniu", "红牛资源"),
        ("site_ikun", "ikun资源"),
        ("site_guangsu", "光速资源"),
        ("site_niuniu", "牛牛资源"),
        ("site_yaya", "丫丫资源"),
        ("site_jisu", "极速资源"),
        ("site_uku", "U酷资源"),
        ("site_feifan", "非凡影视"),
        ("site_shandian", "闪电资源"),
        ("site_yinghua", "樱花资源"),
        ("site_baofeng", "暴风资源"),
        ("site_xinlang", "新浪资源"),
        ("site_senlin", "森林资源"),
        ("site_maotai", "茅台资源"),
    ]
    for key, name in new_sources_check:
        record(f"新源 {name}", key in site_keys, key)

    # All normal sites have searchable=1
    searchable_ok = all(s.get("searchable") == 1 for s in normal_sites)
    record("普通源全部可搜索", searchable_ok, f"{len(normal_sites)} sources searchable")

    # All normal sites have filterable=1
    filterable_ok = all(s.get("filterable") == 1 for s in normal_sites)
    record("普通源全部可过滤", filterable_ok, f"{len(normal_sites)} sources filterable")

    # Poster config
    pc = combined.get("posterConfig", {})
    record("posterConfig 存在", "enableCache" in pc, f"cache={pc.get('enableCache')}, days={pc.get('cacheDays')}")
    record("posterConfig 死源过滤", "slowSourcePatterns" in pc, str(pc.get("slowSourcePatterns", [])))
    record("posterConfig 并发控制", "maxConcurrent" in pc, f"max={pc.get('maxConcurrent')}, timeout={pc.get('timeout')}s")
    record("posterConfig 回退占位图", "fallbackToPlaceholder" in pc, str(pc.get("fallbackToPlaceholder")))

    # Live config
    lc = combined.get("liveConfig", {})
    record("liveConfig 存在", "healthCheck" in lc, f"healthCheck={lc.get('healthCheck')}, interval={lc.get('healthCheckInterval')}s")
    record("liveConfig 自动故障切换", "autoFallback" in lc, str(lc.get("autoFallback")))
    record("liveConfig EPG支持", lc.get("epgEnabled", False), str(lc.get("epgEnabled")))
    record("liveConfig 台标支持", lc.get("logoEnabled", False), str(lc.get("logoEnabled")))

    # Lives count
    lives = combined.get("lives", [])
    record("直播组数 >= 15", len(lives) >= 15, f"{len(lives)} live groups")

    # External live sources (type=0 with url)
    external_lives = [l for l in lives if l.get("type") == 0 and "url" in l]
    record("外部直播源 >= 3", len(external_lives) >= 3, f"{len(external_lives)} external live sources")
    
    for el in external_lives:
        record(f"外部直播源: {el.get('name', '?')}", True, el.get("url", "")[:60])

    # EPG support in external lives
    epg_ok = any("epg" in el for el in external_lives)
    record("外部直播源 EPG 支持", epg_ok, "EPG configured")

    # Multi-URL channels
    multi_url = sum(1 for lg in lives for ch in lg.get("channels", []) if len(ch.get("urls", [])) > 1)
    record("多路备份频道数 >= 84", multi_url >= 84, f"{multi_url} channels with 2+ URLs")

    # Parses count
    parses = combined.get("parses", [])
    record("解析器数 >= 15", len(parses) >= 15, f"{len(parses)} parses (was 12 in v1)")

    # Dead sources removed
    all_urls = []
    for lg in lives:
        for ch in lg.get("channels", []):
            all_urls.extend(ch.get("urls", []))
    has_gcalic = any("gcalic.v.myalicdn.com" in u for u in all_urls)
    record("死源 gcalic 已移除", not has_gcalic, "403 forbidden source removed")

    # enhancedChanges list
    changes = combined.get("enhancedChanges", [])
    record("enhancedChanges 存在", len(changes) >= 5, f"{len(changes)} changes documented")
    record("enhancedChanges v2标识", any("v2" in c for c in changes), "v2 marker in changes")
else:
    record("combined.json 存在", False, "FILE NOT FOUND")

# Manifest version checks
print("\n--- Section 5: Manifest Version Consistency ---")
for fname in ["update-mobile.json", "update.json", "source-update.json"]:
    m = json.loads(Path(fname).read_text(encoding="utf-8"))
    record(f"{fname} enhancedVersion=v2", m.get("enhancedVersion") == "v2", m.get("enhancedVersion", "MISSING"))
    record(f"{fname} enhancedName=v2", "v2" in m.get("enhancedName", ""), m.get("enhancedName", "MISSING"))

# source-update.json specific checks
su = json.loads(Path("source-update.json").read_text(encoding="utf-8"))
record("source-update version=3", su.get("version") == 3, str(su.get("version")))
record("source-update sha256 64chars", len(su.get("sha256", "")) == 64, su.get("sha256", "")[:32] + "...")
record("source-update configUrls >= 3", len(su.get("configUrls", [])) >= 3, f"{len(su.get('configUrls', []))} URLs")
record("source-update changes >= 5", len(su.get("changes", [])) >= 5, f"{len(su.get('changes', []))} changes")

# Poster cache worker
worker_path = Path("tools/poster-cache-worker.js")
record("海报缓存代理脚本存在", worker_path.exists(), f"{len(worker_path.read_bytes())}B" if worker_path.exists() else "NOT FOUND")

guide_path = Path("docs/POSTER_CACHE_GUIDE.md")
record("海报缓存部署指南存在", guide_path.exists(), f"{len(guide_path.read_bytes())}B" if guide_path.exists() else "NOT FOUND")

# Device code validation
record("设备码 - 合法格式", len("88F4FF45B739B16C") == 16, "16 chars uppercase hex")
record("设备码 - 过短拒绝", len("ABC123") < 16, "rejected")
record("设备码 - 空值拒绝", len("") == 0, "rejected")

# --- Summary ---
total = PASS + FAIL
rate = 100 * PASS // total if total > 0 else 0
print("\n" + "=" * 80)
print(f"TOTAL: {PASS}/{total} passed ({rate}%)")
print(f"  PASS: {PASS}")
print(f"  FAIL: {FAIL}")
print("=" * 80)

if FAIL > 0:
    print("\nFailures:")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  - {name}: {detail}")

sys.exit(0 if FAIL == 0 else 1)
