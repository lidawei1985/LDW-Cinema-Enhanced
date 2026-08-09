# TVBox 配置

此目录提供 FongMi TVBox 的远程配置入口。仓库仅保存配置、校验工具和上游 APK 元数据，不保存影视文件、账号、Cookie、密钥或未知远程代码。

## 配置地址

```text
https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/tvbox/config.json
```

## 本机应用

- 上游项目：`https://github.com/FongMi/TV`
- 发布仓库：`https://github.com/FongMi/Release`
- 版本：`5.5.6`（mobile arm64-v8a）
- Android 包名：`com.fongmi.android.tv`
- APK SHA-256：`BF0E3878F7D31DE2C7261B6A285113E8B364C8027817EC5F99F23C378B6B8259`
- Git Blob SHA-1：`53683537e1ea8ce4d70179a0a36fada4b63b7479`

## 安全规则

- 仅加入自有、公共领域或已明确授权的内容源。
- 只使用 HTTPS 地址。
- 不使用 VIP/付费内容绕过解析器。
- 不加载未知远程 JAR、脚本或可执行代码。
- 不加入涉及未成年人、偷拍、胁迫或其他非法内容的来源。

运行 `validate.ps1` 可检查 JSON 格式及上述基础规则。
