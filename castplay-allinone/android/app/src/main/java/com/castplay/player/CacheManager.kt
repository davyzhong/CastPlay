package com.castplay.player

import android.app.DownloadManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.database.Cursor
import android.net.Uri
import android.os.Environment
import android.util.Log
import org.json.JSONObject
import java.io.File
import java.util.concurrent.ConcurrentHashMap

/**
 * 媒体缓存管理器
 * 负责下载、缓存和管理媒体文件
 */
class CacheManager private constructor(private val context: Context) {

    companion object {
        private const val TAG = "CacheManager"
        private const val MEDIA_DIR = "CastPlay/media"

        @Volatile
        private var instance: CacheManager? = null

        fun getInstance(context: Context): CacheManager {
            return instance ?: synchronized(this) {
                instance ?: CacheManager(context.applicationContext).also { instance = it }
            }
        }
    }

    private val downloadManager: DownloadManager by lazy {
        context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
    }

    private val downloadProgress = ConcurrentHashMap<String, Int>()
    private val downloadIds = ConcurrentHashMap<String, Long>()
    private val mediaCacheDir: File by lazy {
        File(context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), MEDIA_DIR).apply {
            if (!exists()) mkdirs()
        }
    }

    private val prefs by lazy {
        context.getSharedPreferences("media_cache", Context.MODE_PRIVATE)
    }

    init {
        // 注册下载完成广播接收器
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (DownloadManager.ACTION_DOWNLOAD_COMPLETE == intent?.action) {
                    val downloadId = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1)
                    handleDownloadComplete(downloadId)
                }
            }
        }
        context.registerReceiver(receiver, IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE))
    }

    /**
     * 下载媒体文件
     */
    fun downloadMedia(url: String, mediaId: String) {
        if (isMediaCached(mediaId)) {
            Log.d(TAG, "Media already cached: $mediaId")
            return
        }

        val targetFile = File(mediaCacheDir, mediaId)

        val request = DownloadManager.Request(Uri.parse(url))
            .setTitle("CastPlay Media $mediaId")
            .setDescription("Downloading media file")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_HIDDEN)
            .setDestinationUri(Uri.fromFile(targetFile))
            .setAllowedOverMetered(true)
            .setAllowedRoaming(true)

        val downloadId = downloadManager.enqueue(request)
        downloadIds[mediaId] = downloadId
        downloadProgress[mediaId] = 0

        // 保存下载信息
        prefs.edit()
            .putLong("download_$mediaId", downloadId)
            .apply()

        Log.d(TAG, "Started download: $mediaId, downloadId: $downloadId")

        // 启动进度监控
        monitorDownloadProgress(mediaId, downloadId)
    }

    /**
     * 监控下载进度
     */
    private fun monitorDownloadProgress(mediaId: String, downloadId: Long) {
        Thread {
            var completed = false
            while (!completed) {
                val query = DownloadManager.Query().setFilterById(downloadId)
                val cursor: Cursor? = downloadManager.query(query)

                cursor?.use {
                    if (cursor.moveToFirst()) {
                        val bytesDownloaded = cursor.getLong(
                            cursor.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)
                        )
                        val totalBytes = cursor.getLong(
                            cursor.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)
                        )
                        val status = cursor.getInt(
                            cursor.getColumnIndex(DownloadManager.COLUMN_STATUS)
                        )

                        val progress = if (totalBytes > 0) {
                            ((bytesDownloaded * 100) / totalBytes).toInt()
                        } else 0

                        downloadProgress[mediaId] = progress

                        if (status == DownloadManager.STATUS_SUCCESSFUL) {
                            completed = true
                            downloadProgress[mediaId] = 100
                        } else if (status == DownloadManager.STATUS_FAILED) {
                            completed = true
                            downloadProgress[mediaId] = -1 // 错误标志
                            Log.e(TAG, "Download failed: $mediaId")
                        }
                    }
                }

                if (!completed) {
                    Thread.sleep(500)
                }
            }
        }.start()
    }

    /**
     * 处理下载完成
     */
    private fun handleDownloadComplete(downloadId: Long) {
        val mediaId = downloadIds.entries.find { it.value == downloadId }?.key
        mediaId?.let { id ->
            val query = DownloadManager.Query().setFilterById(downloadId)
            val cursor: Cursor? = downloadManager.query(query)

            cursor?.use {
                if (cursor.moveToFirst()) {
                    val localUri = cursor.getString(
                        cursor.getColumnIndex(DownloadManager.COLUMN_LOCAL_URI)
                    )
                    localUri?.let { uri ->
                        prefs.edit()
                            .putString("path_$id", uri)
                            .putBoolean("cached_$id", true)
                            .apply()
                        Log.d(TAG, "Download complete: $id, path: $localUri")
                    }
                }
            }

            downloadIds.remove(id)
        }
    }

    /**
     * 获取下载进度
     */
    fun getDownloadProgress(mediaId: String): Int {
        return downloadProgress[mediaId] ?: 0
    }

    /**
     * 检查媒体是否已缓存
     */
    fun isMediaCached(mediaId: String): Boolean {
        return prefs.getBoolean("cached_$mediaId", false)
    }

    /**
     * 获取缓存的媒体路径
     */
    fun getCachedMediaPath(mediaId: String): String {
        if (!isMediaCached(mediaId)) return ""

        val storedPath = prefs.getString("path_$mediaId", null)
        if (storedPath != null) {
            val file = File(Uri.parse(storedPath).path ?: return "")
            if (file.exists()) return file.absolutePath
        }

        // 检查默认路径
        val defaultFile = File(mediaCacheDir, mediaId)
        return if (defaultFile.exists()) defaultFile.absolutePath else ""
    }

    /**
     * 清除缓存
     */
    fun clearCache() {
        mediaCacheDir.deleteRecursively()
        mediaCacheDir.mkdirs()
        prefs.edit().clear().apply()
        downloadProgress.clear()
        downloadIds.clear()
    }

    /**
     * 获取缓存大小
     */
    fun getCacheSize(): Long {
        return calculateDirectorySize(mediaCacheDir)
    }

    private fun calculateDirectorySize(directory: File): Long {
        var size: Long = 0
        directory.listFiles()?.forEach { file ->
            size += if (file.isDirectory) {
                calculateDirectorySize(file)
            } else {
                file.length()
            }
        }
        return size
    }
}
