package com.castplay.player

import android.app.DownloadManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.database.Cursor
import android.net.Uri
import android.os.Environment
import android.os.Looper
import android.util.Log
import androidx.annotation.WorkerThread
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import kotlin.math.min

/**
 * 媒体缓存管理器
 * 负责下载、缓存和管理媒体文件
 *
 * 增强功能：
 * - MD5 校验
 * - 下载失败重试（最多 3 次，指数退避）
 * - 改进下载监控
 */
class CacheManager private constructor(private val context: Context) {

    companion object {
        private const val TAG = "CacheManager"
        private const val MEDIA_DIR = "CastPlay/media"

        // 重试配置
        private const val MAX_RETRY_COUNT = 3
        private const val INITIAL_RETRY_DELAY_MS = 1000L  // 1 秒
        private const val MAX_RETRY_DELAY_MS = 10000L     // 10 秒

        // 存储管理配置
        private const val MIN_FREE_SPACE_BYTES = 100 * 1024 * 1024L  // 100MB
        private const val MAX_CACHE_SIZE_BYTES = 5L * 1024 * 1024 * 1024  // 5GB
        private const val OLD_FILE_THRESHOLD_DAYS = 30  // 30 天
        private const val STORAGE_WARNING_THRESHOLD_PERCENT = 90  // 90%

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
    private val retryCount = ConcurrentHashMap<String, Int>()
    private val expectedMd5 = ConcurrentHashMap<String, String>()

    // P1-10 修复：使用共享线程池替代无限制线程创建
    private val ioExecutor: ExecutorService = Executors.newFixedThreadPool(
        Runtime.getRuntime().availableProcessors().coerceAtLeast(2)
    )

    // P0-2 修复：将 receiver 改为类成员变量以便注销
    private var downloadCompleteReceiver: BroadcastReceiver? = null

    private val mediaCacheDir: File by lazy {
        File(context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), MEDIA_DIR).apply {
            if (!exists()) mkdirs()
        }
    }

    private val prefs by lazy {
        context.getSharedPreferences("media_cache", Context.MODE_PRIVATE)
    }

    // 下载回调接口
    interface DownloadCallback {
        fun onProgress(mediaId: String, progress: Int)
        fun onSuccess(mediaId: String, filePath: String)
        fun onError(mediaId: String, error: String)
    }

    private var downloadCallback: DownloadCallback? = null

    fun setDownloadCallback(callback: DownloadCallback) {
        downloadCallback = callback
    }

