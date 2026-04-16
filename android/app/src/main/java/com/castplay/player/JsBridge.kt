package com.castplay.player

import android.content.Context
import android.net.wifi.WifiManager
import android.os.Build
import android.webkit.JavascriptInterface
import android.widget.Toast
import java.net.NetworkInterface
import java.util.Collections

/**
 * JavaScript Bridge 接口
 * 注入到 WebView 中，提供原生功能访问
 */
class JsBridge(private val context: Context) {

    private val wifiManager: WifiManager? by lazy {
        context.applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
    }

    /**
     * 获取 MAC 地址
     */
    @JavascriptInterface
    fun getMacAddress(): String {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                // Android 6.0+ 需要权限，返回固定值
                return "02:00:00:00:00:00"
            } else {
                @Suppress("DEPRECATION")
                wifiManager?.connectionInfo?.macAddress?.let { mac ->
                    return mac.uppercase()
                } ?: run {
                    // 通过网络接口获取
                    val interfaces = Collections.list(NetworkInterface.getNetworkInterfaces())
                    for (iface in interfaces) {
                        val mac = iface.hardwareAddress
                        if (mac != null && mac.isNotEmpty()) {
                            return mac.joinToString(":") { byte ->
                                String.format("%02X", byte)
                            }
                        }
                    }
                    "02:00:00:00:00:00"
                }
            }
        } catch (e: Exception) {
            "02:00:00:00:00:00"
        }
    }

    /**
     * 获取 IP 地址
     */
    @JavascriptInterface
    fun getIPAddress(): String {
        return try {
            wifiManager?.connectionInfo?.let { info ->
                @Suppress("DEPRECATION")
                android.text.format.Formatter.formatIpAddress(info.ipAddress)
            } ?: "0.0.0.0"
        } catch (e: Exception) {
            "0.0.0.0"
        }
    }

    /**
     * 获取设备唯一 ID
     */
    @JavascriptInterface
    fun getDeviceId(): String {
        val mac = getMacAddress()
        return "device-${mac.replace(":", "")}"
    }

    /**
     * 获取注册码（基于 MAC 地址生成）
     */
    @JavascriptInterface
    fun getRegistrationCode(): String {
        val mac = getMacAddress()
        val cleanMac = mac.replace(":", "").uppercase()
        val hash = cleanMac.hashCode().toString(16).uppercase()
        val paddedHash = hash.padStart(12, '0').take(12)
        return "CP-${paddedHash.take(4)}-${paddedHash.substring(4, 8)}-${paddedHash.substring(8, 12)}"
    }

    /**
     * 下载媒体文件
     */
    @JavascriptInterface
    fun downloadMedia(url: String, mediaId: String) {
        // 通过 DownloadManager 处理
        CacheManager.getInstance(context).downloadMedia(url, mediaId)
    }

    /**
     * 获取下载进度
     */
    @JavascriptInterface
    fun getDownloadProgress(mediaId: String): Int {
        return CacheManager.getInstance(context).getDownloadProgress(mediaId)
    }

    /**
     * 检查媒体是否已缓存
     */
    @JavascriptInterface
    fun isMediaCached(mediaId: String): Boolean {
        return CacheManager.getInstance(context).isMediaCached(mediaId)
    }

    /**
     * 获取缓存的媒体路径
     */
    @JavascriptInterface
    fun getCachedMediaPath(mediaId: String): String {
        return CacheManager.getInstance(context).getCachedMediaPath(mediaId)
    }

    /**
     * 获取本地时区
     */
    @JavascriptInterface
    fun getLocalTimezone(): String {
        return java.util.TimeZone.getDefault().id
    }

    /**
     * 显示 Toast 消息
     */
    @JavascriptInterface
    fun showToast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }

    /**
     * 检查网络是否可用
     */
    @JavascriptInterface
    fun isNetworkAvailable(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE)
                as? android.net.ConnectivityManager
        return connectivityManager?.activeNetworkInfo?.isConnected == true
    }

    /**
     * 获取服务器 URL
     * 模拟器使用 10.0.2.2 访问宿主机
     */
    @JavascriptInterface
    fun getServerUrl(): String {
        return BuildConfig.SERVER_URL
    }

    // ==================== 播放列表下载接口 ====================

    /**
     * 开始播放列表下载
     *
     * @param playlistId 播放列表 ID
     * @param mediaListJson 媒体列表 JSON（数组格式）
     * @return 请求 ID
     */
    @JavascriptInterface
    fun startPlaylistDownload(playlistId: String, mediaListJson: String): String {
        val requestId = java.util.UUID.randomUUID().toString()

        try {
            // 解析媒体列表
            val jsonArray = org.json.JSONArray(mediaListJson)
            val mediaList = mutableListOf<CacheManager.MediaItemInfo>()

            for (i in 0 until jsonArray.length()) {
                val item = jsonArray.getJSONObject(i)
                val mediaItem = CacheManager.MediaItemInfo(
                    id = item.optLong("id", item.optLong("media_id", 0)),
                    url = item.getString("file_url"),
                    fileName = item.optString("file_name", null),
                    fileSize = if (item.has("file_size")) item.getLong("file_size") else null,
                    md5Hash = item.optString("md5_hash", null)
                )
                mediaList.add(mediaItem)
            }

            // 保存播放列表媒体 ID 映射
            val mediaIds = mediaList.map { it.id.toString() }
            CacheManager.getInstance(context).savePlaylistMediaIds(
                playlistId.toLong(),
                mediaIds
            )

            // 开始下载
            CacheManager.getInstance(context).downloadPlaylist(
                playlistId.toLong(),
                mediaList,
                object : CacheManager.PlaylistDownloadCallback {
                    override fun onProgress(playlistId: Long, completed: Int, total: Int, percent: Int) {
                        notifyWebView("onDownloadProgress", org.json.JSONObject().apply {
                            put("playlist_id", playlistId)
                            put("completed", completed)
                            put("total", total)
                            put("percent", percent)
                        }.toString())
                    }

                    override fun onCompleted(playlistId: Long, successCount: Int, failedCount: Int) {
                        notifyWebView("onDownloadCompleted", org.json.JSONObject().apply {
                            put("playlist_id", playlistId)
                            put("success_count", successCount)
                            put("failed_count", failedCount)
                        }.toString())
                    }

                    override fun onError(playlistId: Long, error: String) {
                        notifyWebView("onDownloadError", org.json.JSONObject().apply {
                            put("playlist_id", playlistId)
                            put("error", error)
                        }.toString())
                    }
                }
            )

            return requestId
        } catch (e: Exception) {
            android.util.Log.e("JsBridge", "Failed to start playlist download", e)
            return "error: ${e.message}"
        }
    }

    /**
     * 获取播放列表缓存状态
     *
     * @param playlistId 播放列表 ID
     * @return JSON 格式的状态信息
     */
    @JavascriptInterface
    fun getPlaylistCacheStatus(playlistId: String): String {
        val status = CacheManager.getInstance(context).getPlaylistCacheStatus(playlistId.toLong())
        return status.toJson()
    }

    /**
     * 取消播放列表下载
     *
     * @param playlistId 播放列表 ID
     * @return 是否成功取消
     */
    @JavascriptInterface
    fun cancelPlaylistDownload(playlistId: String): Boolean {
        return CacheManager.getInstance(context).cancelPlaylistDownload(playlistId.toLong())
    }

    /**
     * 检查播放列表是否正在下载
     *
     * @param playlistId 播放列表 ID
     * @return 是否正在下载
     */
    @JavascriptInterface
    fun isPlaylistDownloading(playlistId: String): Boolean {
        return CacheManager.getInstance(context).isPlaylistDownloading(playlistId.toLong())
    }

    /**
     * 报告播放列表切换完成
     *
     * @param playlistId 播放列表 ID
     * @param version 版本号
     */
    @JavascriptInterface
    fun reportSwitchComplete(playlistId: String, version: String) {
        // 记录切换完成
        val prefs = context.getSharedPreferences("playlist_switch", Context.MODE_PRIVATE)
        prefs.edit()
            .putString("current_playlist_id", playlistId)
            .putString("current_version", version)
            .putLong("switch_time", System.currentTimeMillis())
            .apply()

        android.util.Log.d("JsBridge", "Playlist switch completed: $playlistId v$version")
    }

    /**
     * 通知 WebView
     */
    private fun notifyWebView(event: String, data: String) {
        (context as? MainActivity)?.evaluateJavascript("window.AndroidBridgeCallbacks?.$event?.($data)")
    }
}
