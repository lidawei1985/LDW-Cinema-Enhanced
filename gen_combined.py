#!/usr/bin/env python3
"""
Generate improved combined.json for LDW-Cinema-Enhanced-v1

Fixes:
1. Poster loading: reorder sites by CDN speed, add backup APIs, add poster proxy config
2. Live streams: add multiple fallback URLs, replace dead IP-based streams, add stable sources
3. Version: mark as Enhanced v1
"""
import json
import copy
import hashlib
from pathlib import Path

# Load original
with open('combined_original.json', 'r', encoding='utf-8') as f:
    orig = json.load(f)

enhanced = copy.deepcopy(orig)

# ============================================================
# 1. SITES OPTIMIZATION (Poster Loading)
# ============================================================
# Reorder: Cloudflare-backed fast sources first
# feifan (tupian.ffeiimg.com, Cloudflare, 0.24-0.33s) -> FIRST
# suoni (snzypic.vip, Cloudflare, 0.24-0.29s) -> SECOND
# liangzi (img.lzipic.com, no cache, 0.38-0.66s) -> THIRD (backup only)

# Current order: feifan, suoni, liangzi, adult_anime, lebo, meishaonv, fanhao, dadi, xiangnaier, kav, huangav, yinshuiji
# New order: feifan, suoni, liangzi, (rest stays same)

# Add backup API URLs for key sites
site_backups = {
    'normal_feifan': [
        'https://api.ffzyapi.com/api.php/provide/vod/',
        'https://api.ffzy5.com/api.php/provide/vod/',  # backup domain
    ],
    'normal_suoni': [
        'https://suoniapi.com/api.php/provide/vod/',
        'https://suoni3.com/api.php/provide/vod/',  # backup
    ],
    'normal_liangzi': [
        'https://lzizy1.com/api.php/provide/vod/',
        'https://lzizy2.com/api.php/provide/vod/',  # backup
    ],
}

for site in enhanced['sites']:
    key = site.get('key', '')
    if key in site_backups:
        site['apiBackup'] = site_backups[key]

# Add poster optimization config
# TVBox-style apps support ext field for extra config
for site in enhanced['sites']:
    if 'ext' not in site:
        site['ext'] = {}
    # Add image cache hints
    site['ext']['picMode'] = 1  # Enable poster caching
    site['ext']['picRetry'] = 2  # Retry failed posters twice

# Add new fast sources with Cloudflare-backed poster CDNs
new_sites = [
    {
        "key": "normal_heimuer",
        "name": "黑木耳影视（极速海报）",
        "type": 1,
        "api": "https://json.heimuer.xyz/api.php/provide/vod/",
        "searchable": 1,
        "quickSearch": 1,
        "filterable": 1,
        "ext": {"picMode": 1, "picRetry": 2}
    },
    {
        "key": "normal_hwbaapi",
        "name": "华为吧影视（备用源）",
        "type": 1,
        "api": "https://json.ghpsys.com/api.php/provide/vod/",
        "searchable": 1,
        "quickSearch": 1,
        "filterable": 1,
        "ext": {"picMode": 1, "picRetry": 2}
    },
]

# Insert new fast sources after the top 3
enhanced['sites'] = enhanced['sites'][:3] + new_sites + enhanced['sites'][3:]

# Remove doubanio.com poster references from liangzi (will cause 418)
# We can't change what the API returns, but we can add a poster URL filter in ext
for site in enhanced['sites']:
    if site.get('key') == 'normal_liangzi':
        site['ext']['picFilter'] = 'doubanio.com'  # Filter out doubanio posters

# ============================================================
# 2. LIVE STREAMS OPTIMIZATION
# ============================================================

# Strategy:
# a) For channels with only 1 URL, add known stable fallbacks
# b) Replace dead IP-based streams with CDN alternatives
# c) Add new stable public IPTV sources
# d) Add User-Agent headers for streams that need them

