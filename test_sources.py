#!/usr/bin/env python3
"""Test all potential VOD API sources - fixed version."""
import json
import time
import ssl
import gzip
import io
import urllib.request
import urllib.error
import socket

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

socket.setdefaulttimeout(10)

SOURCES = [
    ("非凡影视", "https://api.ffzyapi.com/api.php/provide/vod/"),
    ("索尼影视", "https://suoniapi.com/api.php/provide/vod/"),
    ("量子影视", "https://cj.lziapi.com/api.php/provide/vod/"),
    ("黑木耳", "https://json.heimuer.xyz/api.php/provide/vod/"),
    ("华为吧", "https://json.ghpsys.com/api.php/provide/vod/"),
    ("虎牙资源", "https://www.huyaapi.com/api.php/provide/vod/at/json"),
    ("暴风资源", "https://bfzyapi.com/api.php/provide/vod/"),
    ("极速资源", "https://jszyapi.com/api.php/provide/vod/"),
    ("红牛资源", "https://www.hongniuzy2.com/api.php/provide/vod/"),
    ("飞速资源", "https://www.feisuzyapi.com/api.php/provide/vod/"),
    ("快车资源", "https://caiji.kczyapi.com/api.php/provide/vod/"),
    ("新浪资源", "https://api.xinlangapi.com/xinlangapi.php/provide/vod/"),
    ("无尽影视", "https://api.wujinapi.com/api.php/provide/vod/"),
    ("旺旺资源", "https://api.wwzy.tv/api.php/provide/vod/"),
    ("樱花资源", "https://m3u8.apiyhzy.com/api.php/provide/vod/"),
    ("百度云资源", "https://api.apibdzy.com/api.php/provide/vod/"),
    ("茅台资源", "https://caiji.maotaizy.cc/api.php/provide/vod/"),
    ("豪华资源", "https://hhzyapi.com/api.php/provide/vod"),
    ("U酷资源", "https://api.ukuapi.com/api.php/provide/vod/"),
    ("牛牛资源", "https://api.niuniuzy.me/api.php/provide/vod/"),
    ("丫丫资源", "https://cj.yayazy.net/api.php/provide/vod/"),
    ("ikun资源", "https://ikunzyapi.com/api.php/provide/vod/"),
    ("闪电资源", "https://sdzyapi.com/api.php/provide/vod/from/sdm3u8"),
    ("光速资源", "https://api.guangsuapi.com/api.php/provide/vod/from/gsm3u8"),
    ("森林资源", "https://slapibf.com/api.php/provide/vod/"),
    ("卧龙资源", "https://collect.wolongzyw.com/api.php/provide/vod/"),
    ("金鹰资源", "https://jyzyapi.com/provide/vod/from/jinyingm3u8"),
    ("旺旺短剧", "https://wwzy.tv/api.php/provide/vod/"),
    ("快播资源", "https://www.kuaibozy.com/api.php/provide/vod/"),
    ("猫眼资源", "https://api.maoyanapi.top/api.php/provide/vod/"),
    ("老鸭资源", "https://api.apilyzy.com/api.php/provide/vod/"),
    ("天空资源", "https://api.tkzyapi.com/api.php/provide/vod/"),
    ("百川资源", "https://abczy8.com/api.php/provide/vod/"),
    ("猎人资源", "https://app.lieyingzy.com/api.php/provide/vod/"),
    ("小黄人", "https://iqyi.xiaohuangrentv.com/api.php/provide/vod/"),
    ("四九资源", "https://49zyw.com/api.php/provide/vod/"),
    ("熊掌资源", "https://xzcjz.com/api.php/provide/vod/"),
    ("奥斯卡", "https://aosikazy.com/api.php/provide/vod/"),
    ("北斗星", "https://m3u8.bdxzyapi.com/api.php/provide/vod/"),
    ("唐人街", "https://tangrenjie.tv/api.php/provide/vod/"),
    ("酷点资源", "https://api.kuapi.cc/api.php/provide/vod/"),
    ("探探资源", "https://apittzy.com/api.php/provide/vod/"),
    ("影库资源", "https://api.ykapi.net/api.php/provide/vod/"),
    ("海阔资源", "https://hkjx.tv/api.php/provide/vod/"),
    ("无尽资源", "https://api.wujinapi.me/api.php/provide/vod/"),
]

results = []

for name, url in SOURCES:
    test_url = url + "?ac=list&pg=1"
    try:
        t0 = time.time()
        req = urllib.request.Request(test_url, headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        raw = resp.read()
        # Handle gzip
        if resp.headers.get("Content-Encoding") == "gzip":
            try:
                raw = gzip.decompress(raw)
            except:
                pass
        elapsed = time.time() - t0
        text = raw.decode("utf-8", errors="replace")
        
        # Try to parse as JSON
        try:
            j = json.loads(text)
            total = j.get("total", 0)
            code = j.get("code", 0)
            class_count = len(j.get("class", []))
            list_count = len(j.get("list", []))
            status = "OK" if code == 1 else f"CODE_{code}"
            print(f"  {status:10s} | {elapsed:5.2f}s | {name:10s} | total={total:>8} | cls={class_count} | list={list_count}")
            results.append({
                "name": name, "url": url, "status": status,
                "elapsed": round(elapsed, 2), "total": total,
                "classes": class_count, "list": list_count,
            })
        except json.JSONDecodeError:
            # Check if it's HTML (redirect/error page)
            if "<html" in text.lower() or "<!doctype" in text.lower():
                print(f"  HTML_PAGE  | {elapsed:5.2f}s | {name:10s} | {url}")
                results.append({"name": name, "url": url, "status": "HTML", "elapsed": round(elapsed, 2), "total": 0})
            else:
                # Maybe it returned partial JSON or XML
                print(f"  PARTIAL    | {elapsed:5.2f}s | {name:10s} | len={len(text)} | {text[:80]}")
                results.append({"name": name, "url": url, "status": "PARTIAL", "elapsed": round(elapsed, 2), "total": 0})
    except urllib.error.HTTPError as e:
        print(f"  HTTP_{e.code:3d}  | ----- | {name:10s} | {url}")
        results.append({"name": name, "url": url, "status": f"HTTP_{e.code}", "elapsed": 0, "total": 0})
    except Exception as e:
        err = str(e)[:60]
        print(f"  ERROR      | ----- | {name:10s} | {err}")
        results.append({"name": name, "url": url, "status": "ERROR", "elapsed": 0, "total": 0})

ok_sources = [r for r in results if r["status"] == "OK"]
ok_sources.sort(key=lambda x: x["elapsed"])
print(f"\n{'='*80}")
print(f"WORKING SOURCES: {len(ok_sources)}/{len(SOURCES)}")
print(f"{'='*80}")
for r in ok_sources:
    print(f"  {r['elapsed']:5.2f}s | {r['name']:10s} | total={r['total']:>8} | classes={r['classes']} | {r['url']}")

with open("source_test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nResults saved to source_test_results.json")
