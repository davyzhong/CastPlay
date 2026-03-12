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
        // 开发环境使用端口 8000
        return "http://10.0.2.2:8000"
    }
}
