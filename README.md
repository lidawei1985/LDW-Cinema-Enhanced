# LDW Cinema Enhanced v2

**光幕影院增强版 v2** — 在 v1 基础上大幅扩充内容源（23个已验证VOD源）、新增外部直播源（IPV6/IPV4 + EPG + 台标）、新增5个解析器，并继续优化海报加载和直播稳定性。

> 本仓库是 [lidawei1985/LDW-Cinema](https://github.com/lidawei1985/LDW-Cinema) 的增强分支（v2），用于对比验证改进效果。原仓库继续作为生产仓库使用。

---

## v2 核心改进

### 1. 内容源大扩充（5 → 23 个已验证源）

v1 仅有 5 个普通内容源，v2 通过全网测试验证了 23 个可用源，按响应速度排序：

| # | 源名 | API 域名 | 响应时间 | 资源总量 |
|---|------|---------|---------|---------|
| 1 | 索尼影视 | suoniapi.com | 0.25s | 142,238 |
| 2 | 虎牙资源 | huyaapi.com | 0.25s | 109,036 |
| 3 | 无尽影视 | wujinapi.com | 0.25s | 117,717 |
| 4 | 金鹰资源 | jyzyapi.com | 0.25s | 110,096 |
| 5 | 量子影视 | lziapi.com | 0.35s | 148,593 |
| 6 | 豪华资源 | hhzyapi.com | 0.36s | 109,131 |
| 7 | 猫眼资源 | maoyanapi.top | 0.42s | 33,738 |
| 8 | 百度云资源 | apibdzy.com | 0.43s | 47,977 |
| 9 | 红牛资源 | hongniuzy2.com | 0.46s | 109,520 |
| 10 | ikun资源 | ikunzyapi.com | 0.53s | 66,545 |
| 11 | 光速资源 | guangsuapi.com | 0.53s | 110,096 |
| 12 | 牛牛资源 | niuniuzy.me | 0.54s | 121,713 |
| 13 | 丫丫资源 | yayazy.net | 0.55s | 119,753 |
| 14 | 极速资源 | jszyapi.com | 0.61s | 108,362 |
| 15 | U酷资源 | ukuapi.com | 0.63s | 56,237 |
| 16 | 非凡影视 | ffzyapi.com | 0.64s | 97,697 |
| 17 | 闪电资源 | sdzyapi.com | 0.67s | 121,477 |
| 18 | 樱花资源 | apiyhzy.com | 0.73s | 101,607 |
| 19 | 暴风资源 | bfzyapi.com | 0.75s | 153,794 |
| 20 | 新浪资源 | xinlangapi.com | 0.87s | 110,100 |
| 21 | 森林资源 | slapibf.com | 0.98s | 249,637 |
| 22 | 茅台资源 | maotaizy.cc | 1.29s | 139,489 |

所有源均经过实测验证：响应 code=1、返回 JSON 格式、资源总量 > 30,000。

### 2. 外部直播源（EPG + 台标）

v2 新增 3 个外部直播源，支持 EPG 电子节目单和台标自动匹配：

| 直播源 | 类型 | 说明 |
|--------|------|------|
| IPV6直播源（央视卫视高清） | m3u | 中国移动 OTT 高清源，含央视全部频道 + 31个卫视 |
| IPV4直播源 | txt | 通用 IPTV 列表 |
| IPV6备用直播源 | m3u | 备用 IPV6 源 |

- EPG: `http://epg.51zmt.top:8000/api/diyp/?ch={name}&date={date}`
- 台标: `https://live.fanmingming.com/tv/{name}.png`

### 3. 解析器扩充（12 → 18 个）

新增 5 个解析接口：虾米解析、夜幕解析、CK解析、全民解析、M3U8解析。

### 4. 手机体验优化

- 所有 22 个普通源均开启 `searchable=1` + `quickSearch=1` + `filterable=1`
- 源按响应速度从快到慢排序，首页加载最快
- 海报并发控制（6路并发、8s超时、2次重试、占位图回退）

---

## v1 核心修复（保留）

### 1. 海报加载优化

| 问题 | 原因 | v1 修复方案 |
|------|------|-------------|
| 海报加载极慢 | 部分海报服务器无CDN缓存（`img.lzipic.com` 0.66s） | **站点重排**：Cloudflare CDN源优先（`ffeiimg.com` 0.24s） |
| 海报不显示 | `doubanio.com` 返回418反爬 | **死源过滤**：自动替换占位图 |
| 每次重新加载 | APK无本地海报缓存 | **海报缓存代理**：Cloudflare Worker边缘缓存7天 |
| 并发加载卡顿 | 同时下载20+张海报 | **并发限制**：最多6路并发 + 8s超时 + 2次重试 |

详见 [docs/POSTER_CACHE_GUIDE.md](docs/POSTER_CACHE_GUIDE.md)

### 2. 直播源稳定性

| 问题 | 原因 | v1 修复方案 |
|------|------|-------------|
| 直播卡死/不可用 | 大量频道只有1个URL，断了就没了 | **多路备份**：84个频道添加2-3个备用URL |
| IP地址流断流 | 裸IP流（`112.27.235.94`）IP变更即死 | **CDN替换**：新增CDN-backed稳定源 |
| 403 Forbidden | `gcalic.v.myalicdn.com` 禁止访问 | **死源移除**：自动清理403/418源 |
| 无健康检测 | 不知道哪些源还活着 | **健康检测配置**：5分钟自动检测 + 自动故障切换 |

### 3. 新增内容源

| 源名 | API | 海报CDN | 说明 |
|------|-----|---------|------|
| 黑木耳影视 | `json.heimuer.xyz` | Cloudflare | 极速海报加载 |
| 华为吧影视 | `json.ghpsys.com` | Cloudflare | 备用高速源 |

### 4. 新增稳定直播源

| 组名 | 频道数 | 说明 |
|------|--------|------|
| 央视高清（新增稳定源） | 7 | CCTV1-6 + CCTV13，每频道3路备份 |
| 卫视频道（新增稳定源） | 6 | 湖南/浙江/江苏/东方/北京/广东，每频道2路备份 |

---

## 与原仓库的核心差异

| 改进点 | 原仓库 | 增强版 |
|--------|--------|--------|
| 更新清单完整性 | 仅 SHA256 哈希 | **RSA-SHA256 数字签名** + SHA256 |
| APK 下载源 | GitHub 单一来源 | **4 路镜像**（GitHub + ghproxy×2 + jsDelivr） |
| 授权数据源 | 3 路（GitHub API/raw/jsDelivr） | **4 路**（增加 Gitee 镜像） |
| 配置文件源 | raw.githubusercontent 单路 | **3 路**（raw + jsDelivr + Gitee） |
| 签名密钥管理 | 无 | 专用 RSA 密钥对 + 签名/验证工具 |
| 安全文档 | 无 | `SECURITY.md` + `MIRRORS.md` + keystore 指南 |
| 变更日志 | 散落在 commit message | 结构化 `CHANGELOG.md` |
| CI/CD | 仅构建 TVBoxOSC | 增加 **manifest 自动签名** workflow |

---

## 目录结构

```
.
├── update-mobile.json          # 手机版更新清单（已签名 + 多镜像）
├── update.json                 # 电视版更新清单（已签名 + 多镜像）
├── source-update.json          # 数据源同步清单（已签名 + 多镜像）
├── mobile-licenses.json        # 授权数据（RSA 签名信封）
├── combined.json               # TVBox 正式配置
├── releases/                   # 已发布 APK
├── tvboxosc-build/             # TVBoxOSC 构建脚本
├── tvbox/                      # TVBox 配置文件
├── tools/                      # 【新增】签名与验证工具
│   ├── generate_keys.py        #     生成 RSA 密钥对
│   ├── sign-manifest.py        #     签名更新清单
│   ├── verify-manifest.py      #     验证签名
│   ├── android/                #     Android 端参考代码
│   └── keys/
│       └── update_public_key.pem  #  公钥（可公开）
├── docs/                       # 【新增】文档目录
│   ├── RELEASE_KEYSTORE_GUIDE.md  # 正式签名证书生成指南
│   └── NETWORK_SECURITY.md     #    网络安全配置说明
├── .github/workflows/
│   ├── build-tvboxosc.yml      # TVBoxOSC 构建（原有）
│   └── sign-manifests.yml      # 【新增】清单自动签名 CI
├── SECURITY.md                 # 【新增】安全策略
├── MIRRORS.md                  # 【新增】镜像策略说明
├── CHANGELOG.md                # 【新增】变更日志
└── README.md                   # 本文件
```

---

## 更新清单签名机制

### 为什么需要签名？

原仓库的 `update-mobile.json` 只有 `sha256` 字段做完整性校验。但 SHA256 只是哈希——如果攻击者篡改了 JSON 内容，同时替换 sha256 值，APP 无法察觉。

增强版增加了 **RSA-SHA256 数字签名**：清单内容用私钥签名，APP 用内置公钥验签。即使 GitHub 被劫持或 DNS 被污染，攻击者没有私钥就无法伪造有效签名。

### 签名格式

```json
{
  "versionCode": 248,
  "apkUrl": "https://...",
  "sha256": "9D3591...",
  "signature": {
    "algorithm": "SHA256withRSA",
    "keyId": "update-key-v1",
    "value": "base64..."
  }
}
```

- `algorithm`: 签名算法，当前为 `SHA256withRSA`（PKCS#1 v1.5 + SHA-256）
- `keyId`: 密钥标识，用于密钥轮换时 APP 选择正确的公钥
- `value`: Base64 编码的签名值
- 签名覆盖除 `signature` 字段外的所有内容，使用排序键 + 紧凑 JSON 的规范序列化

### 如何签名

```bash
# 安装依赖
pip install cryptography

# 签名（需要私钥）
python tools/sign-manifest.py update-mobile.json

# 验证（只需要公钥）
python tools/verify-manifest.py update-mobile.json

# 验证远程文件
python tools/verify-manifest.py update-mobile.json --remote
```

### 向后兼容

签名字段是附加的——旧版 APP 读取清单时忽略 `signature` 字段，功能不受影响。新版 APP 可以选择验签，验签失败时拒绝更新。

---

## 多镜像容灾

### 原版的问题

所有 URL 指向 `github.com` 或 `raw.githubusercontent.com`。GitHub 在中国大陆访问不稳定时：
- 授权验证超时 → APP 无法启动
- 更新检查失败 → 用户无法获取新版本
- 配置同步失败 → 频道列表过期

### 增强版的方案

每个关键文件提供 3-4 个镜像 URL，APP 按顺序尝试：

| 文件类型 | 镜像 1 | 镜像 2 | 镜像 3 | 镜像 4 |
|----------|--------|--------|--------|--------|
| 更新清单 | GitHub raw | jsDelivr CDN | Gitee | - |
| APK 下载 | GitHub Releases | ghproxy.net | mirror.ghproxy.com | jsDelivr |
| 授权数据 | GitHub API | GitHub raw | jsDelivr | Gitee |
| 配置文件 | GitHub raw | jsDelivr | Gitee | - |

详见 [MIRRORS.md](MIRRORS.md)。

---

## 安全建议

1. **生成正式 release keystore** — 当前 APK 使用 Android Debug 证书签名，任何人都能生成相同证书重签。详见 [docs/RELEASE_KEYSTORE_GUIDE.md](docs/RELEASE_KEYSTORE_GUIDE.md)。

2. **启用 ProGuard 混淆** — 在 `app/build.gradle` 中开启 `minifyEnabled true`，增加反编译难度。

3. **禁用 HTTP 明文流量** — 使用 `network_security_config.xml` 强制 HTTPS。详见 [docs/NETWORK_SECURITY.md](docs/NETWORK_SECURITY.md)。

4. **证书锁定 (Certificate Pinning)** — 在 OkHttp 中配置公钥锁定，防止中间人攻击。

---

## 快速开始

### 验证更新清单

```bash
# 克隆仓库
git clone https://github.com/lidawei1985/LDW-Cinema-Enhanced.git
cd LDW-Cinema-Enhanced

# 验证所有清单签名
python tools/verify-manifest.py update-mobile.json
python tools/verify-manifest.py source-update.json
python tools/verify-manifest.py update.json
```

### 发布新版本时签名

```bash
# 1. 修改 update-mobile.json（更新版本号、sha256、changelog 等）
# 2. 签名
python tools/sign-manifest.py update-mobile.json
# 3. 验证
python tools/verify-manifest.py update-mobile.json
# 4. 提交并推送
git add update-mobile.json
git commit -m "publish mobile vXXX"
git push
```

---

## License

本项目仅用于个人使用。
