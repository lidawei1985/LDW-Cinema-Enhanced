# LDW Cinema Enhanced

光幕影院增强版仓库 — 在原版基础上增加了**更新清单数字签名**、**国内多镜像容灾**、**安全策略文档**和**自动化验证工具**。

> 本仓库是 [lidawei1985/LDW-Cinema](https://github.com/lidawei1985/LDW-Cinema) 的增强分支，用于对比验证安全改进效果。原仓库继续作为生产仓库使用。

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
