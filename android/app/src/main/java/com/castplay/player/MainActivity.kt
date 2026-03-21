package com.castplay.player

import android.annotation.SuppressLint
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.view.WindowManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import java.io.File

/**
 * 主 Activity
 * WebView 宿主应用，加载播放器前端
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"
        private const val LOCAL_ASSET_URL = "file:///android_asset/www/player.html"
        private const val PREFS_NAME = "castplay_prefs"
        private const val KEY_SERVER_URL = "server_url"
    }

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var devicePolicyManager: DevicePolicyManager
    private lateinit var componentName: ComponentName

    private var serverUrl: String = BuildConfig.SERVER_URL

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 初始化 Kiosk 模式
        setupKioskMode()

        setContentView(R.layout.activity_main)

        // 设置全屏（必须在 setContentView 之后）
        setupFullscreen()

        progressBar = findViewById(R.id.progressBar)
        webView = findViewById(R.id.webView)

        // 获取配置的服务器 URL
        serverUrl = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getString(KEY_SERVER_URL, serverUrl) ?: serverUrl

        setupWebView()
        loadPlayer()
    }

    /**
     * 设置 Kiosk 模式
     */
    private fun setupKioskMode() {
        devicePolicyManager = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        componentName = ComponentName(this, MyDeviceAdminReceiver::class.java)

        // 启用 Kiosk 模式
        if (devicePolicyManager.isDeviceOwnerApp(packageName)) {
            enableKioskMode()
        } else {
            // 如果没有设备所有者权限，请求设置
            val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN)
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, componentName)
            startActivityForResult(intent, 1)
        }
    }

    /**
     * 启用 Kiosk 模式
     */
    private fun enableKioskMode() {
        try {
            // 创建 IntentFilter 用于 Kiosk 模式
            val intentFilter = IntentFilter(Intent.ACTION_MAIN).apply {
                addCategory(Intent.CATEGORY_HOME)
                addCategory(Intent.CATEGORY_DEFAULT)
            }
            devicePolicyManager.addPersistentPreferredActivity(
                componentName,
                intentFilter,
                ComponentName(this, MainActivity::class.java)
            )
            devicePolicyManager.setLockTaskPackages(componentName, arrayOf(packageName))
            startLockTask()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to enable kiosk mode", e)
        }
    }

    /**
     * 设置全屏显示
     */
    private fun setupFullscreen() {
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false)
            window.insetsController?.hide(android.view.WindowInsets.Type.systemBars())
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = (
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            )
        }
    }

    /**
     * 配置 WebView
     */
    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            mediaPlaybackRequiresUserGesture = false
            cacheMode = WebSettings.LOAD_DEFAULT
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            blockNetworkLoads = false
            loadsImagesAutomatically = true

            // 允许本地文件访问（解决 CORS 问题）
            allowFileAccessFromFileURLs = true
            allowUniversalAccessFromFileURLs = true

            // 设置 User Agent
            userAgentString = "CastPlay-Android/${BuildConfig.VERSION_NAME}"
        }

        // 启用调试（调试模式）
        if (BuildConfig.DEBUG) {
            WebView.setWebContentsDebuggingEnabled(true)
        }

        // 注入 JavaScript Bridge
        webView.addJavascriptInterface(JsBridge(this), "AndroidBridge")

        // 设置 WebViewClient
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                progressBar.visibility = View.GONE
                Log.d(TAG, "Page loaded: $url")
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                super.onReceivedError(view, request, error)
                Log.e(TAG, "WebView error: ${error?.description} for URL: ${request?.url}")

                // 只在主页面加载失败时才尝试加载本地资源
                // 检查是否是主页面请求（非 XHR/fetch API 请求）
                val requestUrl = request?.url.toString()
                val isMainFrame = request?.isForMainFrame == true

                // 只有在加载在线服务器主页面失败时才切换到本地资源
                if (isMainFrame && requestUrl.startsWith("http") && hasLocalAssets()) {
                    Log.w(TAG, "Main frame load failed, switching to local assets")
                    webView.loadUrl(LOCAL_ASSET_URL)
                }
                // 对于 API 请求失败（如心跳、媒体请求等），不做任何处理
                // 让前端代码自行处理离线逻辑
            }
        }

        // 设置 WebChromeClient
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progressBar.progress = newProgress
                if (newProgress == 100) {
                    progressBar.visibility = View.GONE
                } else {
                    progressBar.visibility = View.VISIBLE
                }
            }
        }
    }

    /**
     * 加载播放器
     */
    private fun loadPlayer() {
        progressBar.visibility = View.VISIBLE

        if (hasLocalAssets()) {
            // 优先加载本地资源（离线优先）
            Log.d(TAG, "Loading local assets")
            webView.loadUrl(LOCAL_ASSET_URL)
        } else if (serverUrl.isNotEmpty() && isServerReachable()) {
            // 加载远程服务器
            Log.d(TAG, "Loading from server: $serverUrl")
            webView.loadUrl(serverUrl)
        } else {
            // 显示错误提示
            Toast.makeText(this, R.string.no_server_connection, Toast.LENGTH_LONG).show()
            // 尝试重新加载
            webView.postDelayed({ loadPlayer() }, 5000)
        }
    }

    /**
     * 检查是否有本地资源
     */
    private fun hasLocalAssets(): Boolean {
        return try {
            assets.list("www")?.isNotEmpty() == true
        } catch (e: Exception) {
            false
        }
    }

    /**
     * 检查服务器是否可达
     */
    private fun isServerReachable(): Boolean {
        return try {
            val url = java.net.URL(serverUrl)
            val connection = url.openConnection() as java.net.HttpURLConnection
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            connection.requestMethod = "HEAD"
            val responseCode = connection.responseCode
            connection.disconnect()
            responseCode == 200
        } catch (e: Exception) {
            Log.w(TAG, "Server not reachable: ${e.message}")
            false
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        }
        // Kiosk 模式下不响应返回键
    }

    /**
     * 执行 JavaScript 代码（供 JsBridge 调用）
     */
    fun evaluateJavascript(script: String, callback: android.webkit.ValueCallback<String>? = null) {
        runOnUiThread {
            webView.evaluateJavascript(script, callback)
        }
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        // 恢复全屏
        setupFullscreen()
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}
