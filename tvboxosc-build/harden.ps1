$ErrorActionPreference = 'Stop'

$appGradle = 'app/build.gradle'
$gradle = Get-Content -LiteralPath $appGradle -Raw
$gradle = $gradle.Replace('    api fileTree(dir: "libs", include: ["*.jar"])' + "`n", '')
$gradle = $gradle.Replace("    implementation files('libs\\thunder.jar')" + "`n", '')
$gradle = [regex]::Replace($gradle, "(?ms)^\s*implementation\('org\.xwalk:xwalk_shared_library:[^']+'\)\s*\{.*?^\s*\}\s*", '')
$gradle = $gradle.Replace("dependencies {", "dependencies {`n    implementation files('libs/xwalk_shared_library-23.53.589.4.aar')")
$gradle = $gradle.Replace(
    "    implementation 'com.orhanobut:hawk:2.0.1'",
    "    implementation('com.orhanobut:hawk:2.0.1') { exclude group: 'com.facebook.conceal' }"
)
Set-Content -LiteralPath $appGradle -Value $gradle -Encoding UTF8

$rootGradlePath = 'build.gradle'
$rootGradle = Get-Content -LiteralPath $rootGradlePath -Raw
$mirrorBlock = @'
        maven { url 'https://maven.aliyun.com/repository/google' }
        maven { url 'https://maven.aliyun.com/repository/public' }
        maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
        maven { url 'https://maven.aliyun.com/repository/jcenter' }
'@
$rootGradle = $rootGradle.Replace('        gradlePluginPortal()', $mirrorBlock + "`n        gradlePluginPortal()")
Set-Content -LiteralPath $rootGradlePath -Value $rootGradle -Encoding UTF8

$crosswalkBase = 'https://raw.githubusercontent.com/o0HalfLife0o/crosswalk/master/releases/crosswalk/android/maven2/org/xwalk/xwalk_shared_library/23.53.589.4'
$crosswalkDir = 'app/libs'
New-Item -ItemType Directory -Path $crosswalkDir -Force | Out-Null
Invoke-WebRequest -Uri "$crosswalkBase/xwalk_shared_library-23.53.589.4.aar" -OutFile "$crosswalkDir/xwalk_shared_library-23.53.589.4.aar"

# Crosswalk's archived AAR includes an ARM-only conceal helper that is not
# required for its Java API and makes x86_64 Android reject the whole APK.
Add-Type -AssemblyName System.IO.Compression
$xwalkAar = Resolve-Path "$crosswalkDir/xwalk_shared_library-23.53.589.4.aar"
$xwalkZip = [System.IO.Compression.ZipFile]::Open($xwalkAar, [System.IO.Compression.ZipArchiveMode]::Update)
$xwalkZip.Entries | Where-Object { $_.FullName -like 'jni/*/libconceal.so' } | ForEach-Object { $_.Delete() }
$xwalkZip.Dispose()

$appPath = 'app/src/main/java/com/github/tvbox/osc/base/App.java'
$appSource = Get-Content -LiteralPath $appPath -Raw
$appSource = $appSource.Replace(
    'import com.orhanobut.hawk.Hawk;',
    "import com.orhanobut.hawk.Hawk;`nimport com.orhanobut.hawk.NoEncryption;"
)
$appSource = $appSource.Replace('Hawk.init(this).build();', 'Hawk.init(this).setEncryption(new NoEncryption()).build();')
$appSource = $appSource.Replace(
    'Hawk.put(HawkConfig.DEBUG_OPEN, false);',
    "Hawk.put(HawkConfig.DEBUG_OPEN, false);`n        if (!Hawk.contains(HawkConfig.API_URL)) {`n            Hawk.put(HawkConfig.API_URL, `"asset://configs/1741901263936.json`");`n            java.util.ArrayList<String> bundledConfigs = new java.util.ArrayList<>();`n            bundledConfigs.add(`"asset://configs/1741901263936.json`");`n            bundledConfigs.add(`"asset://configs/zcwe.json`");`n            bundledConfigs.add(`"asset://configs/all.json`");`n            bundledConfigs.add(`"asset://configs/1131.json`");`n            bundledConfigs.add(`"asset://configs/cs1.json`");`n            bundledConfigs.add(`"asset://configs/cse.json`");`n            bundledConfigs.add(`"asset://configs/豆包改版.json`");`n            Hawk.put(HawkConfig.API_HISTORY, bundledConfigs);`n        }"
)
Set-Content -LiteralPath $appPath -Value $appSource -Encoding UTF8

$assetConfigDir = 'app/src/main/assets/configs'
New-Item -ItemType Directory -Path $assetConfigDir -Force | Out-Null
Get-ChildItem -LiteralPath '..' -Filter '*.json' -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $assetConfigDir -Force
}

$apiConfigPath = 'app/src/main/java/com/github/tvbox/osc/api/ApiConfig.java'
$apiConfig = Get-Content -LiteralPath $apiConfigPath -Raw
$apiConfig = $apiConfig.Replace('import java.io.BufferedReader;', "import java.io.BufferedReader;`nimport java.io.ByteArrayOutputStream;")
$apiConfig = $apiConfig.Replace('import java.io.InputStreamReader;', "import java.io.InputStream;`nimport java.io.InputStreamReader;")
$assetLoader = @'
        if (apiUrl.startsWith("asset://")) {
            String assetPath = apiUrl.substring("asset://".length());
            try (InputStream input = App.getInstance().getAssets().open(assetPath)) {
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int count;
                while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
                parseJson(apiUrl, output.toString("UTF-8"));
                callback.success();
            } catch (Throwable error) {
                callback.error("Cannot load bundled config: " + error.getMessage());
            }
            return;
        }
