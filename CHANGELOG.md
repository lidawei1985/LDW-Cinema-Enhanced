# 变更日志

所有重要变更记录在此文件中。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

---

## [Enhanced-v1] - 2026-08-10 (第二版修复)

### 海报加载修复

- **站点重排**：Cloudflare CDN保护的源（非凡影视 `ffeiimg.com`、索泥影视 `snzic.vip`）排到最前，海报加载从 0.66s 降至 0.24s
- **死源过滤**：移除 `doubanio.com`（418反爬）、`gcalic.v.myalicdn.com`（403禁止）等死亡海报源
- **海报缓存代理**：新增 Cloudflare Worker 脚本（`tools/poster-cache-worker.js`），边缘缓存7天 + WebP压缩
- **并发控制**：海报最大并发6路、8s超时、2次重试
- **新增2个极速源**：黑木耳影视（`json.heimuer.xyz`）、华为吧影视（`json.ghpsys.com`），均Cloudflare CDN

### 直播源修复

- **多路备份**：84个频道添加2-3个备用URL（原版大量频道只有1个URL）
- **新增稳定直播组**：
  - 央视高清（新增稳定源）：CCTV1-6 + CCTV13，每频道3路备份
  - 卫视频道（新增稳定源）：湖南/浙江/江苏/东方/北京/广东，每频道2路备份
- **死源清理**：移除 `gcalic.v.myalicdn.com`（403）等不可用直播源
- **健康检测配置**：新增 `liveConfig`，5分钟自动检测 + 自动故障切换
- **User-Agent配置**：为需要UA的流（如快手源）添加UA头

### 版本标识

- 所有 manifest 文件新增 `enhancedVersion: "v1"` 和 `enhancedName: "LDW-Cinema-Enhanced-v1"` 字段
- `combined.json` 新增 `version: "Enhanced-v1"` 标识

### 其他

- 新增 `docs/POSTER_CACHE_GUIDE.md`：海报缓存代理部署指南
- 新增 `tools/poster-cache-worker.js`：Cloudflare Worker 海报缓存脚本
- 新增 `gen_combined.py`：combined.json 生成脚本
- `source-update.json` 的 `configUrl` 更新为指向增强版仓库的 `combined.json`

---

## [Enhanced-1.0] - 2026-08-10 (第一版基线)

### 新增

- **更新清单数字签名**：`update-mobile.json`、`source-update.json`、`update.json`、`releases/mobile/update-mobile.json` 全部增加 RSA-SHA256 签名
- **签名/验证工具**：`tools/generate_keys.py`（生成密钥）、`tools/sign-manifest.py`（签名清单）、`tools/verify-manifest.py`（验证签名）
- **多镜像容灾**：所有关键文件增加 3-4 个镜像 URL
  - APK 下载：GitHub Releases + ghproxy.net + mirror.ghproxy.com + jsDelivr
  - 授权数据：GitHub API + GitHub raw + jsDelivr + Gitee
  - 配置文件：GitHub raw + jsDelivr + Gitee
  - 更新清单：GitHub raw + jsDelivr + Gitee
- **安全策略文档** `SECURITY.md`：当前安全状态、密钥管理、密钥轮换流程、应急响应
- **镜像策略文档** `MIRRORS.md`：完整镜像矩阵、APP 端容灾实现示例、Gitee 同步配置
- **正式签名证书指南** `docs/RELEASE_KEYSTORE_GUIDE.md`：从 Debug 证书迁移到正式 release keystore 的完整步骤
- **网络安全配置说明** `docs/NETWORK_SECURITY.md`：禁用 HTTP 明文流量、证书锁定方案
- **Android 端参考代码** `tools/android/`：Java 验签和容灾下载参考实现
- **CI 自动签名** `.github/workflows/sign-manifests.yml`：push 时自动验证清单签名
- **.gitignore**：防止私钥意外提交
- **结构化 CHANGELOG.md**：本文件

### 变更

- `update-mobile.json`：增加 `apkUrls` 多镜像数组、`manifestVersion`、`mirrors` 块、`signature` 块
- `source-update.json`：增加 `configUrls` 多镜像数组、`manifestVersion`、`signature` 块
- `update.json`：增加 `apkUrls` 多镜像数组、`manifestVersion`、`mirrors` 块、`signature` 块
- `README.md`：完整重写，包含差异对比表、签名机制说明、快速开始指南

### 安全改进

- 更新清单从"仅哈希校验"升级为"RSA 数字签名 + 哈希校验"双重保护
- 消除 GitHub 单点依赖，国内用户通过 Gitee/ghproxy 可正常使用
- 文档化密钥轮换和泄露应急流程

---

## 原仓库历史

以下为原仓库 `lidawei1985/LDW-Cinema` 的关键变更（仅记录与安全/更新机制相关的）：

- `v248` - 手机版当前稳定版，成人模式三级片页保留原名称和原海报
- `v103` - 手机版历史版本（`releases/mobile/update-mobile.json`）
- `v56` - 电视端当前版本，修复 GitHub Release APK HTTP 404 问题
- TVBoxOSC 构建流程已移除 Thunder SDK 和不必要权限
