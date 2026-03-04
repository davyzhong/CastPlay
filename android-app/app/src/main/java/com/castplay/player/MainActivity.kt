package com.castplay.player

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.webkit.WebViewAssetLoader
import com.castplay.player.data.model.InitResponse
import com.castplay.player.network.WebSocketManager
import com.castplay.player.service.DefaultPlaylistManager
import com.castplay.player.service.DeviceRegistrationManager
import com.castplay.player.service.ScheduleManager
import com.castplay.player.service.SyncManager
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 主活动 - WebView 全屏播放器
 *
 * 启动流程：
 *  1. 显示加载覆盖层，初始化 WebView
 *  2. 向服务器注册设备，获取/恢复唯一设备 ID
 *  3. 显示设备 ID（启动时显示，播放时自动隐藏）
 *  4. 联网调用 /api/player/init，同步播放列表并下载媒体文件
 *     → 成功：将服务器播放列表 JSON 注入 WebView，开始播放
 *     → 失败：使用 DefaultPlaylistManager 中缓存的列表（或内置默认列表），开始播放
 *  5. WebView 加载 assets/player_local.html，播放器自动循环
 *  6. WebSocket 监听服务器推送，收到更新时重新同步
 */
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"

        /** 设备 ID 显示时间（毫秒） */
        private const val DEVICE_ID_DISPLAY_DURATION = 10_000L
    }

    // ─── UI ──────────────────────────────────────────
    private lateinit var webView: WebView
    private var loadingContainer: LinearLayout? = null
    private var progressBar: ProgressBar? = null
    private var statusText: TextView? = null
    private var deviceIdText: TextView? = null

    // ─── 管理器 ───────────────────────────────────────
    @Inject lateinit var registrationManager: DeviceRegistrationManager
    @Inject lateinit var defaultPlaylistManager: DefaultPlaylistManager
    @Inject lateinit var scheduleManager: ScheduleManager
    @Inject lateinit var syncManagerFactory: SyncManager.Factory
    private var syncManager: SyncManager? = null

    // ─── 状态 ─────────────────────────────────────────
    private var deviceId: String? = null
    private var isSyncing = false
    private var webViewReady = false  // player_local.html 已加载完毕
    private var isPlaying = false  // 是否正在播放

    /** 记录同步结果（在页面加载完成前到达时暂存）*/
    private var pendingPlaylistJson: String? = null

    private val uiHandler = Handler(Looper.getMainLooper())
    private var heartbeatHandler: Handler? = null
    private var heartbeatRunnable: Runnable? = null

    // ─────────────────────────────────────────────────
    //  生命周期
    // ─────────────────────────────────────────────────

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        hideSystemUI()
        initViews()

        showLoading("正在初始化...", 0)

        // 监听 WebSocket 事件（协程方式）
        observeWebSocketEvents()

        // 步骤 1: 注册设备
        performDeviceRegistration()
    }

    override fun onResume() {
        super.onResume()
        hideSystemUI()
        if (::webView.isInitialized) webView.onResume()
    }

    override fun onPause() {
        super.onPause()
        if (::webView.isInitialized) webView.onPause()
    }

    override fun onDestroy() {
        super.onDestroy()
        if (::webView.isInitialized) {
            webView.stopLoading()
            webView.destroy()
        }
        WebSocketManager.disconnect()
        heartbeatHandler?.let { handler ->
            heartbeatRunnable?.let { handler.removeCallbacks(it) }
        }
    }

    // ─────────────────────────────────────────────────
    //  视图初始化
    // ─────────────────────────────────────────────────

    private fun initViews() {
        webView = findViewById(R.id.webView)
        loadingContainer = findViewById(R.id.loadingContainer)
        progressBar = findViewById(R.id.progressBar)
        statusText = findViewById(R.id.statusText)
        deviceIdText = findViewById(R.id.deviceIdText)

        // 点击屏幕显示设备 ID
        webView.setOnClickListener { showDeviceIdTemporarily() }
    }

    // ─────────────────────────────────────────────────
    //  设备注册
    // ─────────────────────────────────────────────────

    /**
     * 执行设备注册
     */
    private fun performDeviceRegistration() {
        showLoading("正在注册设备...", 5)

        registrationManager.register(object : DeviceRegistrationManager.RegistrationCallback {
            override fun onRegistrationSuccess(registeredDeviceId: String, isNew: Boolean) {
                deviceId = registeredDeviceId
                Log.d(TAG, "Device registered: $deviceId (new=$isNew)")

                uiHandler.post {
                    // 显示设备 ID
                    updateDeviceIdDisplay()
                    showDeviceIdTemporarily()

                    // 初始化同步管理器（通过 Factory 创建）
                    syncManager = syncManagerFactory.create(deviceId!!)

                    // 继续启动流程
                    initWebView()
                    initWebSocket()
                    performSync()
                    startHeartbeat()
                }
            }

            override fun onRegistrationFailed(error: String) {
                Log.e(TAG, "Device registration failed: $error")

                uiHandler.post {
                    // 注册失败，使用缓存的 ID 或生成临时 ID
                    deviceId = registrationManager.getCachedDeviceId()
                    if (deviceId == null) {
                        // 首次启动且网络不可用，生成临时 ID
                        deviceId = "OFFLINE-${java.util.UUID.randomUUID().toString().substring(0, 8).uppercase()}"
                        Log.w(TAG, "Using temporary offline ID: $deviceId")
                    }

                    updateDeviceIdDisplay()
                    showDeviceIdTemporarily()

                    // 继续启动流程
                    syncManager = syncManagerFactory.create(deviceId!!)
                    initWebView()
                    initWebSocket()
                    performSync()
                    startHeartbeat()
                }
            }
        })
    }

    /**
     * 更新设备 ID 显示文本
     */
    private fun updateDeviceIdDisplay() {
        deviceIdText?.text = "设备 ID: $deviceId"
    }

    /**
     * 临时显示设备 ID（显示后自动隐藏）
     */
    private fun showDeviceIdTemporarily() {
        deviceIdText?.visibility = View.VISIBLE

        // 如果正在播放，延迟后隐藏
        uiHandler.removeCallbacksAndMessages("hideDeviceId")
        if (isPlaying) {
            uiHandler.postDelayed({
                if (isPlaying) {
                    deviceIdText?.visibility = View.GONE
                }
            }, DEVICE_ID_DISPLAY_DURATION)
        }
    }

    /**
     * 隐藏设备 ID（播放开始时调用）
     */
    private fun hideDeviceId() {
        deviceIdText?.visibility = View.GONE
    }

    // ─────────────────────────────────────────────────
    //  WebView 初始化
    // ─────────────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    private fun initWebView() {
        // 使用 WebViewAssetLoader 同时服务 assets/ 和 filesDir/
        val assetLoader = WebViewAssetLoader.Builder()
            .setDomain("appassets.androidplatform.net")
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .addPathHandler("/files/", WebViewAssetLoader.InternalStoragePathHandler(this, filesDir))
            .build()

        webView.settings.apply {
            javaScriptEnabled = true
            mediaPlaybackRequiresUserGesture = false  // 允许自动播放视频
            domStorageEnabled = true
            cacheMode = WebSettings.LOAD_DEFAULT
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = false
            displayZoomControls = false
            // 允许 file:// 访问 assets（加载本地 HTML 用）
            allowFileAccess = true
        }

        // 注入 Android JS 接口
        webView.addJavascriptInterface(CastPlayBridge(), "Android")

        // WebViewClient：拦截本地资源请求
        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                return assetLoader.shouldInterceptRequest(request.url)
                    ?: super.shouldInterceptRequest(view, request)
            }

            override fun onPageFinished(view: WebView, url: String?) {
                super.onPageFinished(view, url)
                Log.d(TAG, "WebView page finished: $url")
                webViewReady = true

                // 若同步结果已到达，立即注入
                pendingPlaylistJson?.let { json ->
                    injectPlaylistAndHideLoading(json)
                    pendingPlaylistJson = null
                } ?: run {
                    if (defaultPlaylistManager.hasServerPlaylist()) {
                        // 使用已缓存的服务器播放列表（非首次启动场景）
                        hideLoading()
                    }
                }
                // 否则等待 syncCallback 触发注入，loading 继续显示
            }
        }

        // WebChromeClient：允许视频全屏（部分 Android 版本需要）
        webView.webChromeClient = WebChromeClient()

        // 加载本地播放器 HTML
        webView.loadUrl("file:///android_asset/player_local.html")
    }

    // ─────────────────────────────────────────────────
    //  Android → WebView JS 桥接接口
    // ─────────────────────────────────────────────────

    /**
     * 由 player_local.html 中 window.Android.xxx() 调用。
     * 所有方法运行在 WebView JS 线程（非 UI 线程）。
     */
    inner class CastPlayBridge {

        /** 返回当前激活的播放列表 JSON */
        @JavascriptInterface
        fun getPlaylistJson(): String = defaultPlaylistManager.getActivePlaylistJson()

        /** 返回设备 ID */
        @JavascriptInterface
        fun getDeviceId(): String? = deviceId

        /** 返回服务器 API 地址（供 HTML 直接拼 URL 时使用） */
        @JavascriptInterface
        fun getServerBaseUrl(): String = BuildConfig.API_BASE_URL

        /** 是否调试构建 */
        @JavascriptInterface
        fun isDebugMode(): Boolean = BuildConfig.DEBUG
    }

    // ─────────────────────────────────────────────────
    //  同步流程
    // ─────────────────────────────────────────────────

    private fun performSync() {
        if (isSyncing) {
            Log.d(TAG, "Already syncing, skip")
            return
        }
        isSyncing = true
        showLoading("正在连接服务器...", 5)

        syncManager?.performFullSync(object : SyncManager.SyncCallback {
            override fun onSyncSuccess(playlistJson: String, schedule: InitResponse.Schedule?) {
                isSyncing = false

                // 保存服务器列表
                defaultPlaylistManager.saveServerPlaylist(playlistJson)
                defaultPlaylistManager.markFirstLaunchDone()

                // 设置定时任务
                schedule?.let { scheduleManager.setSchedule(it) }

                // 注入 WebView
                uiHandler.post {
                    if (webViewReady) {
                        injectPlaylistAndHideLoading(playlistJson)
                    } else {
                        // WebView 还未加载完毕，暂存等待
                        pendingPlaylistJson = playlistJson
                        showLoading("正在准备播放器...", 98)
                    }
                }
            }

            override fun onSyncFailed(error: String) {
                isSyncing = false
                Log.w(TAG, "Sync failed: $error")

                uiHandler.post {
                    when (error) {
                        "no_playlist" -> {
                            // 服务器未分配播放列表，使用默认列表
                            showLoading("未分配播放列表，使用默认内容", 100)
                        }
                        else -> {
                            // 网络错误等，尝试使用已缓存列表
                            showLoading("同步失败，使用本地缓存...", 80)
                        }
                    }
                    // 延迟 1.5 秒后进入播放（让用户看到提示）
                    uiHandler.postDelayed({
                        if (webViewReady) {
                            // 使用 DefaultPlaylistManager 中当前激活的列表
                            val json = defaultPlaylistManager.getActivePlaylistJson()
                            injectPlaylistAndHideLoading(json)
                        }
                        // 否则 onPageFinished 中会处理
                    }, 1500)
                }
            }

            override fun onProgress(percent: Int, message: String) {
                uiHandler.post { showLoading(message, percent) }
            }
        })
    }

    // ─────────────────────────────────────────────────
    //  WebView 播放列表注入
    // ─────────────────────────────────────────────────

    /**
     * 将播放列表 JSON 注入 WebView 并隐藏加载覆盖层。
     * 调用 player_local.html 中暴露的 window.loadPlaylistJson(json)。
     */
    private fun injectPlaylistAndHideLoading(playlistJson: String?) {
        if (playlistJson.isNullOrEmpty()) {
            hideLoading()
            return
        }
        // 转义 JSON 用于 JS 字符串（防止单引号/换行破坏语法）
        val escaped = playlistJson
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "")

        val js = "window.loadPlaylistJson('$escaped');"
        webView.evaluateJavascript(js, null)
        hideLoading()

        // 标记开始播放，隐藏设备 ID
        isPlaying = true
        hideDeviceId()

        Log.d(TAG, "Playlist injected into WebView")
    }

    // ─────────────────────────────────────────────────
    //  WebSocket
    // ─────────────────────────────────────────────────

    private fun initWebSocket() {
        deviceId?.let { id ->
            WebSocketManager.connect(id, object : WebSocketManager.WebSocketListener {
                override fun onRegistered() {
                    Log.d(TAG, "WebSocket registered")
                }

                override fun onPlaylistUpdate(playlistId: Int) {
                    Log.d(TAG, "Playlist update: $playlistId")
                    uiHandler.post {
                        showLoading("收到更新，重新同步...", 0)
                        performSync()
                    }
                }

                override fun onScheduleUpdate() {
                    Log.d(TAG, "Schedule update")
                    uiHandler.post { performSync() }
                }

                override fun onForceSync() {
                    Log.d(TAG, "Force sync")
                    uiHandler.post { performSync() }
                }

                override fun onReboot() {
                    Log.d(TAG, "Reboot command")
                    uiHandler.post { restartApp() }
                }
            })
        }
    }

    /**
     * 观察 WebSocket 事件（协程版本）
     */
    private fun observeWebSocketEvents() {
        lifecycleScope.launch {
            WebSocketManager.events.collectLatest { event ->
                when (event) {
                    is WebSocketManager.WebSocketEvent.PlaylistUpdate -> {
                        Log.d(TAG, "WebSocket event: Playlist update ${event.playlistId}")
                    }
                    is WebSocketManager.WebSocketEvent.ForceSync -> {
                        Log.d(TAG, "WebSocket event: Force sync")
                    }
                    else -> { /* 其他事件由 Listener 处理 */ }
                }
            }
        }
    }

    private fun restartApp() {
        packageManager.getLaunchIntentForPackage(packageName)?.let { intent ->
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
            startActivity(intent)
            finish()
            System.exit(0)
        }
    }

    // ─────────────────────────────────────────────────
    //  UI 辅助方法
    // ─────────────────────────────────────────────────

    @Suppress("DEPRECATION")
    private fun hideSystemUI() {
        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_FULLSCREEN
        )
    }

    private fun showLoading(message: String, progress: Int) {
        loadingContainer?.visibility = View.VISIBLE
        statusText?.text = message
        if (progress >= 0) {
            progressBar?.progress = progress
        }
        // 加载时显示设备 ID
        isPlaying = false
        showDeviceIdTemporarily()
    }

    private fun hideLoading() {
        loadingContainer?.visibility = View.GONE
    }

    private fun startHeartbeat() {
        heartbeatHandler = Handler(Looper.getMainLooper())
        heartbeatRunnable = object : Runnable {
            override fun run() {
                WebSocketManager.sendHeartbeat()
                heartbeatHandler?.postDelayed(this, 60_000)
            }
        }
        heartbeatHandler?.postDelayed(heartbeatRunnable!!, 60_000)
    }
}