'@
$cacheLine = '        File cache = new File(App.getInstance().getFilesDir().getAbsolutePath() + "/" + MD5.encode(apiUrl));'
$apiConfig = $apiConfig.Replace($cacheLine, $assetLoader + $cacheLine)
$apiConfig = $apiConfig.Replace('for (JsonElement opt : infoJson.get("sites").getAsJsonArray()) {', 'for (JsonElement opt : infoJson.has("sites") ? infoJson.get("sites").getAsJsonArray() : new JsonArray()) {')
$apiConfig = $apiConfig.Replace('for (JsonElement opt : infoJson.get("parses").getAsJsonArray()) {', 'for (JsonElement opt : infoJson.has("parses") ? infoJson.get("parses").getAsJsonArray() : new JsonArray()) {')
$apiConfig = $apiConfig.Replace('for (JsonElement host : infoJson.getAsJsonArray("ads")) {', 'for (JsonElement host : infoJson.has("ads") ? infoJson.getAsJsonArray("ads") : new JsonArray()) {')
$apiConfig = $apiConfig.Replace('for (JsonElement opt : infoJson.get("ijk").getAsJsonArray()) {', 'for (JsonElement opt : infoJson.has("ijk") ? infoJson.get("ijk").getAsJsonArray() : new JsonArray()) {')
Set-Content -LiteralPath $apiConfigPath -Value $apiConfig -Encoding UTF8

$apiDialogPath = 'app/src/main/java/com/github/tvbox/osc/ui/dialog/ApiDialog.java'
$apiDialog = Get-Content -LiteralPath $apiDialogPath -Raw
$apiDialog = $apiDialog.Replace('(newApi.startsWith("http") || newApi.startsWith("clan"))', '(newApi.startsWith("http") || newApi.startsWith("clan") || newApi.startsWith("asset://"))')
Set-Content -LiteralPath $apiDialogPath -Value $apiDialog -Encoding UTF8

$playerGradlePath = 'player/build.gradle'
$playerGradle = Get-Content -LiteralPath $playerGradlePath -Raw
$playerGradle = [regex]::Replace($playerGradle, '(?m)^\s*api "com\.google\.android\.exoplayer:extension-rtmp:[^"]+"\r?\n?', '')
Set-Content -LiteralPath $playerGradlePath -Value $playerGradle -Encoding UTF8

$exoHelperPath = 'player/src/main/java/xyz/doikki/videoplayer/exo/ExoMediaSourceHelper.java'
$exoHelper = Get-Content -LiteralPath $exoHelperPath -Raw
$exoHelper = [regex]::Replace($exoHelper, '(?m)^import com\.google\.android\.exoplayer2\.ext\.rtmp\.RtmpDataSourceFactory;\r?\n', '')
$exoHelper = [regex]::Replace(
    $exoHelper,
    '(?ms)\s*if \("rtmp"\.equals\(contentUri\.getScheme\(\)\)\) \{.*?\}\s*else if \("rtsp"\.equals\(contentUri\.getScheme\(\)\)\) \{',
    "`n        if (`"rtsp`".equals(contentUri.getScheme())) {"
)
Set-Content -LiteralPath $exoHelperPath -Value $exoHelper -Encoding UTF8

$manifestPath = 'app/src/main/AndroidManifest.xml'
$manifest = Get-Content -LiteralPath $manifestPath -Raw
$manifest = $manifest.Replace(
    '<manifest xmlns:android="http://schemas.android.com/apk/res/android"',
    '<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools"'
)
$permissions = @(
    'android.permission.READ_PHONE_STATE',
    'android.permission.READ_EXTERNAL_STORAGE',
    'android.permission.WRITE_EXTERNAL_STORAGE',
    'android.permission.ACCESS_FINE_LOCATION',
    'android.permission.REQUEST_INSTALL_PACKAGES',
    'android.permission.GET_TASKS'
)
foreach ($permission in $permissions) {
    $pattern = '(?m)^\s*<uses-permission android:name="' + [regex]::Escape($permission) + '"\s*/>\r?\n?'
    $manifest = [regex]::Replace($manifest, $pattern, '')
}
$removeNodes = ($permissions | ForEach-Object {
    '    <uses-permission android:name="' + $_ + '" tools:node="remove" />'
}) -join "`n"
$manifest = $manifest.Replace(
    '    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />',
    '    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />' + "`n" + $removeNodes
)
Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8

$thunderPath = 'app/src/main/java/com/github/tvbox/osc/util/thunder/Thunder.java'
@'
package com.github.tvbox.osc.util.thunder;

import android.content.Context;

/** Disables the opaque bundled Thunder/magnet implementation. */
public final class Thunder {
    private Thunder() {}

    public interface ThunderCallback {
        void status(int code, String info);
        void list(String playList);
        void play(String url);
    }

    public static void parse(Context context, String url, ThunderCallback callback) {
        if (callback != null) callback.status(-1, "Unsupported link type");
    }

    public static boolean play(String url, ThunderCallback callback) {
        return false;
    }

    public static boolean isSupportUrl(String url) {
        return false;
    }
}
'@ | Set-Content -LiteralPath $thunderPath -Encoding UTF8

if (Test-Path 'app/libs/thunder.jar') {
    Remove-Item -LiteralPath 'app/libs/thunder.jar'
}

# The preserved project bundles ARM-only opaque player/Thunder libraries. They
# are not used by the HTTPS/HLS/RTSP playback path and prevent x86_64 install.
if (Test-Path 'app/src/main/jniLibs') {
    Remove-Item -LiteralPath 'app/src/main/jniLibs' -Recurse -Force
}
if (Test-Path 'player/src/main/jniLibs') {
    Remove-Item -LiteralPath 'player/src/main/jniLibs' -Recurse -Force
}
