#!/usr/bin/env python3
"""Update all manifest files to v2 and re-sign them."""
import json
import hashlib
import sys
import os
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEY_PATH = Path(__file__).resolve().parent / "tools" / "keys" / "update_private_key.pem"
KEY_ID = "update-key-v1"

def canonical_bytes(manifest):
    payload = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

def sign_manifest(manifest, private_key_pem):
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

# 1. Compute SHA256 of combined.json
with open("combined.json", "r", encoding="utf-8") as f:
    combined_data = f.read()
combined_sha256 = hashlib.sha256(combined_data.encode("utf-8")).hexdigest()
print(f"combined.json SHA256: {combined_sha256}")

# 2. Update source-update.json
source_update = {
    "version": 3,
    "enhancedVersion": "v2",
    "enhancedName": "LDW-Cinema-Enhanced-v2",
    "configUrl": "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema-Enhanced/main/combined.json",
    "configUrls": [
        "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema-Enhanced/main/combined.json",
        "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema-Enhanced@main/combined.json",
        "https://ghfast.top/https://raw.githubusercontent.com/lidawei1985/LDW-Cinema-Enhanced/main/combined.json"
    ],
    "sha256": combined_sha256,
    "manifestVersion": 2,
    "changes": [
        "内容源大扩充: 从5个增至23个已验证可用的VOD源",
        "直播源增强: 新增3个外部直播源(IPV6央视卫视高清/IPV4通用/IPV6备用), 支持EPG和台标",
        "解析器扩充: 新增5个解析接口(虾米/夜幕/CK/全民/M3U8)",
        "海报加载优化: CDN优先排序, 慢源代理加速, 双重重试, 死源过滤",
        "直播稳定性: 每频道多路备份, 自动健康检测, 自动故障切换",
        "手机体验优化: 源按响应速度排序, 搜索全覆盖, 过滤器全开启",
        "版本标识: Enhanced-v2"
    ]
}
signed_su = sign_manifest(source_update, KEY_PATH.read_bytes())
with open("source-update.json", "w", encoding="utf-8") as f:
    json.dump(signed_su, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("source-update.json signed (v2)")

# 3. Update update-mobile.json (read existing, update version fields)
with open("update-mobile.json", "r", encoding="utf-8") as f:
    um = json.load(f)
um["enhancedVersion"] = "v2"
um["enhancedName"] = "LDW-Cinema-Enhanced-v2"
um["changelog"] = "内容源大扩充(23个已验证VOD源), 新增3个外部直播源(IPV6/IPV4+EPG+台标), 新增5个解析器, 海报加载优化, 直播多路备份+自动故障切换"
signed_um = sign_manifest(um, KEY_PATH.read_bytes())
with open("update-mobile.json", "w", encoding="utf-8") as f:
    json.dump(signed_um, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("update-mobile.json signed (v2)")

# 4. Update update.json (read existing, update version fields)
with open("update.json", "r", encoding="utf-8") as f:
    u = json.load(f)
u["enhancedVersion"] = "v2"
u["enhancedName"] = "LDW-Cinema-Enhanced-v2"
u["changelog"] = "内容源大扩充(23个已验证VOD源), 新增3个外部直播源(IPV6/IPV4+EPG+台标), 新增5个解析器"
signed_u = sign_manifest(u, KEY_PATH.read_bytes())
with open("update.json", "w", encoding="utf-8") as f:
    json.dump(signed_u, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("update.json signed (v2)")

print("\n=== All manifests updated to v2 and signed ===")
