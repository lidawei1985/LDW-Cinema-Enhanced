# 镜像策略

## 概述

本仓库的所有关键文件通过多个 CDN 和镜像分发，确保在单一源不可达时 APP 仍能正常工作。本文档说明每个文件的镜像列表和容灾策略。

---

## 文件镜像矩阵

### 1. 更新清单 (`update-mobile.json`)

| 优先级 | URL | 类型 | 说明 |
|--------|-----|------|------|
| 1 | `https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json` | GitHub raw | 原始源，权威 |
| 2 | `https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/update-mobile.json` | jsDelivr CDN | 全球 CDN 加速 |
| 3 | `https://gitee.com/lidawei1985/LDW-Cinema/raw/main/update-mobile.json` | Gitee | 国内镜像 |

### 2. APK 下载

| 优先级 | URL 模式 | 类型 | 说明 |
|--------|----------|------|------|
| 1 | `https://github.com/lidawei1985/LDW-Cinema/releases/download/v{version}/LDW-Cinema-Mobile-v{code}.apk` | GitHub Releases | 原始源 |
| 2 | `https://ghproxy.net/https://github.com/lidawei1985/LDW-Cinema/releases/download/v{version}/...` | ghproxy.net | GitHub 代理 |
| 3 | `https://mirror.ghproxy.com/https://github.com/lidawei1985/LDW-Cinema/releases/download/v{version}/...` | mirror.ghproxy.com | GitHub 代理备选 |
| 4 | `https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/releases/mobile/LDW-Cinema-Mobile-v{code}.apk` | jsDelivr CDN | 仓库内 APK（<50MB 限制） |

### 3. 授权数据 (`mobile-licenses.json`)

| 优先级 | URL | 类型 | 说明 |
|--------|-----|------|------|
| 1 | `https://api.github.com/repos/lidawei1985/LDW-Cinema/contents/mobile-licenses.json?ref=main` | GitHub API | 返回 base64 编码内容 |
| 2 | `https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/mobile-licenses.json` | GitHub raw | 原始文件 |
| 3 | `https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/mobile-licenses.json` | jsDelivr CDN | CDN 加速 |
| 4 | `https://gitee.com/lidawei1985/LDW-Cinema/raw/main/mobile-licenses.json` | Gitee | 国内镜像 |

### 4. 配置文件 (`combined.json`)

| 优先级 | URL | 类型 | 说明 |
|--------|-----|------|------|
| 1 | `https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/combined.json` | GitHub raw | 原始源 |
| 2 | `https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/combined.json` | jsDelivr CDN | CDN 加速 |
| 3 | `https://gitee.com/lidawei1985/LDW-Cinema/raw/main/combined.json` | Gitee | 国内镜像 |

### 5. 电视端更新清单 (`update.json`)

| 优先级 | URL | 类型 | 说明 |
|--------|-----|------|------|
| 1 | `https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update.json` | GitHub raw | 原始源 |
| 2 | `https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/update.json` | jsDelivr CDN | CDN 加速 |
| 3 | `https://gitee.com/lidawei1985/LDW-Cinema/raw/main/update.json` | Gitee | 国内镜像 |

---

## APP 端容灾逻辑（推荐实现）

```java
/**
 * 多镜像容灾下载器
 * 按优先级依次尝试 URL 列表，全部失败才返回错误。
 */
public class MirrorDownloader {

    /**
     * 从多个镜像获取 JSON 内容
     * @param urls 镜像 URL 列表（按优先级排序）
     * @param timeoutMs 单个 URL 超时
     * @return 第一个成功获取的内容
     */
    public static String fetchJsonWithFallback(String[] urls, int timeoutMs) {
        Exception lastError = null;
        for (String url : urls) {
            try {
                OkHttpClient client = new OkHttpClient.Builder()
                        .connectTimeout(timeoutMs, TimeUnit.MILLISECONDS)
                        .readTimeout(timeoutMs, TimeUnit.MILLISECONDS)
                        .build();
                Request request = new Request.Builder()
                        .url(url)
                        .header("Cache-Control", "no-cache")
                        .header("User-Agent", "LDW-Cinema-Mobile")
                        .build();
                try (Response response = client.newCall(request).execute()) {
                    if (response.isSuccessful() && response.body() != null) {
                        return response.body().string();
                    }
                }
            } catch (Exception e) {
                lastError = e;
                Log.w("MirrorDownloader", "Failed: " + url, e);
            }
        }
        throw new RuntimeException("All mirrors failed", lastError);
    }

    /**
     * 验证更新清单签名后返回
     */
    public static JSONObject fetchAndVerifyManifest(String[] urls, PublicKey publicKey) {
        for (String url : urls) {
            try {
                String json = fetchJsonWithFallback(new String[]{url}, 15000);
                JSONObject manifest = new JSONObject(json);
                if (ManifestVerifier.verify(manifest, publicKey)) {
                    return manifest;
                }
            } catch (Exception e) {
                Log.w("MirrorDownloader", "Verify failed for " + url, e);
            }
        }
        throw new RuntimeException("No valid signed manifest from any mirror");
    }
}
```

---

## Gitee 镜像设置

### 自动同步

在 Gitee 上创建仓库后，使用 Gitee 的「强制同步」功能从 GitHub 同步：

1. 在 Gitee 创建 `lidawei1985/LDW-Cinema` 仓库
2. 选择「导入已有仓库」→ 输入 GitHub 仓库地址
3. 同步完成后，每次 GitHub push 后手动或定时触发 Gitee 同步

### GitHub Action 自动同步

在 `.github/workflows/` 中添加同步 action（需要 Gitee token）：

```yaml
name: Sync to Gitee
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Sync to Gitee
        uses: Yikun/hub-mirror-action@master
        with:
          src: github/lidawei1985
          dst: gitee/lidawei1985
          dst_key: ${{ secrets.GITEE_PRIVATE_KEY }}
          dst_token: ${{ secrets.GITEE_TOKEN }}
          mappings: "LDW-Cinema=>LDW-Cinema"
          force_update: true
```

---

## 镜像可靠性参考

| 镜像 | 中国大陆速度 | 全球速度 | 可靠性 | 文件大小限制 |
|------|-------------|---------|--------|-------------|
| GitHub raw | 慢/不稳定 | 快 | 高 | 100MB |
| GitHub Releases | 慢/不稳定 | 快 | 高 | 2GB |
| jsDelivr CDN | 快 | 快 | 高 | 50MB（仓库内文件） |
| ghproxy.net | 快 | 中 | 中 | 无限制 |
| mirror.ghproxy.com | 快 | 中 | 中 | 无限制 |
| Gitee raw | 快 | 中 | 高 | 100MB |
