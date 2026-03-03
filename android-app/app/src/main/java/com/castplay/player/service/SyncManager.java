package com.castplay.player.service;

import android.content.Context;
import android.util.Log;

import com.castplay.player.data.db.AppDatabase;
import com.castplay.player.data.db.entity.MediaFileEntity;
import com.castplay.player.data.db.entity.PlaylistEntity;
import com.castplay.player.data.model.InitResponse;
import com.castplay.player.network.ApiService;
import com.castplay.player.network.RetrofitClient;

import org.json.JSONArray;
import org.json.JSONObject;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

import java.io.*;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 同步管理器
 * 职责：
 *  1. 调用 /api/player/init，获取当前设备的播放列表
 *  2. 将媒体文件下载到 filesDir/media/ 目录
 *  3. 构建包含本地文件路径的播放列表 JSON，供 WebView 播放器使用
 *  4. 通过 SyncCallback 向调用方报告进度和结果
 */
public class SyncManager {

    private static final String TAG = "SyncManager";

    private final Context context;
    private final AppDatabase database;
    private final ApiService apiService;
    private final String deviceId;
    private final ExecutorService executor;

    public SyncManager(Context context, String deviceId) {
        this.context    = context.getApplicationContext();
        this.deviceId   = deviceId;
        this.database   = AppDatabase.getInstance(context);
        this.apiService = RetrofitClient.getInstance().getApiService();
        this.executor   = Executors.newSingleThreadExecutor();
    }

    // ────────────────────────────────────────────────
    //  公开接口
    // ────────────────────────────────────────────────

