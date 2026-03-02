package com.castplay.player.service;

import android.content.Context;
import android.util.Log;
import com.castplay.player.data.db.AppDatabase;
import com.castplay.player.data.db.entity.MediaFileEntity;
import com.castplay.player.data.db.entity.PlaylistEntity;
import com.castplay.player.data.model.InitResponse;
import com.castplay.player.network.ApiService;
import com.castplay.player.network.RetrofitClient;
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
 * 同步管理器 - 负责从服务器同步播放列表和下载媒体文件
 */
public class SyncManager {
    private static final String TAG = "SyncManager";

    private Context context;
    private AppDatabase database;
    private ApiService apiService;
    private String deviceId;
    private ExecutorService executor;

    public SyncManager(Context context, String deviceId) {
        this.context = context;
        this.deviceId = deviceId;
        this.database = AppDatabase.getInstance(context);
        this.apiService = RetrofitClient.getInstance().getApiService();
        this.executor = Executors.newSingleThreadExecutor();
    }

    /**
     * 执行完整同步
     */
    public void performFullSync(SyncCallback callback) {
        Log.d(TAG, "Starting full sync for device: " + deviceId);

        // 调用初始化接口获取配置
        Call<InitResponse> call = apiService.playerInit(
                new ApiService.InitRequest(deviceId));

        call.enqueue(new Callback<InitResponse>() {
            @Override
            public void onResponse(Call<InitResponse> call, Response<InitResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    InitResponse initResponse = response.body();

                    // 使用 Executor 处理同步逻辑
                    executor.execute(() -> {
                        try {
                            // 1. 更新播放列表
                            updatePlaylists(initResponse.getPlaylists());

                            // 2. 下载媒体文件
                            downloadMediaFiles(initResponse.getPlaylists());

                            Log.d(TAG, "Sync completed successfully");
                            if (callback != null) {
                                callback.onSyncSuccess(initResponse.getSchedule());
                            }
                        } catch (Exception e) {
                            Log.e(TAG, "Sync failed", e);
                            if (callback != null) {
                                callback.onSyncFailed("Sync failed: " + e.getMessage());
                            }
                        }
                    });

                } else {
                    Log.e(TAG, "Init request failed: " + response.code());
                    if (callback != null) {
                        callback.onSyncFailed("Server error: " + response.code());
                    }
                }
            }

            @Override
            public void onFailure(Call<InitResponse> call, Throwable t) {
                Log.e(TAG, "Init request failed", t);
                if (callback != null) {
                    callback.onSyncFailed(t.getMessage());
                }
            }
        });
    }

    /**
     * 更新播放列表到数据库
     */
    private void updatePlaylists(List<InitResponse.PlaylistData> playlists) {
        List<Integer> activePlaylistIds = new ArrayList<>();

        for (InitResponse.PlaylistData playlistData : playlists) {
            // 保存播放列表
            PlaylistEntity playlist = new PlaylistEntity();
            playlist.setId(playlistData.getId());
            playlist.setName(playlistData.getName());
            playlist.setVersion(playlistData.getVersion());
            playlist.setLastUpdated(System.currentTimeMillis());
            database.playlistDao().insert(playlist);

            activePlaylistIds.add(playlistData.getId());

            // 保存媒体文件信息
            for (InitResponse.PlaylistItemData item : playlistData.getItems()) {
                MediaFileEntity mediaFile = new MediaFileEntity();
                mediaFile.setId(item.getMediaId());
                mediaFile.setPlaylistId(playlistData.getId());
                mediaFile.setFileName(item.getFileName());
                mediaFile.setFileType(item.getFileType());
                mediaFile.setFileUrl(item.getFileUrl());
                mediaFile.setDisplayOrder(item.getDisplayOrder());
                mediaFile.setDisplayDuration(item.getDisplayDuration());
                mediaFile.setFileSize(item.getFileSize());
                mediaFile.setMd5Hash(item.getMd5Hash());
                mediaFile.setDownloaded(false);

                database.mediaFileDao().insert(mediaFile);
            }
        }

        // 删除不活跃的播放列表
        if (!activePlaylistIds.isEmpty()) {
            database.mediaFileDao().deleteInactivePlaylists(activePlaylistIds);
        }

        Log.d(TAG, "Playlists updated: " + playlists.size());
    }

    /**
     * 下载媒体文件
     */
    private void downloadMediaFiles(List<InitResponse.PlaylistData> playlists) {
        File mediaDir = new File(context.getFilesDir(), "media");
        if (!mediaDir.exists()) {
            mediaDir.mkdirs();
        }

        for (InitResponse.PlaylistData playlistData : playlists) {
            for (InitResponse.PlaylistItemData item : playlistData.getItems()) {
                MediaFileEntity mediaFile = database.mediaFileDao()
                        .getByPlaylistId(playlistData.getId())
                        .stream()
                        .filter(m -> m.getId() == item.getMediaId())
                        .findFirst()
                        .orElse(null);

                if (mediaFile == null || mediaFile.isDownloaded()) {
                    continue;
                }

                // 检查文件是否已存在且MD5匹配
                File localFile = new File(mediaDir, item.getMediaId() + "_" + item.getFileName());
                if (localFile.exists() && verifyMD5(localFile, item.getMd5Hash())) {
                    // 文件已存在且有效，更新数据库
                    mediaFile.setFilePath(localFile.getAbsolutePath());
                    mediaFile.setDownloaded(true);
                    database.mediaFileDao().update(mediaFile);
                    Log.d(TAG, "File already exists: " + item.getFileName());
                    continue;
                }

                // 下载文件
                try {
                    downloadFile(item.getMediaId(), localFile);

                    // 验证下载的文件
                    if (verifyMD5(localFile, item.getMd5Hash())) {
                        mediaFile.setFilePath(localFile.getAbsolutePath());
                        mediaFile.setDownloaded(true);
                        database.mediaFileDao().update(mediaFile);
                        Log.d(TAG, "Downloaded: " + item.getFileName());
                    } else {
                        Log.e(TAG, "MD5 verification failed: " + item.getFileName());
                        localFile.delete();
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Download failed: " + item.getFileName(), e);
                }
            }
        }
    }

    /**
     * 下载单个文件
     */
    private void downloadFile(int mediaId, File outputFile) throws IOException {
        Call<ResponseBody> call = apiService.downloadMedia(mediaId);
        Response<ResponseBody> response = call.execute();

        if (response.isSuccessful() && response.body() != null) {
            try (InputStream inputStream = response.body().byteStream();
                    FileOutputStream outputStream = new FileOutputStream(outputFile)) {

                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = inputStream.read(buffer)) != -1) {
                    outputStream.write(buffer, 0, bytesRead);
                }
            }
        } else {
            throw new IOException("Download failed: " + response.code());
        }
    }

    /**
     * 验证文件MD5
     */
    private boolean verifyMD5(File file, String expectedMd5) {
        if (expectedMd5 == null || expectedMd5.isEmpty()) {
            return true;
        }

        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            try (FileInputStream fis = new FileInputStream(file)) {
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = fis.read(buffer)) != -1) {
                    md.update(buffer, 0, bytesRead);
                }
            }

            byte[] digest = md.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }

            return sb.toString().equalsIgnoreCase(expectedMd5);
        } catch (Exception e) {
            Log.e(TAG, "MD5 verification error", e);
            return false;
        }
    }

    /**
     * 同步回调接口
     */
    public interface SyncCallback {
        void onSyncSuccess(InitResponse.Schedule schedule);

        void onSyncFailed(String error);
    }
}
