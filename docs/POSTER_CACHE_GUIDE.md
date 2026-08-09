# 海报缓存加速部署指南

## 问题
海报每次进入 APK 加载极慢或完全不显示，原因：
1. 部分海报服务器无 CDN 缓存（如 `img.lzipic.com`），每次重新下载
2. 部分海报源已死亡（如 `doubanio.com` 返回 418 反爬）
3. APK 无本地海报缓存，每次启动都重新加载全部图片

## 解决方案

### 方案 A：Cloudflare Worker 代理（推荐，免费）

1. **注册 Cloudflare 账号**：https://dash.cloudflare.com/sign-up（免费）

2. **创建 Worker**：
   - 进入 Workers & Pages → Create Worker
   - 将 `tools/poster-cache-worker.js` 的内容粘贴到编辑器
   - 点击 Save and Deploy

3. **获取 Worker URL**：格式类似 `https://ldw-poster.your-name.workers.dev`

4. **更新配置**：
   在 `combined.json` 的 `posterConfig.proxyUrl` 中填入：
   ```json
   "proxyUrl": "https://ldw-poster.your-name.workers.dev/?url={url}&w=300&h=400&output=webp&q=80"
   ```

5. **效果**：
   - 首次加载海报后，Cloudflare 全球边缘节点缓存 7 天
   - 之后每次加载从最近的边缘节点返回，延迟 < 50ms
   - 自动压缩为 WebP 格式，体积减少 50-70%
   - 死亡海报源自动返回占位图，不再卡白屏

### 方案 B：使用公共图片代理（无需部署）

直接使用 `wsrv.nl`（免费公共图片代理）：
```json
"proxyUrl": "https://wsrv.nl/?url={url}&w=300&h=400&output=webp&q=80"
```

缺点：不如自建 Worker 稳定，有速率限制。

### 方案 C：站点排序优化（已内置）

已将 Cloudflare CDN 保护的源排在最前：
- `非凡影视`（`tupian.ffeiimg.com` → Cloudflare，0.24s）→ 第 1 优先
- `索泥影视`（`snzypic.vip` → Cloudflare，0.24s）→ 第 2 优先
- `量子影视`（`img.lzipic.com` → 无缓存，0.66s）→ 降为第 3 备用

## 配置项说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `enableCache` | 启用海报缓存 | true |
| `cacheDays` | 缓存天数 | 7 |
| `proxySlowSources` | 对慢源使用代理 | true |
| `slowSourcePatterns` | 慢源匹配规则 | `["img.lzipic.com", "doubanio.com"]` |
| `proxyUrl` | 代理 URL 模板 | wsrv.nl |
| `maxConcurrent` | 最大并发加载数 | 6 |
| `timeout` | 单张超时（ms） | 8000 |
| `retryCount` | 失败重试次数 | 2 |