    /**
     * 执行完整同步流程：
     *  1. 向服务器请求播放列表
     *  2. 下载媒体文件到本地
     *  3. 生成播放列表 JSON（含 local:/// 路径）
     *  4. 回调通知调用方
     */
    public void performFullSync(SyncCallback callback) {
        Log.d(TAG, "Starting full sync for device: " + deviceId);

        Call<InitResponse> call = apiService.playerInit(
                new ApiService.InitRequest(deviceId));

        call.enqueue(new Callback<InitResponse>() {
            @Override
            public void onResponse(Call<InitResponse> call,
                                   Response<InitResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    InitResponse initResponse = response.body();
                    List<InitResponse.PlaylistData> playlists = initResponse.getPlaylists();

                    // 服务器未分配播放列表
                    if (playlists == null || playlists.isEmpty()) {
                        Log.w(TAG, "No playlists assigned to this device");
                        if (callback != null) {
                            callback.onSyncFailed("no_playlist");
                        }
                        return;
                    }

                    executor.execute(() -> {
                        try {
                            // Step 1: 更新 Room 数据库
                            notifyProgress(callback, 10, "正在更新播放列表...");
                            updatePlaylists(playlists);

                            // Step 2: 下载媒体文件
                            notifyProgress(callback, 20, "正在下载媒体文件...");
                            downloadMediaFiles(playlists, callback);

                            // Step 3: 构建 WebView 播放器 JSON
                            notifyProgress(callback, 95, "正在生成播放器配置...");
                            String playlistJson = buildPlayerJson(playlists);

                            Log.d(TAG, "Sync completed successfully");
                            notifyProgress(callback, 100, "同步完成");

                            if (callback != null) {
                                callback.onSyncSuccess(playlistJson,
                                        initResponse.getSchedule());
                            }
                        } catch (Exception e) {
                            Log.e(TAG, "Sync failed", e);
                            if (callback != null) {
                                callback.onSyncFailed(e.getMessage());
                            }
                        }
                    });

                } else {
                    Log.e(TAG, "Init request failed: " + response.code());
                    if (callback != null) {
                        callback.onSyncFailed("server_error:" + response.code());
                    }
                }
            }

            @Override
            public void onFailure(Call<InitResponse> call, Throwable t) {
                Log.e(TAG, "Init request network error", t);
                if (callback != null) {
                    callback.onSyncFailed(t.getMessage());
                }
            }
        });
    }

    // ────────────────────────────────────────────────
    //  私有方法：更新 Room DB
    // ────────────────────────────────────────────────

    private void updatePlaylists(List<InitResponse.PlaylistData> playlists) {
        List<Integer> activeIds = new ArrayList<>();

        for (InitResponse.PlaylistData pd : playlists) {
            PlaylistEntity pe = new PlaylistEntity();
            pe.setId(pd.getId());
            pe.setName(pd.getName());
            pe.setVersion(pd.getVersion());
            pe.setLastUpdated(System.currentTimeMillis());
            database.playlistDao().insert(pe);
            activeIds.add(pd.getId());

            for (InitResponse.PlaylistItemData item : pd.getItems()) {
                MediaFileEntity mfe = new MediaFileEntity();
                mfe.setId(item.getMediaId());
                mfe.setPlaylistId(pd.getId());
                mfe.setFileName(item.getFileName());
                mfe.setFileType(item.getFileType());
                mfe.setFileUrl(item.getFileUrl());
                mfe.setDisplayOrder(item.getDisplayOrder());
                mfe.setDisplayDuration(item.getDisplayDuration());
                mfe.setFileSize(item.getFileSize());
                mfe.setMd5Hash(item.getMd5Hash());
                mfe.setDownloaded(false);
                database.mediaFileDao().insert(mfe);
            }
        }

        if (!activeIds.isEmpty()) {
            database.mediaFileDao().deleteInactivePlaylists(activeIds);
        }
        Log.d(TAG, "Playlists updated in DB: " + playlists.size());
    }

    // ────────────────────────────────────────────────
    //  私有方法：下载媒体文件
    // ────────────────────────────────────────────────

    private void downloadMediaFiles(List<InitResponse.PlaylistData> playlists,
                                    SyncCallback callback) {
        File mediaDir = new File(context.getFilesDir(), "media");
        if (!mediaDir.exists()) {
            mediaDir.mkdirs();
        }

        // 计算总文件数，用于进度报告
        int total = 0;
        for (InitResponse.PlaylistData pd : playlists) {
            total += pd.getItems().size();
        }

        int done = 0;
        for (InitResponse.PlaylistData pd : playlists) {
            for (InitResponse.PlaylistItemData item : pd.getItems()) {
                done++;
                int percent = 20 + (int) (done * 70.0 / Math.max(total, 1));
                notifyProgress(callback, percent,
                        "下载 (" + done + "/" + total + "): " + item.getFileName());

                MediaFileEntity mfe = database.mediaFileDao()
                        .getByPlaylistId(pd.getId())
                        .stream()
                        .filter(m -> m.getId() == item.getMediaId())
                        .findFirst()
                        .orElse(null);

                if (mfe == null) continue;
                if (mfe.isDownloaded() && mfe.getFilePath() != null
                        && new File(mfe.getFilePath()).exists()) {
                    Log.d(TAG, "Already downloaded: " + item.getFileName());
                    continue;
                }

                File localFile = new File(mediaDir,
                        item.getMediaId() + "_" + item.getFileName());

                // 检查文件是否已存在且 MD5 匹配
                if (localFile.exists() && verifyMD5(localFile, item.getMd5Hash())) {
                    mfe.setFilePath(localFile.getAbsolutePath());
                    mfe.setDownloaded(true);
                    database.mediaFileDao().update(mfe);
                    Log.d(TAG, "File verified from disk: " + item.getFileName());
                    continue;
                }

                try {
                    downloadFile(item.getMediaId(), localFile);
                    if (verifyMD5(localFile, item.getMd5Hash())) {
                        mfe.setFilePath(localFile.getAbsolutePath());
                        mfe.setDownloaded(true);
                        database.mediaFileDao().update(mfe);
                        Log.d(TAG, "Downloaded: " + item.getFileName());
                    } else {
                        Log.e(TAG, "MD5 mismatch: " + item.getFileName());
                        localFile.delete();
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Download failed: " + item.getFileName(), e);
                }
            }
        }
    }

    // ────────────────────────────────────────────────
    //  私有方法：生成 WebView 播放器 JSON
    // ────────────────────────────────────────────────

    /**
     * 将第一个有下载完成媒体文件的播放列表转换为 WebView 播放器所需的 JSON。
     * file_url 使用 local:/// 前缀（指向 filesDir）。
     */
    private String buildPlayerJson(List<InitResponse.PlaylistData> playlists) {
        try {
            for (InitResponse.PlaylistData pd : playlists) {
                JSONArray itemsArr = new JSONArray();
                boolean hasDownloaded = false;

                for (InitResponse.PlaylistItemData item : pd.getItems()) {
                    // 从数据库获取已下载的文件路径
                    List<MediaFileEntity> dbList = database.mediaFileDao()
                            .getByPlaylistId(pd.getId());

                    MediaFileEntity mfe = dbList.stream()
                            .filter(m -> m.getId() == item.getMediaId())
                            .findFirst()
                            .orElse(null);

                    String fileUrl;
                    if (mfe != null && mfe.isDownloaded() && mfe.getFilePath() != null) {
                        // 已下载 → 转换为 local:/// 相对路径
                        String absPath = mfe.getFilePath();
                        String filesDir = context.getFilesDir().getAbsolutePath();
                        String rel = absPath.startsWith(filesDir)
                                ? absPath.substring(filesDir.length()) // e.g. /media/5_file.mp4
                                : absPath;
                        // 去掉开头的 /
                        if (rel.startsWith("/")) rel = rel.substring(1);
                        fileUrl = "local:///" + rel;
                        hasDownloaded = true;
                    } else {
                        // 未下载成功 → 使用服务器 URL
                        fileUrl = item.getFileUrl();
                    }

                    JSONObject obj = new JSONObject();
                    obj.put("id",              item.getId());
                    obj.put("media_id",        item.getMediaId());
                    obj.put("media_name",      item.getFileName());
                    obj.put("media_type",      item.getFileType());
                    obj.put("file_url",        fileUrl);
                    obj.put("display_duration", item.getDisplayDuration());
                    obj.put("display_order",   item.getDisplayOrder());
                    itemsArr.put(obj);
                }

                if (hasDownloaded) {
                    JSONObject result = new JSONObject();
                    result.put("id",    pd.getId());
                    result.put("name",  pd.getName());
                    result.put("items", itemsArr);
                    return result.toString();
                }
            }

            // 没有任何已下载文件，使用服务器 URL
            InitResponse.PlaylistData first = playlists.get(0);
            JSONArray arr = new JSONArray();
            for (InitResponse.PlaylistItemData item : first.getItems()) {
                JSONObject obj = new JSONObject();
                obj.put("id",              item.getId());
                obj.put("media_id",        item.getMediaId());
                obj.put("media_name",      item.getFileName());
                obj.put("media_type",      item.getFileType());
                obj.put("file_url",        item.getFileUrl());
                obj.put("display_duration", item.getDisplayDuration());
                obj.put("display_order",   item.getDisplayOrder());
                arr.put(obj);
            }
            JSONObject result = new JSONObject();
            result.put("id",    first.getId());
            result.put("name",  first.getName());
            result.put("items", arr);
            return result.toString();

        } catch (Exception e) {
            Log.e(TAG, "Failed to build player JSON", e);
            return "{\"id\":0,\"name\":\"error\",\"items\":[]}";
        }
    }

    // ────────────────────────────────────────────────
    //  私有工具方法
    // ────────────────────────────────────────────────

    private void downloadFile(int mediaId, File outputFile) throws IOException {
        Call<ResponseBody> call = apiService.downloadMedia(mediaId);
        Response<ResponseBody> response = call.execute();

        if (response.isSuccessful() && response.body() != null) {
            try (InputStream in  = response.body().byteStream();
                 FileOutputStream out = new FileOutputStream(outputFile)) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) != -1) {
                    out.write(buf, 0, n);
                }
            }
        } else {
            throw new IOException("Download failed: " + response.code());
        }
    }

    private boolean verifyMD5(File file, String expectedMd5) {
        if (expectedMd5 == null || expectedMd5.isEmpty()) return true;
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            try (FileInputStream fis = new FileInputStream(file)) {
                byte[] buf = new byte[4096];
                int n;
                while ((n = fis.read(buf)) != -1) {
                    md.update(buf, 0, n);
                }
            }
            byte[] digest = md.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString().equalsIgnoreCase(expectedMd5);
        } catch (Exception e) {
            Log.e(TAG, "MD5 error", e);
            return false;
        }
    }

    private void notifyProgress(SyncCallback callback, int percent, String message) {
        if (callback != null) {
            callback.onProgress(percent, message);
        }
    }

    // ────────────────────────────────────────────────
    //  回调接口
    // ────────────────────────────────────────────────

    /**
     * 同步回调接口
     */
    public interface SyncCallback {
        /**
         * 同步成功
         * @param playlistJson 可直接注入 WebView 播放器的播放列表 JSON
         * @param schedule     设备定时开关机配置（可为 null）
         */
        void onSyncSuccess(String playlistJson, InitResponse.Schedule schedule);

        /**
         * 同步失败（网络不可用、服务器错误、未分配播放列表等）
         * @param error 错误描述或错误码："no_playlist" / "server_error:xxx" / 异常消息
         */
        void onSyncFailed(String error);

        /**
         * 进度回调（在后台线程调用，需 runOnUiThread 更新 UI）
         * @param percent 0–100
         * @param message 进度描述
         */
        void onProgress(int percent, String message);
    }
}
