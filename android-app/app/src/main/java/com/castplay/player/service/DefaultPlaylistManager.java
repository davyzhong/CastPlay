package com.castplay.player.service;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * 默认播放列表管理器
 * 负责：
 *  1. 从 assets/default_playlist.json 读取打包的默认播放列表
 *  2. 持久化服务器下发的播放列表 JSON（含本地媒体文件路径）
 *  3. 提供"当前激活播放列表"：优先使用服务器列表，否则使用默认列表
 */
public class DefaultPlaylistManager {

    private static final String TAG = "DefaultPlaylistManager";

    // SharedPreferences 键
    private static final String PREFS_NAME = "CastPlayPrefs";
    private static final String KEY_SERVER_PLAYLIST = "server_playlist_json";
    private static final String KEY_HAS_SERVER_PLAYLIST = "has_server_playlist";
    private static final String KEY_APP_LAUNCHED = "app_launched";

    private final Context context;
    private final SharedPreferences prefs;

    public DefaultPlaylistManager(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = this.context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    // ───────────────────────────────────────────────
    //  服务器播放列表（同步成功后写入）
    // ───────────────────────────────────────────────

    /** 是否已有服务器同步的播放列表 */
    public boolean hasServerPlaylist() {
        return prefs.getBoolean(KEY_HAS_SERVER_PLAYLIST, false);
    }

    /**
     * 保存服务器同步后生成的播放列表 JSON（含本地文件路径）
     * @param playlistJson WebView 播放器可直接使用的 JSON 字符串
     */
    public void saveServerPlaylist(String playlistJson) {
        prefs.edit()
                .putString(KEY_SERVER_PLAYLIST, playlistJson)
                .putBoolean(KEY_HAS_SERVER_PLAYLIST, true)
                .apply();
        Log.d(TAG, "Server playlist saved, length=" + playlistJson.length());
    }

    /** 清除服务器播放列表，回退到默认列表 */
    public void clearServerPlaylist() {
        prefs.edit()
                .remove(KEY_SERVER_PLAYLIST)
                .putBoolean(KEY_HAS_SERVER_PLAYLIST, false)
                .apply();
        Log.d(TAG, "Server playlist cleared, will use default");
    }

    // ───────────────────────────────────────────────
    //  对外接口：获取当前激活播放列表
    // ───────────────────────────────────────────────

    /**
     * 获取当前应播放的列表 JSON：
     *  - 若有服务器列表且非空 → 返回服务器列表
     *  - 否则 → 返回 assets 中的默认列表
     */
    public String getActivePlaylistJson() {
        if (hasServerPlaylist()) {
            String serverJson = prefs.getString(KEY_SERVER_PLAYLIST, null);
            if (serverJson != null && !serverJson.isEmpty()) {
                Log.d(TAG, "Using server playlist");
                return serverJson;
            }
        }
        Log.d(TAG, "Using default playlist from assets");
        return getDefaultPlaylistJson();
    }

    /**
     * 直接读取 assets/default_playlist.json
     */
    public String getDefaultPlaylistJson() {
        try {
            InputStream is = context.getAssets().open("default_playlist.json");
            int size = is.available();
            byte[] buffer = new byte[size];
            is.read(buffer);
            is.close();
            return new String(buffer, StandardCharsets.UTF_8);
        } catch (IOException e) {
            Log.e(TAG, "Failed to read default_playlist.json from assets", e);
            // 最小兜底
            return "{\"id\":\"default\",\"name\":\"CastPlay\",\"items\":[]}";
        }
    }

    // ───────────────────────────────────────────────
    //  首次启动标记
    // ───────────────────────────────────────────────

    /** 是否首次启动（从未完成过一次完整同步）*/
    public boolean isFirstLaunch() {
        return !prefs.getBoolean(KEY_APP_LAUNCHED, false);
    }

    /** 标记首次启动同步已完成 */
    public void markFirstLaunchDone() {
        prefs.edit().putBoolean(KEY_APP_LAUNCHED, true).apply();
    }
}
