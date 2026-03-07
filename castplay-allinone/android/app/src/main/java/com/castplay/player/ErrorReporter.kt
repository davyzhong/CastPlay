package com.castplay.player

import android.content.Context
import android.util.Log
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * 错误上报服务
 * 统一收集和上报 Android 播放端错误
 */
class ErrorReporter private constructor(private val context: Context) {

    companion object {
        private const val TAG = "ErrorReporter"

        // 错误类型常量
        const val TYPE_DOWNLOAD_FAILED = "download_failed"
        const val TYPE_PLAYBACK_ERROR = "playback_error"
        const val TYPE_CACHE_ERROR = "cache_error"
        const val TYPE_NETWORK_ERROR = "network_error"
        const val TYPE_PLAYLIST_SYNC_FAILED = "playlist_sync_failed"
        const val TYPE_REGISTRATION_FAILED = "registration_failed"
        const val TYPE_INSUFFICIENT_STORAGE = "insufficient_storage"
        const val TYPE_SWITCH_FAILED = "switch_failed"
        const val TYPE_MEDIA_LOAD_ERROR = "media_load_error"
        const val TYPE_UNKNOWN_ERROR = "unknown_error"

        // 配置
        private const val MAX_QUEUE_SIZE = 50
        private const val FLUSH_INTERVAL_MS = 30000L  // 30 秒
        private const val API_ENDPOINT = "/api/player/devices/notifications"

        @Volatile
        private var instance: ErrorReporter? = null

        fun getInstance(context: Context): ErrorReporter {
            return instance ?: synchronized(this) {
                instance ?: ErrorReporter(context.applicationContext).also { instance = it }
            }
        }
    }

    private val errorQueue = ConcurrentLinkedQueue<ErrorReport>()
    private val executor = Executors.newSingleThreadScheduledExecutor()
    private val prefs by lazy {
        context.getSharedPreferences("error_reporter", Context.MODE_PRIVATE)
    }

    private var deviceId: String? = null
    private var serverUrl: String? = null

    data class ErrorReport(
        val type: String,
        val message: String,
        val playlistId: Long? = null,
        val mediaId: String? = null,
        val timestamp: Long = System.currentTimeMillis(),
        val additionalData: Map<String, Any>? = null
    )

    init {
        // 启动定时刷新任务
        startFlushTimer()
    }

    /**
     * 初始化错误上报服务
     */
    fun init(deviceId: String, serverUrl: String) {
        this.deviceId = deviceId
        this.serverUrl = serverUrl
        Log.d(TAG, "ErrorReporter initialized for device: $deviceId")
    }

    /**
     * 设置设备 ID
     */
    fun setDeviceId(deviceId: String) {
        this.deviceId = deviceId
    }

    /**
     * 设置服务器 URL
     */
    fun setServerUrl(url: String) {
        this.serverUrl = url
    }

    /**
     * 上报错误
     */
    fun reportError(
        type: String,
        message: String,
        playlistId: Long? = null,
        mediaId: String? = null,
        additionalData: Map<String, Any>? = null
    ) {
        if (deviceId == null) {
            Log.w(TAG, "Cannot report error: device ID not set")
            return
        }

        val report = ErrorReport(
            type = type,
            message = message,
            playlistId = playlistId,
            mediaId = mediaId,
            additionalData = additionalData
        )

        // 防止队列过大
        if (errorQueue.size >= MAX_QUEUE_SIZE) {
            errorQueue.poll()  // 移除最旧的
        }

        errorQueue.offer(report)
        Log.w(TAG, "Error reported: [$type] $message")

        // 如果是严重错误，立即发送
        if (isCriticalError(type)) {
            flush()
        }
    }

    /**
     * 判断是否为严重错误
     */
    private fun isCriticalError(type: String): Boolean {
        return type in listOf(
            TYPE_INSUFFICIENT_STORAGE,
            TYPE_REGISTRATION_FAILED,
            TYPE_SWITCH_FAILED
        )
    }

