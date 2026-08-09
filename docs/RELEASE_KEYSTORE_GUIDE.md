# 正式签名证书 (Release Keystore) 生成指南

## 为什么需要正式证书？

当前 APK 使用 Android Debug 证书签名（`CN=Android Debug`），这存在严重安全问题：

1. **无法验证来源**：任何人都能生成相同的 Debug 证书，篡改 APK 后重签
2. **无法升级**：换用正式证书后，旧用户无法直接升级（签名不一致）
3. **不被商店接受**：Google Play 等应用商店不接受 Debug 证书签名的 APK
4. **自动更新冲突**：下载的新 APK 签名不一致会导致安装失败

---

## 生成步骤

### 1. 生成 release keystore

```bash
keytool -genkeypair \
  -alias ldw-release \
  -keyalg RSA \
  -keysize 2048 \
  -validity 36500 \
  -keystore ldw-release.keystore \
  -storepass YOUR_STORE_PASSWORD \
  -keypass YOUR_KEY_PASSWORD \
  -dname "CN=LDW Cinema, OU=Development, O=LDW, L=Beijing, ST=Beijing, C=CN"
```

**参数说明：**
- `-alias`: 密钥别名，后续签名时使用
- `-keysize 2048`: RSA 2048 位（最低安全要求）
- `-validity 36500`: 有效期 100 年（避免证书过期导致无法升级）
- `-storepass` / `-keypass`: 设置强密码
- `-dname`: 证书持有者信息

### 2. 安全保管 keystore

```bash
# 备份到多个安全位置
cp ldw-release.keystore /secure/backup/ldw-release.keystore
cp ldw-release.keystore /cloud/backup/ldw-release.keystore

# 设置文件权限
chmod 600 ldw-release.keystore
```

**⚠️ 关键：**
- keystore 文件丢失 = 永远无法更新已安装的 APP
- 密码丢失 = 同上
- 务必备份到多个独立位置

### 3. 在 Gradle 中配置签名

在 `app/build.gradle` 中添加：

```gradle
android {
    signingConfigs {
        release {
            storeFile file("ldw-release.keystore")
            storePassword System.getenv("LDW_STORE_PASSWORD")
            keyAlias "ldw-release"
            keyPassword System.getenv("LDW_KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 4. 在 CI/CD 中安全使用

**绝不要把 keystore 提交到仓库。** 使用 GitHub Secrets：

```yaml
# .github/workflows/build-release.yml
- name: Decode keystore
  run: echo "${{ secrets.LDW_KEYSTORE_BASE64 }}" | base64 -d > app/ldw-release.keystore

- name: Build release APK
  env:
    LDW_STORE_PASSWORD: ${{ secrets.LDW_STORE_PASSWORD }}
    LDW_KEY_PASSWORD: ${{ secrets.LDW_KEY_PASSWORD }}
  run: ./gradlew assembleRelease
```

将 keystore 文件 base64 编码后存入 GitHub Secrets：
```bash
base64 -w0 ldw-release.keystore
# 将输出复制到 GitHub repo Settings → Secrets → Actions → LDW_KEYSTORE_BASE64
```

### 5. 验证签名

```bash
# 查看 APK 签名证书
keytool -printcert -jarfile LDW-Cinema-Mobile-v248.apk

# 预期输出应包含：
# Owner: CN=LDW Cinema, OU=Development, O=LDW, L=Beijing, ST=Beijing, C=CN
# 而不是：CN=Android Debug
```

---

## 迁移策略（从 Debug 到 Release 证书）

由于签名证书变更后旧用户无法直接升级，需要以下策略：

### 方案 A：渐进式迁移（推荐）

1. 用 Debug 证书发布最后一个版本（v249），在 APP 内内置 release 公钥
2. APP 启动时检查：如果当前签名是 Debug 证书，提示用户"即将升级到增强安全版本"
3. 下载 release 签名的 v250 APK，引导用户卸载旧版后安装新版
4. 之后的更新全部使用 release 证书

### 方案 B：强制重装

1. 直接用 release 证书发布新版
2. 在更新说明中告知用户需要卸载旧版后安装
3. 简单粗暴，用户体验差

### 方案 C：使用 Android 签名方案 v2/v3 的密钥轮换

Android 9+ 支持签名密钥轮换（`apksigner rotate`），但仅对 v2+ 签名方案有效，且旧系统不支持。不推荐在需要兼容旧 Android 版本时使用。

---

## ProGuard 混淆配置

生成 release APK 时应同时启用 ProGuard：

```proguard
# app/proguard-rules.pro

# 保留核心 API 入口
-keep class com.ldw.cinema.** { *; }
-keep class com.github.tvbox.osc.api.** { *; }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**

# Gson
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.google.gson.** { *; }

# 移除调试日志
-assumenosideeffects class android.util.Log {
    public static *** v(...);
    public static *** d(...);
    public static *** i(...);
}
```

---

## 检查清单

- [ ] 生成 release keystore（RSA 2048，100 年有效期）
- [ ] 备份 keystore 到至少 2 个独立位置
- [ ] 记录密码到安全位置（密码管理器）
- [ ] 在 Gradle 中配置 signingConfigs
- [ ] 在 CI/CD 中配置 secrets
- [ ] 启用 ProGuard 混淆
- [ ] 用 release 证书签名第一个版本
- [ ] 验证 `keytool -printcert` 输出非 Debug 证书
- [ ] 制定用户迁移方案
