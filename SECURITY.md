# 安全策略

## 报告安全漏洞

如果发现安全漏洞，请**不要**在 GitHub Issues 中公开报告。请通过以下方式私密报告：

1. 在 GitHub 上创建 Security Advisory（Security 标签页 → Report a vulnerability）
2. 或直接在 Issues 中标记为 private

我们会在收到报告后 48 小时内回复。

---

## 当前安全状态

### ✅ 已实施

| 措施 | 说明 |
|------|------|
| 授权数据 RSA 签名 | `mobile-licenses.json` 使用 SHA256withRSA 签名信封，防篡改 |
| 更新清单 RSA 签名 | `update-mobile.json`、`source-update.json`、`update.json` 均有数字签名 |
| 多镜像容灾 | 4 路 APK 下载 + 4 路授权验证 + 3 路配置同步 |
| 授权防回放 | 使用 `issuedAt` 时间戳，取最新版本 |
| 权限最小化 (TVBoxOSC) | 构建脚本移除电话、位置、存储、安装包等不必要权限 |
| Thunder SDK 禁用 | TVBoxOSC 构建版本移除了迅雷不透明 SDK |

### ⚠️ 待改进

| 措施 | 优先级 | 说明 |
|------|--------|------|
| 正式 release keystore | **P0** | 当前 APK 使用 Debug 证书签名，无法保证来源真实性 |
| ProGuard 混淆 | **P1** | DEX 可被 jadx 一键反编译，类名/方法名完全暴露 |
| 禁用 HTTP 明文流量 | **P1** | 部分接口仍使用 HTTP，可被中间人窃听 |
| 证书锁定 (Pinning) | **P2** | OkHttp 未配置证书锁定，CA 被攻破时可被 MITM |
| 硬编码密钥检查 | **P2** | 需审计 DEX 中是否有硬编码 API key 或密码 |

---

## 密钥管理

### 更新签名密钥

| 文件 | 用途 | 存放位置 |
|------|------|----------|
| `update_private_key.pem` | 签名更新清单 | **本地保管，绝不提交仓库** |
| `update_public_key.pem` | 验证更新签名 | `tools/keys/` 目录，公开 |
| `private_key.pem` (授权) | 签名授权数据 | 授权管理器本地，绝不提交 |

### 密钥轮换流程

1. 生成新密钥对：`python tools/generate_keys.py`
2. 用新私钥重新签名所有清单
3. 更新 APP 内置公钥（增加新 keyId，保留旧 keyId 一段时间）
4. 发布 APP 更新
5. 旧用户升级后，移除旧公钥

### 密钥泄露应急

1. 立即用新密钥重新签名所有清单
2. 在 APP 更新中内置新公钥并标记旧 keyId 为 revoked
3. 发布强制更新（`minimumSupportedVersionCode` 提高）
4. 审计历史清单是否被篡改

---

## APK 签名证书

### 当前状态（需修复）

```
签名证书: CN=Android Debug
类型: Android Debug Keystore（默认调试密钥）
有效期: 30 年（但 Debug 证书不被 Google Play 接受）
风险: 任何人都能生成相同的 Debug 证书重签 APK
```

### 目标状态

生成正式 release keystore，用正式密钥签名所有发布版本。详见 [docs/RELEASE_KEYSTORE_GUIDE.md](docs/RELEASE_KEYSTORE_GUIDE.md)。

---

## 更新验证流程（推荐 APP 端实现）

```
1. 从多个镜像获取 update-mobile.json
2. 验证 RSA 签名（使用内置公钥）
   ├── 签名无效 → 拒绝更新，尝试下一个镜像
   └── 签名有效 → 继续
3. 检查 versionCode > 当前版本
4. 从 apkUrls 列表依次尝试下载 APK
5. 下载完成后验证 SHA256
   ├── 哈希不匹配 → 删除文件，尝试下一个 URL
   └── 哈希匹配 → 提示安装
6. 安装前系统会验证 APK 签名证书
```