    /**
     * 上报下载失败
     */
    fun reportDownloadFailed(
        message: String,
        playlistId: Long? = null,
        mediaId: String? = null
    ) {
        reportError(TYPE_DOWNLOAD_FAILED, message, playlistId, mediaId)
    }

    /**
     * 上报播放错误
     */
    fun reportPlaybackError(
        message: String,
        mediaId: String? = null,
        additionalData: Map<String, Any>? = null
    ) {
        reportError(TYPE_PLAYBACK_ERROR, message, mediaId = mediaId, additionalData = additionalData)
    }

    /**
     * 上报缓存错误
     */
    fun reportCacheError(message: String) {
        reportError(TYPE_CACHE_ERROR, message)
    }

    /**
     * 上报网络错误
     */
    fun reportNetworkError(message: String) {
        reportError(TYPE_NETWORK_ERROR, message)
    }

    /**
     * 上报播放列表同步失败
     */
    fun reportPlaylistSyncFailed(message: String, playlistId: Long? = null) {
        reportError(TYPE_PLAYLIST_SYNC_FAILED, message, playlistId = playlistId)
    }

    /**
     * 上报存储空间不足
     */
    fun reportInsufficientStorage(requiredBytes: Long, availableBytes: Long) {
        reportError(
            TYPE_INSUFFICIENT_STORAGE,
            "Storage insufficient: required $requiredBytes, available $availableBytes",
            additionalData = mapOf(
                "required_bytes" to requiredBytes,
                "available_bytes" to availableBytes
            )
        )
    }

    /**
     * 刷新错误队列到服务器
     */
    fun flush() {
        if (errorQueue.isEmpty() || deviceId == null || serverUrl == null) {
            return
        }

        val errorsToSend = mutableListOf<ErrorReport>()
        while (errorQueue.isNotEmpty()) {
            errorQueue.poll()?.let { errorsToSend.add(it) }
        }

        if (errorsToSend.isEmpty()) return

        // 在后台线程发送
        Thread {
            for (error in errorsToSend) {
                sendErrorReport(error)
            }
        }.start()
    }

    /**
     * 发送单个错误报告
     */
    private fun sendErrorReport(error: ErrorReport) {
        try {
            val url = URL("${serverUrl}${API_ENDPOINT}")
            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
                connectTimeout = 5000
                readTimeout = 5000
                doOutput = true
            }

            val jsonBody = JSONObject().apply {
                put("device_id", deviceId)
                put("type", error.type)
                put("error_message", error.message)
                error.playlistId?.let { put("playlist_id", it) }
                error.mediaId?.let { put("media_id", it) }
                error.additionalData?.let { data ->
                    put("additional_data", JSONObject(data))
                }
            }

            connection.outputStream.use { os ->
                os.write(jsonBody.toString().toByteArray(Charsets.UTF_8))
            }

            val responseCode = connection.responseCode
            if (responseCode in 200..299) {
                Log.d(TAG, "Error report sent successfully: ${error.type}")
            } else {
                Log.e(TAG, "Failed to send error report: HTTP $responseCode")
                // 重新加入队列
                errorQueue.offer(error)
            }

            connection.disconnect()
        } catch (e: Exception) {
            Log.e(TAG, "Exception sending error report: ${e.message}")
            // 重新加入队列
            errorQueue.offer(error)
        }
    }

    /**
     * 启动定时刷新
     */
    private fun startFlushTimer() {
        executor.scheduleWithFixedDelay({
            try {
                flush()
            } catch (e: Exception) {
                Log.e(TAG, "Error in flush timer: ${e.message}")
            }
        }, FLUSH_INTERVAL_MS, FLUSH_INTERVAL_MS, TimeUnit.MILLISECONDS)
    }

    /**
     * 停止服务
     */
    fun stop() {
        flush()
        executor.shutdown()
        try {
            if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                executor.shutdownNow()
            }
        } catch (e: InterruptedException) {
            executor.shutdownNow()
        }
    }

    /**
     * 获取队列长度
     */
    fun getQueueSize(): Int = errorQueue.size
}