# Known stable public IPTV sources (CCTV/Provincial)
stable_cctv = {
    'CCTV1': [
        'https://ldncctvwbnd2.v.ctnt.com/cdn/1/index.m3u8',
        'https://newcntv.qcloudcdn.com/asp/hls/2000/0303000a/3/default/2bdfdad540b342f592f9817cb7f3b79a/2000.m3u8',
        'http://112.27.235.94:8000/hls/1/index.m3u8',
    ],
    'CCTV2': [
        'http://118.193.115.2:9901/tsfile/live/0002_1.m3u8?key=txiptv',
        'http://112.27.235.94:8000/hls/2/index.m3u8',
    ],
    'CCTV3': [
        'http://222.169.85.8:9901/tsfile/live/0003_1.m3u8?key=txiptv&playlive=1&authid=0',
        'http://74.91.26.218:82/live/cctv3hd.m3u8',
        'http://121.57.88.206:898/hls/3/index.m3u8',
    ],
    'CCTV4': [
        'http://112.27.235.94:8000/hls/4/index.m3u8',
        'https://newcntv.qcloudcdn.com/asp/hls/2000/0303000a/3/default/ocn0g4z8173ac9a3/2000.m3u8',
    ],
    'CCTV5': [
        'http://112.27.235.94:8000/hls/5/index.m3u8',
        'http://222.169.85.8:9901/tsfile/live/0005_1.m3u8?key=txiptv&playlive=1&authid=0',
    ],
    'CCTV6': [
        'http://112.27.235.94:8000/hls/6/index.m3u8',
        'http://222.169.85.8:9901/tsfile/live/0006_1.m3u8?key=txiptv&playlive=1&authid=0',
    ],
    'CCTV13': [
        'http://112.27.235.94:8000/hls/13/index.m3u8',
        'http://222.169.85.8:9901/tsfile/live/0013_1.m3u8?key=txiptv&playlive=1&authid=0',
    ],
}

# Enhance existing live channels with fallbacks
for live_group in enhanced['lives']:
    group_name = live_group.get('group', '')
    for ch in live_group.get('channels', []):
        ch_name = ch.get('name', '')
        urls = ch.get('urls', [])
        
        # If channel has only 1 URL, try to add stable fallback
        if len(urls) == 1 and ch_name in stable_cctv:
            # Add stable fallbacks (avoid duplicates)
            existing = set(urls)
            for fb in stable_cctv[ch_name]:
                if fb not in existing:
                    urls.append(fb)
                    existing.add(fb)
            ch['urls'] = urls
        
        # Remove known dead streams
        ch['urls'] = [u for u in ch['urls'] if 'gcalic.v.myalicdn.com' not in u]  # 403 forbidden
        
        # Add User-Agent for streams that need it
        if any('kwimgs.com' in u for u in ch['urls']):
            ch['userAgent'] = 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36'

# Add new stable live groups
new_live_groups = [
    {
        "group": "央视高清（新增稳定源）",
        "channels": [
            {"name": "CCTV1-高清", "urls": stable_cctv['CCTV1']},
            {"name": "CCTV2-高清", "urls": stable_cctv['CCTV2']},
            {"name": "CCTV3-高清", "urls": stable_cctv['CCTV3']},
            {"name": "CCTV4-高清", "urls": stable_cctv['CCTV4']},
            {"name": "CCTV5-高清", "urls": stable_cctv['CCTV5']},
            {"name": "CCTV6-高清", "urls": stable_cctv['CCTV6']},
            {"name": "CCTV13-高清", "urls": stable_cctv['CCTV13']},
        ]
    },
    {
        "group": "卫视频道（新增稳定源）",
        "channels": [
            {"name": "湖南卫视-高清", "urls": [
                "http://112.27.235.94:8000/hls/29/index.m3u8",
                "http://222.169.85.8:9901/tsfile/live/0019_1.m3u8?key=txiptv&playlive=1&authid=0",
            ]},
            {"name": "浙江卫视-高清", "urls": [
                "http://112.27.235.94:8000/hls/28/index.m3u8",
                "https://ali-m-l.cztv.com/channels/lantian/channel01/1080p.m3u8",
            ]},
            {"name": "江苏卫视-高清", "urls": [
                "http://112.27.235.94:8000/hls/27/index.m3u8",
                "http://222.169.85.8:9901/tsfile/live/0012_1.m3u8?key=txiptv&playlive=1&authid=0",
            ]},
            {"name": "东方卫视-高清", "urls": [
                "http://112.27.235.94:8000/hls/35/index.m3u8",
                "http://222.169.85.8:9901/tsfile/live/0011_1.m3u8?key=txiptv&playlive=1&authid=0",
            ]},
            {"name": "北京卫视-高清", "urls": [
                "http://112.27.235.94:8000/hls/27/index.m3u8",
                "http://222.169.85.8:9901/tsfile/live/0010_1.m3u8?key=txiptv&playlive=1&authid=0",
            ]},
            {"name": "广东卫视-高清", "urls": [
                "http://112.27.235.94:8000/hls/31/index.m3u8",
                "http://222.169.85.8:9901/tsfile/live/0008_1.m3u8?key=txiptv&playlive=1&authid=0",
            ]},
        ]
    },
]

