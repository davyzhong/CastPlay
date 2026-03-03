package com.castplay.player;

import android.annotation.SuppressLint;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.webkit.WebViewAssetLoader;

import com.castplay.player.data.model.InitResponse;
import com.castplay.player.network.WebSocketManager;
import com.castplay.player.service.DefaultPlaylistManager;
import com.castplay.player.service.ScheduleManager;
import com.castplay.player.service.SyncManager;

import java.io.File;
import java.util.UUID;

/**
 * 主活动 - WebView 全屏播放器
 *
 * 启动流程：
 *  1. 显示加载覆盖层，初始化 WebView
 *  2. 获取 / 创建设备 ID
 *  3. 联网调用 /api/player/init，同步播放列表并下载媒体文件
 *     → 成功：将服务器播放列表 JSON 注入 WebView，开始播放
 *     → 失败：使用 DefaultPlaylistManager 中缓存的列表（或内置默认列表），开始播放
 *  4. WebView 加载 assets/player_local.html，播放器自动循环
 *  5. WebSocket 监听服务器推送，收到更新时重新同步
 */
public class MainActivity extends AppCompatActivity {

    private static final String TAG = "MainActivity";
    private static final String PREFS_NAME   = "CastPlayPrefs";
    private static final String KEY_DEVICE_ID = "device_id";

    // ─── UI ──────────────────────────────────────────
    private WebView          webView;
    private LinearLayout     loadingContainer;
    private ProgressBar      progressBar;
    private TextView         statusText;
    private TextView         deviceIdText;

    // ─── 管理器 ───────────────────────────────────────
    private SyncManager             syncManager;
    private DefaultPlaylistManager  defaultPlaylistManager;
    private ScheduleManager         scheduleManager;
    private WebSocketManager        webSocketManager;

    // ─── 状态 ─────────────────────────────────────────
    private String  deviceId;
    private boolean isSyncing     = false;
    private boolean webViewReady  = false;  // player_local.html 已加载完毕

    /** 记录同步结果（在页面加载完成前到达时暂存）*/
    private String pendingPlaylistJson = null;

    private final Handler uiHandler = new Handler(Looper.getMainLooper());
    private Handler  heartbeatHandler;
    private Runnable heartbeatRunnable;

    // ─────────────────────────────────────────────────
    //  生命周期
    // ─────────────────────────────────────────────────

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        hideSystemUI();
        initViews();

        deviceId = getOrCreateDeviceId();

        // 调试模式显示设备 ID
        if (BuildConfig.DEBUG) {
            deviceIdText.setText("ID: " + deviceId.substring(0, 8));
            deviceIdText.setVisibility(View.VISIBLE);
        }

        defaultPlaylistManager = new DefaultPlaylistManager(this);
        syncManager            = new SyncManager(this, deviceId);
        scheduleManager        = new ScheduleManager(this);

        showLoading("正在初始化...", 0);

