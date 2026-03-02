package com.castplay.player;

import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.castplay.player.data.db.AppDatabase;
import com.castplay.player.data.db.entity.MediaFileEntity;
import com.castplay.player.data.model.MediaItem;
import com.castplay.player.network.WebSocketManager;
import com.castplay.player.player.PlaybackEngine;
import com.castplay.player.service.ScheduleManager;
import com.castplay.player.service.SyncManager;
import com.google.android.exoplayer2.ui.StyledPlayerView;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 主活动 - 播放界面
 */
public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private static final String PREFS_NAME = "CastPlayPrefs";
    private static final String KEY_DEVICE_ID = "device_id";
    private static final boolean DEBUG_MODE = BuildConfig.DEBUG;

    // UI组件
    private ImageView imageView;
    private StyledPlayerView playerView;
    private LinearLayout loadingContainer;
    private ProgressBar progressBar;
    private TextView statusText;
    private TextView deviceIdText;

    // 管理器
    private PlaybackEngine playbackEngine;
    private SyncManager syncManager;
    private ScheduleManager scheduleManager;
    private WebSocketManager webSocketManager;
    private AppDatabase database;

    private String deviceId;
    private Handler heartbeatHandler;
    private Runnable heartbeatRunnable;
    private boolean isSyncing = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 隐藏系统UI
        hideSystemUI();

        // 初始化视图
        initViews();

        // 获取或生成设备ID
        deviceId = getOrCreateDeviceId();
        
        // 显示设备ID（调试模式）
        if (DEBUG_MODE) {
            deviceIdText.setText("ID: " + deviceId.substring(0, 8));
            deviceIdText.setVisibility(View.VISIBLE);
        }

        // 初始化数据库
        database = AppDatabase.getInstance(this);

        // 初始化播放引擎
        initPlaybackEngine();

        // 初始化同步管理器
        syncManager = new SyncManager(this, deviceId);

        // 初始化定时管理器
        scheduleManager = new ScheduleManager(this);

        // 显示加载状态
        showLoading("正在初始化...");

        // 初始化WebSocket
        initWebSocket();

        // 执行初始同步
        performInitialSync();

        // 启动心跳
        startHeartbeat();
    }

    /**
     * 初始化视图
     */
    private void initViews() {
        imageView = findViewById(R.id.imageView);
        playerView = findViewById(R.id.playerView);
        loadingContainer = findViewById(R.id.loadingContainer);
        progressBar = findViewById(R.id.progressBar);
        statusText = findViewById(R.id.statusText);
        deviceIdText = findViewById(R.id.deviceIdText);
    }

    /**
     * 初始化播放引擎
     */
    private void initPlaybackEngine() {
        playbackEngine = new PlaybackEngine(this, imageView, playerView);
        playbackEngine.setProgressViews(progressBar, statusText);
        playbackEngine.setCallback(new PlaybackEngine.PlaybackCallback() {
            @Override
            public void onPlaybackStarted(int index, MediaItem item) {
                Log.d(TAG, "Now playing: " + item.getFileName());
                hideLoading();
            }

            @Override
            public void onPlaybackCompleted() {
                Log.d(TAG, "Playback completed");
            }

            @Override
            public void onPlaybackError(String error) {
                Log.e(TAG, "Playback error: " + error);
            }
        });
    }

    /**
     * 隐藏系统UI（全屏模式）
     */
    private void hideSystemUI() {
        View decorView = getWindow().getDecorView();
        decorView.setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN);
    }

    /**
     * 获取或创建设备ID
     */
    private String getOrCreateDeviceId() {
        android.content.SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String id = prefs.getString(KEY_DEVICE_ID, null);

        if (id == null) {
            id = UUID.randomUUID().toString();
            prefs.edit().putString(KEY_DEVICE_ID, id).apply();
            Log.d(TAG, "Created new device ID: " + id);
        } else {
            Log.d(TAG, "Using existing device ID: " + id);
        }

        return id;
    }

    /**
     * 初始化WebSocket
     */
    private void initWebSocket() {
        webSocketManager = WebSocketManager.getInstance();
        webSocketManager.connect(deviceId, new WebSocketManager.WebSocketListener() {
            @Override
            public void onRegistered() {
                Log.d(TAG, "WebSocket registered");
                runOnUiThread(() -> {
                    if (statusText != null) {
                        statusText.setText("已连接服务器");
                    }
                });
            }

            @Override
            public void onPlaylistUpdate(int playlistId) {
                Log.d(TAG, "Playlist update received: " + playlistId);
                // 重新同步
                performInitialSync();
            }

            @Override
            public void onScheduleUpdate() {
                Log.d(TAG, "Schedule update received");
                // 重新同步
                performInitialSync();
            }

            @Override
            public void onForceSync() {
                Log.d(TAG, "Force sync received");
                performInitialSync();
            }

            @Override
            public void onReboot() {
                Log.d(TAG, "Reboot command received");
                // 重启应用
                restartApp();
            }
        });
    }

    /**
     * 执行初始同步
     */
    private void performInitialSync() {
        if (isSyncing) {
            Log.d(TAG, "Already syncing, skip");
            return;
        }
        
        isSyncing = true;
        runOnUiThread(() -> showLoading("正在同步数据..."));
        
        syncManager.performFullSync(new SyncManager.SyncCallback() {
            @Override
            public void onSyncSuccess(com.castplay.player.data.model.InitResponse.Schedule schedule) {
                isSyncing = false;
                runOnUiThread(() -> {
                    Log.d(TAG, "Sync success, loading playlist");

                    // 设置定时任务
                    if (schedule != null && scheduleManager != null) {
                        scheduleManager.setSchedule(schedule);
                        Log.d(TAG, "Schedule set: " + schedule.getPowerOnTime() + " - " + schedule.getPowerOffTime());
                    }

                    loadAndPlayPlaylist();
                });
            }

            @Override
            public void onSyncFailed(String error) {
                isSyncing = false;
                Log.e(TAG, "Sync failed: " + error);
                // 尝试播放本地缓存
                runOnUiThread(() -> {
                    showLoading("同步失败，使用本地缓存...");
                    loadAndPlayPlaylist();
                });
            }
        });
    }

    /**
     * 加载并播放播放列表
     */
    private void loadAndPlayPlaylist() {
        new Thread(() -> {
            try {
                // 获取所有播放列表，找到第一个有媒体文件的
                List<Integer> allPlaylistIds = database.mediaFileDao().getAllPlaylistIds();

                if (allPlaylistIds.isEmpty()) {
                    Log.w(TAG, "No playlists found");
                    runOnUiThread(() -> showLoading("暂无播放内容"));
                    return;
                }

                // 遍历所有播放列表，找到第一个有下载完成的媒体文件的播放列表
                List<MediaItem> playlist = new ArrayList<>();
                for (Integer playlistId : allPlaylistIds) {
                    List<MediaFileEntity> mediaFiles = database.mediaFileDao()
                            .getByPlaylistId(playlistId);

                    for (MediaFileEntity entity : mediaFiles) {
                        if (entity.isDownloaded() && entity.getFilePath() != null) {
                            playlist.add(new MediaItem(
                                    entity.getId(),
                                    entity.getFileName(),
                                    entity.getFileType(),
                                    entity.getFilePath(),
                                    entity.getDisplayDuration()));
                        }
                    }

                    if (!playlist.isEmpty()) {
                        Log.d(TAG, "Found playlist with media: " + playlistId);
                        break;
                    }
                }

                if (playlist.isEmpty()) {
                    Log.w(TAG, "No downloaded media files");
                    runOnUiThread(() -> showLoading("暂无可播放的媒体文件"));
                    return;
                }

                // 设置播放列表并开始播放
                final List<MediaItem> finalPlaylist = playlist;
                runOnUiThread(() -> {
                    hideLoading();
                    playbackEngine.setPlaylist(finalPlaylist);
                    playbackEngine.play();
                    Log.d(TAG, "Playback started with " + finalPlaylist.size() + " items");
                });
            } catch (Exception e) {
                Log.e(TAG, "Error loading playlist", e);
                runOnUiThread(() -> showLoading("加载播放列表失败"));
            }
        }).start();
    }

    /**
     * 显示加载状态
     */
    private void showLoading(String message) {
        if (loadingContainer != null) {
            loadingContainer.setVisibility(View.VISIBLE);
        }
        if (statusText != null) {
            statusText.setText(message);
        }
    }

    /**
     * 隐藏加载状态
     */
    private void hideLoading() {
        if (loadingContainer != null) {
            loadingContainer.setVisibility(View.GONE);
        }
    }

    /**
     * 启动心跳
     */
    private void startHeartbeat() {
        heartbeatHandler = new Handler();
        heartbeatRunnable = new Runnable() {
            @Override
            public void run() {
                if (webSocketManager != null) {
                    webSocketManager.sendHeartbeat();
                }
                heartbeatHandler.postDelayed(this, 60000); // 每分钟一次
            }
        };
        heartbeatHandler.post(heartbeatRunnable);
    }

    /**
     * 重启应用
     */
    private void restartApp() {
        android.content.Intent intent = getPackageManager()
                .getLaunchIntentForPackage(getPackageName());
        if (intent != null) {
            intent.addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
            finish();
            System.exit(0);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemUI();
        if (playbackEngine != null) {
            playbackEngine.resume();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (playbackEngine != null) {
            playbackEngine.pause();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        if (playbackEngine != null) {
            playbackEngine.release();
        }

        if (webSocketManager != null) {
            webSocketManager.disconnect();
        }

        if (heartbeatHandler != null && heartbeatRunnable != null) {
            heartbeatHandler.removeCallbacks(heartbeatRunnable);
        }
    }
}
