# 网络安全配置

## 禁用 HTTP 明文流量

### 配置文件

在 Android 项目中创建 `app/src/main/res/xml/network_security_config.xml`：

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- 全局禁用明文 HTTP 流量 -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- 仅允许特定域名使用明文（如有必要） -->
    <!-- 尽可能不配置任何例外 -->

    <!-- 证书锁定（可选，增强安全性） -->
    <domain-config>
        <domain includeSubdomains="true">raw.githubusercontent.com</domain>
        <pin-set expiration="2027-12-31">
            <!-- GitHub 的公钥哈希 -->
            <pin digest="SHA-256">2kOi4HdYYsvtr1RBy6nUDrZZxYxtCBk1t1VYQ1cYQhc=</pin>
            <!-- 备用公钥（密钥轮换时使用） -->
            <pin digest="SHA-256">YlhZpYj5hGq6USIcn5dZ丛生的另一个公钥哈希=</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```

### 在 AndroidManifest.xml 中引用

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="false"
    ... >
    ...
</application>
```

---

## 证书锁定 (Certificate Pinning)

### OkHttp 配置

在 APP 的 OkHttpClient 中配置证书锁定：

```java
public class HttpClient {

    private static OkHttpClient client;

    public static synchronized OkHttpClient getClient() {
        if (client == null) {
            CertificatePinner certificatePinner = new CertificatePinner.Builder()
                // GitHub raw
                .add("raw.githubusercontent.com",
                    "sha256/2kOi4HdYYsvtr1RBy6nUDrZZxYxtCBk1t1VYQ1cYQhc=")
                // jsDelivr CDN
                .add("cdn.jsdelivr.net",
                    "sha256/+vXyXmQLnQFwWAOYpDdY1dCa4pc6Io3bkQpujA3+RSc=")
                // Gitee
                .add("gitee.com",
                    "sha256/填入Gitee的证书公钥哈希=")
                // GitHub API
                .add("api.github.com",
                    "sha256/填入GitHub API的证书公钥哈希=")
                .build();

            client = new OkHttpClient.Builder()
                .certificatePinner(certificatePinner)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
        }
        return client;
    }
}
```

### 获取证书公钥哈希

```bash
# 方法 1: 用 openssl
echo | openssl s_client -connect raw.githubusercontent.com:443 2>/dev/null \
  | openssl x509 -pubkey -noout \
  | openssl pkey -pubin -outform der \
  | openssl dgst -sha256 -binary \
  | openssl base64

# 方法 2: 用 Python
python3 -c "
import ssl, hashlib, base64
cert = ssl.get_server_certificate(('raw.githubusercontent.com', 443))
# ... 提取公钥并计算 SHA256
"

# 方法 3: 用 OkHttp 的 CertificatePinner.getKeyHash
```

**注意：** 证书锁定可能导致 CDN 证书轮换后 APP 无法连接。建议：
1. 设置 `expiration` 日期
2. 配置备用 pin（backup pin）
3. 监控证书变更

---

## 当前 HTTP 使用情况

从 APK 分析发现，APP 中存在以下 HTTP 使用情况：

| 组件 | 当前 | 目标 | 优先级 |
|------|------|------|--------|
| 更新清单获取 | HTTPS | HTTPS | ✅ 已合规 |
| 授权验证 | HTTPS | HTTPS | ✅ 已合规 |
| 部分影视源接口 | HTTP | HTTPS | 需要源站支持 |
| 直播流地址 | HTTP/RTMP | HTTPS/RTSP | 需要源站支持 |

**建议：** 对于第三方影视源和直播流，APP 层面无法强制 HTTPS，但应在 `network_security_config.xml` 中为已知支持 HTTPS 的域名禁用明文。

---

## AndroidManifest 安全属性清单

建议在 `<application>` 标签中设置以下属性：

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="false"
    android:allowBackup="false"
    android:debuggable="false"
    android:extractNativeLibs="true"
    android:fullBackupContent="false"
    ... >
```

| 属性 | 值 | 说明 |
|------|-----|------|
| `usesCleartextTraffic` | `false` | 禁止明文 HTTP |
| `allowBackup` | `false` | 禁止 adb backup 提取数据 |
| `debuggable` | `false` | release 版禁止调试 |
| `fullBackupContent` | `false` | 禁止全量备份 |

---

## 检查清单

- [ ] 创建 `network_security_config.xml`
- [ ] 在 AndroidManifest 中引用
- [ ] 设置 `usesCleartextTraffic="false"`
- [ ] 配置 OkHttp 证书锁定
- [ ] 设置 `allowBackup="false"`
- [ ] 确认 release 构建 `debuggable="false"`
- [ ] 测试所有 HTTPS 连接正常
- [ ] 配置证书锁定备用 pin