        initWebView();
        initWebSocket();
        performSync();
        startHeartbeat();
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemUI();
        if (webView != null) webView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) webView.onPause();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
        }
        if (webSocketManager != null) webSocketManager.disconnect();
        if (heartbeatHandler != null && heartbeatRunnable != null) {
            heartbeatHandler.removeCallbacks(heartbeatRunnable);
        }
    }

    // ─────────────────────────────────────────────────
    //  视图初始化
    // ─────────────────────────────────────────────────

    private void initViews() {
        webView          = findViewById(R.id.webView);
        loadingContainer = findViewById(R.id.loadingContainer);
        progressBar      = findViewById(R.id.progressBar);
        statusText       = findViewById(R.id.statusText);
        deviceIdText     = findViewById(R.id.deviceIdText);
    }

    // ─────────────────────────────────────────────────
    //  WebView 初始化
    // ─────────────────────────────────────────────────

    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    private void initWebView() {
        // 使用 WebViewAssetLoader 同时服务 assets/ 和 filesDir/
        WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .setDomain("appassets.androidplatform.net")
                .addPathHandler("/assets/",
                        new WebViewAssetLoader.AssetsPathHandler(this))
                .addPathHandler("/files/",
                        new WebViewAssetLoader.InternalStoragePathHandler(
                                this, getFilesDir()))
                .build();

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);  // 允许自动播放视频
        settings.setDomStorageEnabled(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        // 允许 file:// 访问 assets（加载本地 HTML 用）
        settings.setAllowFileAccess(true);

        // 注入 Android JS 接口
        webView.addJavascriptInterface(new CastPlayBridge(), "Android");

        // WebViewClient：拦截本地资源请求
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                WebResourceResponse resp = assetLoader.shouldInterceptRequest(
                        request.getUrl());
                return resp != null ? resp
                        : super.shouldInterceptRequest(view, request);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                Log.d(TAG, "WebView page finished: " + url);
                webViewReady = true;

                // 若同步结果已到达，立即注入
                if (pendingPlaylistJson != null) {
                    injectPlaylistAndHideLoading(pendingPlaylistJson);
                    pendingPlaylistJson = null;
                } else if (defaultPlaylistManager.hasServerPlaylist()) {
                    // 使用已缓存的服务器播放列表（非首次启动场景）
                    hideLoading();
                }
                // 否则等待 syncCallback 触发注入，loading 继续显示
            }
        });

        // WebChromeClient：允许视频全屏（部分 Android 版本需要）
        webView.setWebChromeClient(new WebChromeClient());

        // 加载本地播放器 HTML
        webView.loadUrl("file:///android_asset/player_local.html");
    }

    // ─────────────────────────────────────────────────
    //  Android → WebView JS 桥接接口
    // ─────────────────────────────────────────────────

    /**
     * 由 player_local.html 中 window.Android.xxx() 调用。
     * 所有方法运行在 WebView JS 线程（非 UI 线程）。
     */
    private class CastPlayBridge {

        /** 返回当前激活的播放列表 JSON */
        @JavascriptInterface
        public String getPlaylistJson() {
            return defaultPlaylistManager.getActivePlaylistJson();
        }

        /** 返回设备 ID */
        @JavascriptInterface
        public String getDeviceId() {
            return deviceId;
        }

        /** 返回服务器 API 地址（供 HTML 直接拼 URL 时使用） */
        @JavascriptInterface
        public String getServerBaseUrl() {
            return BuildConfig.API_BASE_URL;
        }

        /** 是否调试构建 */
        @JavascriptInterface
        public boolean isDebugMode() {
            return BuildConfig.DEBUG;
        }
    }

    // ─────────────────────────────────────────────────
    //  同步流程
    // ─────────────────────────────────────────────────

    private void performSync() {
        if (isSyncing) {
            Log.d(TAG, "Already syncing, skip");
            return;
        }
        isSyncing = true;
        showLoading("正在连接服务器...", 5);

        syncManager.performFullSync(new SyncManager.SyncCallback() {

            @Override
            public void onSyncSuccess(String playlistJson,
                                      InitResponse.Schedule schedule) {
                isSyncing = false;

                // 保存服务器列表
                defaultPlaylistManager.saveServerPlaylist(playlistJson);
                defaultPlaylistManager.markFirstLaunchDone();

                // 设置定时任务
                if (schedule != null && scheduleManager != null) {
                    scheduleManager.setSchedule(schedule);
                }

                // 注入 WebView
                uiHandler.post(() -> {
                    if (webViewReady) {
                        injectPlaylistAndHideLoading(playlistJson);
                    } else {
                        // WebView 还未加载完毕，暂存等待
                        pendingPlaylistJson = playlistJson;
                        showLoading("正在准备播放器...", 98);
                    }
                });
            }

            @Override
            public void onSyncFailed(String error) {
                isSyncing = false;
                Log.w(TAG, "Sync failed: " + error);

                uiHandler.post(() -> {
                    if ("no_playlist".equals(error)) {
                        // 服务器未分配播放列表，使用默认列表
                        showLoading("未分配播放列表，使用默认内容", 100);
                    } else {
                        // 网络错误等，尝试使用已缓存列表
                        showLoading("同步失败，使用本地缓存...", 80);
                    }
                    // 延迟 1.5 秒后进入播放（让用户看到提示）
                    uiHandler.postDelayed(() -> {
                        if (webViewReady) {
                            // 使用 DefaultPlaylistManager 中当前激活的列表
                            String json = defaultPlaylistManager.getActivePlaylistJson();
                            injectPlaylistAndHideLoading(json);
                        }
                        // 否则 onPageFinished 中会处理
                    }, 1500);
                });
            }

            @Override
            public void onProgress(int percent, String message) {
                uiHandler.post(() -> showLoading(message, percent));
            }
        });
    }

    // ─────────────────────────────────────────────────
    //  WebView 播放列表注入
    // ─────────────────────────────────────────────────

    /**
     * 将播放列表 JSON 注入 WebView 并隐藏加载覆盖层。
     * 调用 player_local.html 中暴露的 window.loadPlaylistJson(json)。
     */
    private void injectPlaylistAndHideLoading(String playlistJson) {
        if (playlistJson == null || playlistJson.isEmpty()) {
            hideLoading();
            return;
        }
        // 转义 JSON 用于 JS 字符串（防止单引号/换行破坏语法）
        String escaped = playlistJson
                .replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace("\n", "\\n")
                .replace("\r", "");

        String js = "window.loadPlaylistJson('" + escaped + "');";
        webView.evaluateJavascript(js, null);
        hideLoading();
        Log.d(TAG, "Playlist injected into WebView");
    }

    // ─────────────────────────────────────────────────
    //  WebSocket
    // ─────────────────────────────────────────────────

    private void initWebSocket() {
        webSocketManager = WebSocketManager.getInstance();
        webSocketManager.connect(deviceId, new WebSocketManager.WebSocketListener() {
            @Override
            public void onRegistered() {
                Log.d(TAG, "WebSocket registered");
            }

            @Override
            public void onPlaylistUpdate(int playlistId) {
                Log.d(TAG, "Playlist update: " + playlistId);
                uiHandler.post(() -> {
                    showLoading("收到更新，重新同步...", 0);
                    performSync();
                });
            }

            @Override
            public void onScheduleUpdate() {
                Log.d(TAG, "Schedule update");
                uiHandler.post(() -> performSync());
            }

            @Override
            public void onForceSync() {
                Log.d(TAG, "Force sync");
                uiHandler.post(() -> performSync());
            }

            @Override
            public void onReboot() {
                Log.d(TAG, "Reboot command");
                uiHandler.post(() -> restartApp());
            }
        });
    }

    // ─────────────────────────────────────────────────
    //  辅助方法
    // ─────────────────────────────────────────────────

    private String getOrCreateDeviceId() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String id = prefs.getString(KEY_DEVICE_ID, null);
        if (id == null) {
            id = UUID.randomUUID().toString();
            prefs.edit().putString(KEY_DEVICE_ID, id).apply();
            Log.d(TAG, "Created device ID: " + id);
        } else {
            Log.d(TAG, "Existing device ID: " + id);
        }
        return id;
    }

    private void hideSystemUI() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN);
    }

    private void showLoading(String message, int progress) {
        if (loadingContainer != null)
            loadingContainer.setVisibility(View.VISIBLE);
        if (statusText != null)
            statusText.setText(message);
        if (progressBar != null && progress >= 0) {
            progressBar.setProgress(progress);
        }
    }

    private void hideLoading() {
        if (loadingContainer != null)
            loadingContainer.setVisibility(View.GONE);
    }

    private void startHeartbeat() {
        heartbeatHandler = new Handler(Looper.getMainLooper());
        heartbeatRunnable = () -> {
            if (webSocketManager != null) webSocketManager.sendHeartbeat();
            heartbeatHandler.postDelayed(heartbeatRunnable, 60_000);
        };
        heartbeatHandler.postDelayed(heartbeatRunnable, 60_000);
    }

    private void restartApp() {
        android.content.Intent intent =
                getPackageManager().getLaunchIntentForPackage(getPackageName());
        if (intent != null) {
            intent.addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
            finish();
            System.exit(0);
        }
    }
}