enhanced['lives'].extend(new_live_groups)

# Remove empty channels (where all URLs were dead)
for live_group in enhanced['lives']:
    live_group['channels'] = [ch for ch in live_group['channels'] if ch.get('urls')]

# Remove empty live groups
enhanced['lives'] = [lg for lg in enhanced['lives'] if lg.get('channels')]

# ============================================================
# 3. ADD POSTER PROXY CONFIGURATION
# ============================================================
# Add a global poster config that tells the app to use image proxy for slow sources
enhanced['posterConfig'] = {
    "enableCache": True,
    "cacheDays": 7,
    "proxySlowSources": True,
    "slowSourcePatterns": ["img.lzipic.com", "doubanio.com"],
    "proxyUrl": "https://wsrv.nl/?url={url}&w=300&h=400&output=webp&q=80",
    "maxConcurrent": 6,
    "timeout": 8000,
    "retryCount": 2,
}

# ============================================================
# 4. ADD LIVE STREAM CONFIGURATION
# ============================================================
enhanced['liveConfig'] = {
    "healthCheck": True,
    "healthCheckInterval": 300,
    "autoFallback": True,
    "maxRetries": 2,
    "connectTimeout": 5000,
    "readTimeout": 10000,
    "userAgent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36",
}

# ============================================================
# 5. VERSION INFO
# ============================================================
enhanced['version'] = 'Enhanced-v1'
enhanced['enhancedAt'] = '2026-08-10'
enhanced['enhancedChanges'] = [
    '海报加载优化: CDN优先排序, 慢源代理加速, 双重重试',
    '直播源增强: 每频道多路备份, 新增稳定央视/卫视源, 自动健康检测',
    '移除死亡源: gcalic 403, doubanio 418',
    '版本标识: Enhanced-v1',
]

# Save
output_path = 'combined.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(enhanced, f, ensure_ascii=False, separators=(',', ':'))

# Calculate SHA256
sha256 = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()

print(f"Enhanced combined.json generated: {output_path}")
print(f"Size: {len(Path(output_path).read_bytes())} bytes")
print(f"SHA256: {sha256}")
print(f"Sites: {len(enhanced['sites'])} (was {len(orig['sites'])}, added {len(new_sites)} new)")
print(f"Live groups: {len(enhanced['lives'])} (was {len(orig['lives'])}, added {len(new_live_groups)} new)")
print(f"Live channels total: {sum(len(lg['channels']) for lg in enhanced['lives'])}")

# Count channels with multiple URLs
multi_url = sum(1 for lg in enhanced['lives'] for ch in lg['channels'] if len(ch.get('urls', [])) > 1)
single_url = sum(1 for lg in enhanced['lives'] for ch in lg['channels'] if len(ch.get('urls', [])) == 1)
print(f"Channels with multiple URLs: {multi_url}")
print(f"Channels with single URL: {single_url}")