    init {
        // P0-2 修复：注册下载完成广播接收器，保存引用以便后续注销
        downloadCompleteReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (DownloadManager.ACTION_DOWNLOAD_COMPLETE == intent?.action) {
                    val downloadId = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1)
                    handleDownloadComplete(downloadId)
                }
            }
        }
        context.registerReceiver(
            downloadCompleteReceiver,
            IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE)
        )
    }

    /**
     * 下载媒体文件（带 MD5 校验和重试）
     *
     * @param url 下载地址
     * @param mediaId 媒体 ID
     * @param md5Hash 预期的 MD5 哈希值（可选，用于校验）
     */
    fun downloadMedia(url: String, mediaId: String, md5Hash: String? = null) {
        if (isMediaCached(mediaId)) {
            // 如果已缓存，验证 MD5
            val cachedPath = getCachedMediaPath(mediaId)
            if (cachedPath.isNotEmpty() && md5Hash != null) {
                if (verifyMd5(cachedPath, md5Hash)) {
                    Log.d(TAG, "Media already cached and verified: $mediaId")
                    return
                } else {
                    Log.w(TAG, "Cached file MD5 mismatch, re-downloading: $mediaId")
                    deleteCachedMedia(mediaId)
                }
            } else {
                Log.d(TAG, "Media already cached: $mediaId")
                return
            }
        }

        // 保存预期的 MD5
        if (md5Hash != null) {
            expectedMd5[mediaId] = md5Hash
        }

        // 重置重试计数
        retryCount[mediaId] = 0

        startDownload(url, mediaId)
    }

    /**
     * 启动下载
     */
    private fun startDownload(url: String, mediaId: String) {
        // P0-1 修复：保存 URL 以便重试时使用
        prefs.edit().putString("url_$mediaId", url).apply()

        val targetFile = File(mediaCacheDir, mediaId)

        // 如果存在部分下载的文件，删除它
        if (targetFile.exists()) {
            targetFile.delete()
        }

        val request = DownloadManager.Request(Uri.parse(url))
            .setTitle("CastPlay Media $mediaId")
            .setDescription("Downloading media file")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_HIDDEN)
            .setDestinationUri(Uri.fromFile(targetFile))
            .setAllowedOverMetered(true)
            // setAllowedRoaming 在 API 29 中被移除，使用 setRequiresDeviceIdle 替代
            .setRequiresDeviceIdle(false)
            .setRequiresCharging(false)

        try {
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
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start download: $mediaId", e)
            handleDownloadError(mediaId, "Failed to start download: ${e.message}")
        }
    }

    /**
     * 监控下载进度
     */
    private fun monitorDownloadProgress(mediaId: String, downloadId: Long) {
        // P1-10 修复：使用共享线程池替代 Thread{}.start()
        ioExecutor.execute {
            var completed = false
            while (!completed) {
                try {
                    val query = DownloadManager.Query().setFilterById(downloadId)
                    val cursor: Cursor? = downloadManager.query(query)

                    cursor?.use {
                        if (cursor.moveToFirst()) {
                            val bytesDownloaded = cursor.getLong(
                                cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)
                            )
                            val totalBytes = cursor.getLong(
                                cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)
                            )
                            val status = cursor.getInt(
                                cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)
                            )

                            val progress = if (totalBytes > 0) {
                                ((bytesDownloaded * 100) / totalBytes).toInt()
                            } else 0

                            downloadProgress[mediaId] = progress

                            // 回调进度
                            downloadCallback?.onProgress(mediaId, progress)

                            when (status) {
                                DownloadManager.STATUS_SUCCESSFUL -> {
                                    completed = true
                                    downloadProgress[mediaId] = 100
                                }
                                DownloadManager.STATUS_FAILED -> {
                                    completed = true
                                    downloadProgress[mediaId] = -1
                                    // 错误处理在 handleDownloadComplete 中进行
                                }
                                DownloadManager.STATUS_PAUSED -> {
                                    Log.d(TAG, "Download paused: $mediaId")
                                }
                            }
                        }
                    }

                    if (!completed) {
                        Thread.sleep(500)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error monitoring download: $mediaId", e)
                    completed = true
                    handleDownloadError(mediaId, "Monitoring error: ${e.message}")
                }
            }
        }
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
                    val status = cursor.getInt(
                        cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)
                    )

                    when (status) {
                        DownloadManager.STATUS_SUCCESSFUL -> {
                            val localUri = cursor.getString(
                                cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_LOCAL_URI)
                            )
                            localUri?.let { uri ->
                                val filePath = Uri.parse(uri).path

                                // MD5 校验
                                val expectedMd5Hash = expectedMd5[id]
                                if (expectedMd5Hash != null && filePath != null) {
                                    if (verifyMd5(filePath, expectedMd5Hash)) {
                                        Log.d(TAG, "MD5 verification passed: $id")
                                        saveCachedMedia(id, uri)
                                        downloadCallback?.onSuccess(id, filePath)
                                    } else {
                                        Log.e(TAG, "MD5 verification failed: $id")
                                        handleDownloadError(id, "MD5 verification failed")
                                        return
                                    }
                                } else {
                                    saveCachedMedia(id, uri)
                                    downloadCallback?.onSuccess(id, filePath ?: "")
                                }
                            }
                        }
                        DownloadManager.STATUS_FAILED -> {
                            val reason = cursor.getInt(
                                cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON)
                            )
                            Log.e(TAG, "Download failed: $id, reason: $reason")
                            handleDownloadError(id, "Download failed with reason: $reason")
                        }
                    }
                }
            }

            downloadIds.remove(id)
            expectedMd5.remove(id)
        }
    }

    /**
     * 保存缓存媒体信息
     */
    private fun saveCachedMedia(mediaId: String, uri: String) {
        prefs.edit()
            .putString("path_$mediaId", uri)
            .putBoolean("cached_$mediaId", true)
            .remove("retry_$mediaId")
            .apply()
        Log.d(TAG, "Download complete: $mediaId, path: $uri")
    }

    /**
     * 处理下载错误（带重试机制）
     */
    private fun handleDownloadError(mediaId: String, error: String) {
        val currentRetryCount = retryCount[mediaId] ?: 0

        if (currentRetryCount < MAX_RETRY_COUNT) {
            // 指数退避重试
            val delay = min(
                INITIAL_RETRY_DELAY_MS * (1 shl currentRetryCount),
                MAX_RETRY_DELAY_MS
            )

            retryCount[mediaId] = currentRetryCount + 1
            Log.w(TAG, "Retrying download ($currentRetryCount/$MAX_RETRY_COUNT) for $mediaId after ${delay}ms")

            // 保存重试信息
            prefs.edit()
                .putInt("retry_$mediaId", currentRetryCount + 1)
                .apply()

            // P1-10 修复：使用共享线程池延迟重试
            ioExecutor.execute {
                Thread.sleep(delay)
                // 重新获取下载 URL
                val savedUrl = prefs.getString("url_$mediaId", null)
                if (savedUrl != null) {
                    startDownload(savedUrl, mediaId)
                } else {
                    Log.e(TAG, "Cannot retry: no URL saved for $mediaId")
                    downloadCallback?.onError(mediaId, "$error (no retry URL)")
                }
            }
        } else {
            // 重试次数用尽
            Log.e(TAG, "Download failed after $MAX_RETRY_COUNT retries: $mediaId")
            retryCount.remove(mediaId)
            downloadProgress[mediaId] = -1

            // 通知错误上报服务
            ErrorReporter.getInstance(context).reportError(
                type = "download_failed",
                message = "Download failed after $MAX_RETRY_COUNT retries: $error",
                mediaId = mediaId
            )

            downloadCallback?.onError(mediaId, "$error (max retries exceeded)")
        }
    }

    /**
     * 计算 MD5 哈希值
     */
    fun calculateMd5(filePath: String): String? {
        return try {
            val file = File(filePath)
            if (!file.exists()) return null

            val md = MessageDigest.getInstance("MD5")
            val buffer = ByteArray(8192)

            // P0-3 修复：使用 use 扩展函数确保流被正确关闭
            FileInputStream(file).use { fis ->
                var bytesRead: Int
                while (fis.read(buffer).also { bytesRead = it } != -1) {
                    md.update(buffer, 0, bytesRead)
                }
            }

            val digest = md.digest()
            digest.joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to calculate MD5: $filePath", e)
            null
        }
    }

    /**
     * 验证 MD5
     */
    fun verifyMd5(filePath: String, expectedMd5: String): Boolean {
        val calculatedMd5 = calculateMd5(filePath)
        return calculatedMd5?.equals(expectedMd5, ignoreCase = true) == true
    }

    /**
     * 获取下载进度
     */
    fun getDownloadProgress(mediaId: String): Int {
        return downloadProgress[mediaId] ?: 0
    }

    /**
     * 获取重试次数
     */
    fun getRetryCount(mediaId: String): Int {
        return retryCount[mediaId] ?: 0
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
     * 删除缓存的媒体
     */
    fun deleteCachedMedia(mediaId: String) {
        val path = getCachedMediaPath(mediaId)
        if (path.isNotEmpty()) {
            File(path).delete()
        }

        prefs.edit()
            .remove("path_$mediaId")
            .remove("cached_$mediaId")
            .remove("download_$mediaId")
            .remove("retry_$mediaId")
            .remove("url_$mediaId")
            .apply()

        downloadProgress.remove(mediaId)
        downloadIds.remove(mediaId)
        retryCount.remove(mediaId)
        expectedMd5.remove(mediaId)
    }

    /**
     * 清除所有缓存
     */
    fun clearCache() {
        mediaCacheDir.deleteRecursively()
        mediaCacheDir.mkdirs()
        prefs.edit().clear().apply()
        downloadProgress.clear()
        downloadIds.clear()
        retryCount.clear()
        expectedMd5.clear()
    }

    /**
     * 获取缓存大小
     * P1-9 修复：添加主线程检测和警告
     */
    @WorkerThread
    fun getCacheSize(): Long {
        // P1-9 修复：检测是否在主线程调用
        if (Looper.myLooper() == Looper.getMainLooper()) {
            Log.w(TAG, "Warning: getCacheSize() called on main thread, may cause ANR")
        }
        return calculateDirectorySize(mediaCacheDir)
    }

    /**
     * 异步获取缓存大小（P1-9 修复：新增异步接口）
     * @param callback 回调函数，接收缓存大小（字节）
     */
    fun getCacheSizeAsync(callback: (Long) -> Unit) {
        ioExecutor.execute {
            val size = calculateDirectorySize(mediaCacheDir)
            callback(size)
        }
    }

    /**
     * 获取可用存储空间
     */
    fun getAvailableStorage(): Long {
        return mediaCacheDir.freeSpace
    }

    /**
     * 检查是否有足够空间
     * @param requiredBytes 需要的字节数
     */
    fun hasEnoughSpace(requiredBytes: Long): Boolean {
        return getAvailableStorage() > requiredBytes * 2  // 预留 2 倍空间
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

    // ==================== 存储空间管理 ====================

    /**
     * 检查存储空间状态
     *
     * @return StorageStatus 对象
     */
    fun checkStorageStatus(): StorageStatus {
        val totalSpace = mediaCacheDir.totalSpace
        val freeSpace = mediaCacheDir.freeSpace
        val usedSpace = totalSpace - freeSpace
        val usedPercent = if (totalSpace > 0) (usedSpace * 100 / totalSpace).toInt() else 0
        val cacheSize = getCacheSize()

        return StorageStatus(
            totalSpace = totalSpace,
            freeSpace = freeSpace,
            usedSpace = usedSpace,
            usedPercent = usedPercent,
            cacheSize = cacheSize,
            isLowStorage = freeSpace < MIN_FREE_SPACE_BYTES,
            isCacheOverLimit = cacheSize > MAX_CACHE_SIZE_BYTES
        )
    }

    /**
     * 存储状态数据类
     */
    data class StorageStatus(
        val totalSpace: Long,
        val freeSpace: Long,
        val usedSpace: Long,
        val usedPercent: Int,
        val cacheSize: Long,
        val isLowStorage: Boolean,
        val isCacheOverLimit: Boolean
    ) {
        fun toMap(): Map<String, Any> {
            return mapOf(
                "total_space" to totalSpace,
                "free_space" to freeSpace,
                "used_space" to usedSpace,
                "used_percent" to usedPercent,
                "cache_size" to cacheSize,
                "is_low_storage" to isLowStorage,
                "is_cache_over_limit" to isCacheOverLimit
            )
        }
    }

    /**
     * 清理旧缓存文件
     *
     * @param daysOld 超过多少天的文件视为旧文件
     * @return 清理的字节数
     */
    fun cleanupOldFiles(daysOld: Int = OLD_FILE_THRESHOLD_DAYS): Long {
        val cutoffTime = System.currentTimeMillis() - (daysOld * 24 * 60 * 60 * 1000L)
        var cleanedBytes: Long = 0

        mediaCacheDir.listFiles()?.forEach { file ->
            if (file.isFile && file.lastModified() < cutoffTime) {
                // 检查是否在当前播放列表中
                val mediaId = file.name
                if (!isMediaInCurrentPlaylist(mediaId)) {
                    cleanedBytes += file.length()
                    file.delete()
                    deleteCachedMedia(mediaId)
                    Log.d(TAG, "Cleaned old file: $mediaId")
                }
            }
        }

        if (cleanedBytes > 0) {
            Log.i(TAG, "Cleaned ${cleanedBytes / (1024 * 1024)}MB of old cache files")
        }

        return cleanedBytes
    }

    /**
     * 智能清理缓存
     * 当存储空间不足时，按策略清理文件
     *
     * @param requiredBytes 需要释放的空间（字节）
     * @return 实际清理的字节数
     */
    fun smartCleanup(requiredBytes: Long): Long {
        var cleanedBytes: Long = 0

        // 1. 首先清理旧文件
        cleanedBytes += cleanupOldFiles()

        // 2. 如果还不够，清理最大的非当前播放列表文件
        if (cleanedBytes < requiredBytes) {
            val nonCurrentFiles = mediaCacheDir.listFiles()
                ?.filter { it.isFile && !isMediaInCurrentPlaylist(it.name) }
                ?.sortedByDescending { it.length() }
                ?: emptyList()

            for (file in nonCurrentFiles) {
                if (cleanedBytes >= requiredBytes) break

                cleanedBytes += file.length()
                val mediaId = file.name
                file.delete()
                deleteCachedMedia(mediaId)
                Log.d(TAG, "Cleaned large file for space: $mediaId")
            }
        }

        // 3. 如果仍然不够，报告存储空间不足
        if (cleanedBytes < requiredBytes) {
            val availableAfter = getAvailableStorage()
            ErrorReporter.getInstance(context).reportInsufficientStorage(
                requiredBytes = requiredBytes,
                availableBytes = availableAfter
            )
        }

        return cleanedBytes
    }

    /**
     * 检查媒体是否在当前播放列表中
     * 子类可以重写此方法以实现更精确的判断
     */
    protected open fun isMediaInCurrentPlaylist(mediaId: String): Boolean {
        // 简单实现：检查最近访问时间
        val lastAccessTime = prefs.getLong("access_$mediaId", 0)
        val oneDayAgo = System.currentTimeMillis() - (24 * 60 * 60 * 1000L)
        return lastAccessTime > oneDayAgo
    }

    /**
     * 记录媒体访问时间
     */
    fun recordMediaAccess(mediaId: String) {
        prefs.edit()
            .putLong("access_$mediaId", System.currentTimeMillis())
            .apply()
    }

    /**
     * 获取存储使用情况摘要
     */
    fun getStorageSummary(): String {
        val status = checkStorageStatus()
        val cacheMB = status.cacheSize / (1024 * 1024)
        val freeMB = status.freeSpace / (1024 * 1024)
        val totalGB = status.totalSpace / (1024 * 1024 * 1024)

        return "Cache: ${cacheMB}MB, Free: ${freeMB}MB, Total: ${totalGB}GB, Used: ${status.usedPercent}%"
    }

    /**
     * 检查并自动清理（如果需要）
     */
    fun checkAndAutoCleanup(): Boolean {
        val status = checkStorageStatus()

        if (status.isLowStorage || status.isCacheOverLimit) {
            Log.w(TAG, "Storage check failed: ${getStorageSummary()}")

            // 计算需要清理的空间
            val requiredCleanup = when {
                status.isLowStorage -> MIN_FREE_SPACE_BYTES - status.freeSpace
                status.isCacheOverLimit -> status.cacheSize - MAX_CACHE_SIZE_BYTES
                else -> 0L
            }

            if (requiredCleanup > 0) {
                val cleaned = smartCleanup(requiredCleanup)
                Log.i(TAG, "Auto cleanup completed: cleaned ${cleaned / (1024 * 1024)}MB")
                return true
            }
        }

        return false
    }

    /**
     * 获取缓存文件列表（按最后修改时间排序）
     */
    fun getCachedFiles(): List<CacheFileInfo> {
        return mediaCacheDir.listFiles()
            ?.filter { it.isFile }
            ?.map { file ->
                CacheFileInfo(
                    mediaId = file.name,
                    path = file.absolutePath,
                    size = file.length(),
                    lastModified = file.lastModified()
                )
            }
            ?.sortedByDescending { it.lastModified }
            ?: emptyList()
    }

    /**
     * 缓存文件信息
     */
    data class CacheFileInfo(
        val mediaId: String,
        val path: String,
        val size: Long,
        val lastModified: Long
    )

    // ==================== 播放列表批量下载 ====================

    /**
     * 播放列表下载回调
     */
    interface PlaylistDownloadCallback {
        fun onProgress(playlistId: Long, completed: Int, total: Int, percent: Int)
        fun onCompleted(playlistId: Long, successCount: Int, failedCount: Int)
        fun onError(playlistId: Long, error: String)
    }

    // 活动的播放列表下载
    private val activePlaylistDownloads = ConcurrentHashMap<Long, PlaylistDownloadJob>()

    /**
     * 媒体项信息
     */
    data class MediaItemInfo(
        val id: Long,
        val url: String,
        val fileName: String? = null,
        val fileSize: Long? = null,
        val md5Hash: String? = null
    )

    /**
     * 播放列表下载任务
     */
    private inner class PlaylistDownloadJob(
        private val playlistId: Long,
        private val mediaList: List<MediaItemInfo>,
        private val callback: PlaylistDownloadCallback
    ) {
        @Volatile private var cancelled = false
        private val completed = java.util.concurrent.atomic.AtomicInteger(0)
        private val failed = java.util.concurrent.atomic.AtomicInteger(0)
        private val semaphore = java.util.concurrent.Semaphore(3) // 最多 3 个并发

        fun execute() {
            val total = mediaList.size
            val latch = java.util.concurrent.CountDownLatch(total)

            for (media in mediaList) {
                if (cancelled) break

                ioExecutor.execute {
                    semaphore.acquire()
                    try {
                        if (!cancelled) {
                            val success = downloadSingleMediaWithRetry(media)
                            if (success) {
                                completed.incrementAndGet()
                            } else {
                                failed.incrementAndGet()
                            }
                        }
                    } finally {
                        semaphore.release()
                        latch.countDown()

                        // 回调进度
                        val currentCompleted = completed.get()
                        val currentFailed = failed.get()
                        val percent = ((currentCompleted + currentFailed) * 100 / total)
                        callback.onProgress(playlistId, currentCompleted, total, percent)
                    }
                }
            }

            // 等待所有下载完成（最长 30 分钟）
            latch.await(30, java.util.concurrent.TimeUnit.MINUTES)

            // 回调完成
            if (cancelled) {
                callback.onError(playlistId, "Download cancelled")
            } else {
                callback.onCompleted(playlistId, completed.get(), failed.get())
            }

            activePlaylistDownloads.remove(playlistId)
        }

        private fun downloadSingleMediaWithRetry(media: MediaItemInfo): Boolean {
            var lastError: String? = null

            for (retry in 0..MAX_RETRY_COUNT) {
                if (cancelled) return false

                try {
                    // 检查是否已缓存
                    if (isMediaCached(media.id.toString())) {
                        // 验证 MD5
                        if (media.md5Hash != null) {
                            val path = getCachedMediaPath(media.id.toString())
                            if (path.isNotEmpty() && verifyMd5(path, media.md5Hash)) {
                                return true
                            } else {
                                deleteCachedMedia(media.id.toString())
                            }
                        } else {
                            return true
                        }
                    }

                    // 使用现有的下载逻辑
                    return downloadMediaWithRetryInternal(media.url, media.id.toString(), media.md5Hash) { cancelled }
                } catch (e: Exception) {
                    lastError = e.message
                    Log.w(TAG, "Download retry $retry for media ${media.id}: ${e.message}")

                    if (retry < MAX_RETRY_COUNT) {
                        val delay = min(INITIAL_RETRY_DELAY_MS * (1 shl retry), MAX_RETRY_DELAY_MS)
                        Thread.sleep(delay)
                    }
                }
            }

            Log.e(TAG, "Download failed after $MAX_RETRY_COUNT retries for media ${media.id}: $lastError")
            return false
        }

        fun cancel() {
            cancelled = true
        }
    }

    /**
     * 下载单个媒体文件（带重试，内部方法）
     */
    private fun downloadMediaWithRetryInternal(url: String, mediaId: String, md5Hash: String? = null, isCancelled: () -> Boolean = { false }): Boolean {
        val targetFile = File(mediaCacheDir, mediaId)

        // 如果存在部分下载的文件，删除它
        if (targetFile.exists()) {
            targetFile.delete()
        }

        // 使用 OkHttp 或系统下载管理器
        // 这里简化为同步下载
        return try {
            val request = DownloadManager.Request(Uri.parse(url))
                .setTitle("CastPlay Media $mediaId")
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_HIDDEN)
                .setDestinationUri(Uri.fromFile(targetFile))
                .setAllowedOverMetered(true)
                .setRequiresDeviceIdle(false)
                .setRequiresCharging(false)

            val downloadId = downloadManager.enqueue(request)
            downloadIds[mediaId] = downloadId

            // 等待下载完成
            var completed = false
            var success = false
            val startTime = System.currentTimeMillis()
            val timeout = 5 * 60 * 1000L // 5 分钟超时

            while (!completed && !isCancelled() && System.currentTimeMillis() - startTime < timeout) {
                val query = DownloadManager.Query().setFilterById(downloadId)
                val cursor: Cursor? = downloadManager.query(query)

                cursor?.use {
                    if (cursor.moveToFirst()) {
                        val status = cursor.getInt(
                            cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)
                        )

                        when (status) {
                            DownloadManager.STATUS_SUCCESSFUL -> {
                                completed = true
                                success = true

                                // MD5 校验
                                if (md5Hash != null && !verifyMd5(targetFile.absolutePath, md5Hash)) {
                                    targetFile.delete()
                                    success = false
                                }

                                if (success) {
                                    saveCachedMedia(mediaId, Uri.fromFile(targetFile).toString())
                                }
                            }
                            DownloadManager.STATUS_FAILED -> {
                                completed = true
                                success = false
                            }
                        }
                    }
                }

                if (!completed) {
                    Thread.sleep(500)
                }
            }

            downloadIds.remove(mediaId)
            success
        } catch (e: Exception) {
            Log.e(TAG, "Download failed for $mediaId", e)
            false
        }
    }

    /**
     * 开始播放列表下载
     */
    fun downloadPlaylist(
        playlistId: Long,
        mediaList: List<MediaItemInfo>,
        callback: PlaylistDownloadCallback
    ) {
        // 取消该播放列表的现有下载
        cancelPlaylistDownload(playlistId)

        val job = PlaylistDownloadJob(playlistId, mediaList, callback)
        activePlaylistDownloads[playlistId] = job

        ioExecutor.execute {
            job.execute()
        }
    }

    /**
     * 获取播放列表缓存状态
     */
    fun getPlaylistCacheStatus(playlistId: Long): PlaylistCacheStatus {
        // 获取与该播放列表相关的媒体 ID 列表
        val mediaIds = getPlaylistMediaIds(playlistId)
        var cachedCount = 0
        var totalSize = 0L
        var cachedSize = 0L

        for (mediaId in mediaIds) {
            val info = getMediaCacheInfoInternal(mediaId)
            totalSize += info.totalSize
            if (info.isCached) {
                cachedCount++
                cachedSize += info.cachedSize
            }
        }

        return PlaylistCacheStatus(
            playlistId = playlistId,
            totalFiles = mediaIds.size,
            cachedFiles = cachedCount,
            totalSize = totalSize,
            cachedSize = cachedSize,
            isReady = cachedCount == mediaIds.size
        )
    }

    /**
     * 获取播放列表媒体 ID 列表（从 SharedPreferences 恢复）
     */
    private fun getPlaylistMediaIds(playlistId: Long): List<String> {
        val key = "playlist_media_$playlistId"
        val mediaIdsStr = prefs.getString(key, "") ?: ""
        return if (mediaIdsStr.isNotEmpty()) mediaIdsStr.split(",") else emptyList()
    }

    /**
     * 保存播放列表媒体 ID 列表
     */
    fun savePlaylistMediaIds(playlistId: Long, mediaIds: List<String>) {
        val key = "playlist_media_$playlistId"
        prefs.edit().putString(key, mediaIds.joinToString(",")).apply()
    }

    /**
     * 获取媒体缓存信息（内部方法）
     */
    private fun getMediaCacheInfoInternal(mediaId: String): MediaCacheInfo {
        val isCached = prefs.getBoolean("cached_$mediaId", false)
        val path = if (isCached) prefs.getString("path_$mediaId", null) else null

        val file = if (path != null) File(Uri.parse(path).path ?: "") else null
        val fileSize = file?.length() ?: 0L

        return MediaCacheInfo(
            mediaId = mediaId,
            isCached = isCached && (file?.exists() == true),
            cachedSize = if (isCached && file?.exists() == true) fileSize else 0L,
            totalSize = fileSize
        )
    }

    /**
     * 媒体缓存信息
     */
    data class MediaCacheInfo(
        val mediaId: String,
        val isCached: Boolean,
        val cachedSize: Long,
        val totalSize: Long
    )

    /**
     * 播放列表缓存状态
     */
    data class PlaylistCacheStatus(
        val playlistId: Long,
        val totalFiles: Int,
        val cachedFiles: Int,
        val totalSize: Long,
        val cachedSize: Long,
        val isReady: Boolean
    ) {
        fun toJson(): String {
            return org.json.JSONObject().apply {
                put("playlist_id", playlistId)
                put("total_files", totalFiles)
                put("cached_files", cachedFiles)
                put("total_size", totalSize)
                put("cached_size", cachedSize)
                put("is_ready", isReady)
            }.toString()
        }
    }

    /**
     * 取消播放列表下载
     */
    fun cancelPlaylistDownload(playlistId: Long): Boolean {
        val job = activePlaylistDownloads.remove(playlistId)
        job?.cancel()
        return job != null
    }

    /**
     * 检查播放列表下载是否正在进行
     */
    fun isPlaylistDownloading(playlistId: Long): Boolean {
        return activePlaylistDownloads.containsKey(playlistId)
    }

    /**
     * P0-2 修复：销毁时注销广播接收器，防止内存泄漏
     */
    fun onDestroy() {
        downloadCompleteReceiver?.let {
            try {
                context.unregisterReceiver(it)
            } catch (e: Exception) {
                Log.e(TAG, "Error unregistering receiver: ${e.message}")
            }
        }
        downloadCompleteReceiver = null

        // P1-10 修复：关闭线程池
        ioExecutor.shutdown()
        try {
            if (!ioExecutor.awaitTermination(5, java.util.concurrent.TimeUnit.SECONDS)) {
                ioExecutor.shutdownNow()
            }
        } catch (e: InterruptedException) {
            ioExecutor.shutdownNow()
        }
    }
}
