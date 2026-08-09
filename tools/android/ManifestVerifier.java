package com.ldw.cinema.update;

import android.content.Context;
import android.util.Base64;
import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.Signature;
import java.security.spec.X509EncodedKeySpec;
import java.util.Iterator;

/**
 * 更新清单签名验证器
 *
 * 用法：
 *   boolean valid = ManifestVerifier.verify(jsonString, context);
 *
 * APP 内置公钥：res/raw/update_public_key.pem
 */
public final class ManifestVerifier {

    private static final String TAG = "ManifestVerifier";
    private static final String ALGORITHM = "SHA256withRSA";
    private static final String KEY_ID = "update-key-v1";

    private ManifestVerifier() {}

    /**
     * 验证 JSON 字符串格式的更新清单
     *
     * @param jsonString 清单 JSON 字符串
     * @param context    Android Context（用于读取内置公钥）
     * @return true = 签名有效, false = 签名无效或无签名
     */
    public static boolean verify(String jsonString, Context context) {
        try {
            JSONObject manifest = new JSONObject(jsonString);
            return verify(manifest, getPublicKey(context));
        } catch (Exception e) {
            Log.e(TAG, "Parse error", e);
            return false;
        }
    }

    /**
     * 验证已解析的更新清单
     *
     * @param manifest   清单 JSON 对象
     * @param publicKey  RSA 公钥
     * @return true = 签名有效
     */
    public static boolean verify(JSONObject manifest, PublicKey publicKey) {
        if (!manifest.has("signature")) {
            Log.w(TAG, "No signature field in manifest");
            return false;
        }

        try {
            JSONObject sig = manifest.getJSONObject("signature");
            String algorithm = sig.getString("algorithm");
            String keyId = sig.getString("keyId");
            String value = sig.getString("value");

            if (!ALGORITHM.equals(algorithm)) {
                Log.e(TAG, "Unsupported algorithm: " + algorithm);
                return false;
            }
            if (!KEY_ID.equals(keyId)) {
                Log.e(TAG, "Unknown keyId: " + keyId);
                return false;
            }

            // 构建规范序列化（排除 signature 字段，排序键，紧凑格式）
            String canonical = canonicalJson(manifest);

            byte[] signatureBytes = Base64.decode(value, Base64.DEFAULT);
            byte[] dataBytes = canonical.getBytes("UTF-8");

            Signature verifier = Signature.getInstance(ALGORITHM);
            verifier.initVerify(publicKey);
            verifier.update(dataBytes);

            boolean result = verifier.verify(signatureBytes);
            if (result) {
                Log.i(TAG, "Manifest signature valid");
            } else {
                Log.e(TAG, "Manifest signature INVALID");
            }
            return result;

        } catch (Exception e) {
            Log.e(TAG, "Verification error", e);
            return false;
        }
    }

    /**
     * 构建规范 JSON：排除 signature 字段，键名排序，紧凑格式
     * 与 Python 端 canonical_bytes() 保持一致
     */
    private static String canonicalJson(JSONObject manifest) throws JSONException {
        // 复制所有字段（排除 signature）
        JSONObject copy = new JSONObject();
        Iterator<String> keys = manifest.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            if (!"signature".equals(key)) {
                copy.put(key, manifest.get(key));
            }
        }

        // 排序键并紧凑输出
        return sortKeysCompact(copy);
    }

    /**
     * 递归排序 JSON 键并紧凑序列化
     */
    private static String sortKeysCompact(JSONObject obj) throws JSONException {
        StringBuilder sb = new StringBuilder("{");
        String[] keys = new String[obj.length()];
        int i = 0;
        for (Iterator<String> it = obj.keys(); it.hasNext(); ) {
            keys[i++] = it.next();
        }
        java.util.Arrays.sort(keys);

        for (int j = 0; j < keys.length; j++) {
            if (j > 0) sb.append(",");
            sb.append("\"").append(keys[j]).append("\":");
            Object val = obj.get(keys[j]);
            sb.append(valueToJson(val));
        }
        sb.append("}");
        return sb.toString();
    }

    @SuppressWarnings("unchecked")
    private static String valueToJson(Object val) throws JSONException {
        if (val == null) return "null";
        if (val instanceof String) return jsonString((String) val);
        if (val instanceof Boolean) return val.toString();
        if (val instanceof Number) {
            // JSON 数字：整数不带小数点
            if (val instanceof Integer || val instanceof Long) {
                return val.toString();
            }
            return val.toString();
        }
        if (val instanceof JSONObject) return sortKeysCompact((JSONObject) val);
        if (val instanceof org.json.JSONArray) {
            org.json.JSONArray arr = (org.json.JSONArray) val;
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < arr.length(); i++) {
                if (i > 0) sb.append(",");
                sb.append(valueToJson(arr.get(i)));
            }
            sb.append("]");
            return sb.toString();
        }
        return jsonString(val.toString());
    }

    private static String jsonString(String s) {
        StringBuilder sb = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\r': sb.append("\\r");  break;
                case '\t': sb.append("\\t");  break;
                default:
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
            }
        }
        sb.append("\"");
        return sb.toString();
    }

    /**
     * 从 res/raw/update_public_key.pem 读取公钥
     */
    private static PublicKey getPublicKey(Context context) throws Exception {
        // 将 tools/keys/update_public_key.pem 复制到 app/src/main/res/raw/
        int resId = context.getResources()
                .getIdentifier("update_public_key", "raw", context.getPackageName());
        java.io.InputStream is = context.getResources().openRawResource(resId);
        byte[] pemBytes = readAll(is);

        // 去除 PEM 头尾
        String pem = new String(pemBytes, "UTF-8")
                .replace("-----BEGIN PUBLIC KEY-----", "")
                .replace("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");
        byte[] derBytes = Base64.decode(pem, Base64.DEFAULT);

        X509EncodedKeySpec spec = new X509EncodedKeySpec(derBytes);
        KeyFactory factory = KeyFactory.getInstance("RSA");
        return factory.generatePublic(spec);
    }

    private static byte[] readAll(java.io.InputStream is) throws Exception {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = is.read(buf)) != -1) bos.write(buf, 0, n);
        is.close();
        return bos.toByteArray();
    }
}
