package com.ldw.cinema.update;

import android.content.Context;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/**
 * 多镜像更新检查器
 *
 * 工作流程：
 * 1. 从多个镜像获取 update-mobile.json
 * 2. 验证 RSA 签名
 * 3. 比较 versionCode 决定是否需要更新
 * 4. 从 apkUrls 列表依次尝试下载 APK
 * 5. 下载后验证 SHA256
 *
 * 用法：
 *   UpdateChecker checker = new UpdateChecker(context);
 *   UpdateInfo info = checker.checkForUpdates();
 *   if (info != null && info.hasUpdate()) {
 *       checker.downloadApk(info);
 *   }
 */
public class UpdateChecker {

    private static final String TAG = "UpdateChecker";

    // 更新清单镜像 URL（按优先级排序）
    private static final String[] MANIFEST_URLS = {
        "https://raw.githubusercontent.com/lidawei1985/LDW-Cinema/main/update-mobile.json",
        "https://cdn.jsdelivr.net/gh/lidawei1985/LDW-Cinema@main/update-mobile.json",
        "https://gitee.com/lidawei1985/LDW-Cinema/raw/main/update-mobile.json"
    };

    private final Context context;
    private final OkHttpClient client;
    private final int currentVersionCode;

    public UpdateChecker(Context context, int currentVersionCode) {
        this.context = context;
        this.currentVersionCode = currentVersionCode;
        this.client = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .build();
    }

    /**
     * 检查更新
     * @return 更新信息，null 表示检查失败
     */
    public UpdateInfo checkForUpdates() {
        for (String url : MANIFEST_URLS) {
            try {
                Log.i(TAG, "Fetching manifest from: " + url);
                String json = fetchUrl(url);
                JSONObject manifest = new JSONObject(json);

                // 验证签名
                if (!ManifestVerifier.verify(manifest, context)) {
                    Log.w(TAG, "Signature verification failed for " + url);
                    continue;
                }

                int versionCode = manifest.optInt("versionCode", -1);
                String versionName = manifest.optString("versionName", "");
                String changelog = manifest.optString("changelog", "");
                String sha256 = manifest.optString("sha256", "").toUpperCase();
                int minSupported = manifest.optInt("minimumSupportedVersionCode", 0);

                // 收集 APK 下载 URL
                List<String> apkUrls = new ArrayList<>();
                if (manifest.has("apkUrls")) {
                    JSONArray urls = manifest.getJSONArray("apkUrls");
                    for (int i = 0; i < urls.length(); i++) {
                        apkUrls.add(urls.getString(i));
                    }
                }
                if (apkUrls.isEmpty() && manifest.has("apkUrl")) {
                    apkUrls.add(manifest.getString("apkUrl"));
                }

                boolean hasUpdate = versionCode > currentVersionCode;
                boolean mustUpdate = currentVersionCode < minSupported;

                Log.i(TAG, "Manifest OK: v" + versionName + " (code=" + versionCode +
                      ") hasUpdate=" + hasUpdate + " urls=" + apkUrls.size());

                return new UpdateInfo(versionCode, versionName, changelog,
                        sha256, apkUrls, hasUpdate, mustUpdate);

            } catch (Exception e) {
                Log.w(TAG, "Failed: " + url, e);
            }
        }

        Log.e(TAG, "All manifest mirrors failed");
        return null;
    }

    private String fetchUrl(String url) throws Exception {
        Request request = new Request.Builder()
                .url(url)
                .header("Cache-Control", "no-cache")
                .header("User-Agent", "LDW-Cinema-Mobile")
                .build();
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful() || response.body() == null) {
                throw new RuntimeException("HTTP " + response.code());
            }
            return response.body().string();
        }
    }

    /**
     * 更新信息
     */
    public static class UpdateInfo {
        public final int versionCode;
        public final String versionName;
        public final String changelog;
        public final String sha256;
        public final List<String> apkUrls;
        public final boolean hasUpdate;
        public final boolean mustUpdate;

        UpdateInfo(int versionCode, String versionName, String changelog,
                   String sha256, List<String> apkUrls,
                   boolean hasUpdate, boolean mustUpdate) {
            this.versionCode = versionCode;
            this.versionName = versionName;
            this.changelog = changelog;
            this.sha256 = sha256;
            this.apkUrls = apkUrls;
            this.hasUpdate = hasUpdate;
            this.mustUpdate = mustUpdate;
        }
    }
}
