package com.castplay.player.service

import android.content.Context
import android.util.Log
import com.castplay.player.data.db.AppDatabase
import com.castplay.player.data.db.entity.MediaFileEntity
import com.castplay.player.data.db.entity.PlaylistEntity
import com.castplay.player.data.model.InitResponse
import com.castplay.player.network.ApiService
import com.castplay.player.network.RetrofitClient
import dagger.assisted.Assisted
import dagger.assisted.AssistedFactory
import dagger.assisted.AssistedInject
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.*
import okhttp3.ResponseBody
import org.json.JSONArray
import org.json.JSONObject
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException
import java.security.MessageDigest
import java.util.concurrent.Executors

/**
 * 同步管理器
 * 职责：
 *  1. 调用 /api/player/init，获取当前设备的播放列表
 *  2. 将媒体文件下载到 filesDir/media/ 目录
 *  3. 构建包含本地文件路径的播放列表 JSON，供 WebView 播放器使用
 *  4. 通过 SyncCallback 向调用方报告进度和结果
 */
class SyncManager @AssistedInject constructor(
    @ApplicationContext private val appContext: Context,
    private val database: AppDatabase,
    private val apiService: ApiService,
    @Assisted private val deviceId: String
) {

    /**
     * Hilt Assisted Inject Factory
     * 用于创建带有动态参数 (deviceId) 的 SyncManager 实例
     */
    @AssistedFactory
    interface Factory {
        fun create(deviceId: String): SyncManager
    }

    companion object {
        private const val TAG = "SyncManager"
    }

    private val executor = Executors.newSingleThreadExecutor()

    // ────────────────────────────────────────────────
    //  公开接口
    // ────────────────────────────────────────────────

    /**
     * 执行完整同步流程（回调版本，兼容旧代码）：
     *  1. 向服务器请求播放列表
     *  2. 下载媒体文件到本地
     *  3. 生成播放列表 JSON（含 local:/// 路径）
     *  4. 回调通知调用方
     */
    fun performFullSync(callback: SyncCallback?) {
        Log.d(TAG, "Starting full sync for device: $deviceId")

        val call = apiService.playerInit(ApiService.InitRequest(deviceId))

        call.enqueue(object : Callback<InitResponse> {
            override fun onResponse(call: Call<InitResponse>, response: Response<InitResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val initResponse = response.body()!!
                    val playlists = initResponse.playlists

                    // 服务器未分配播放列表
                    if (playlists.isNullOrEmpty()) {
                        Log.w(TAG, "No playlists assigned to this device")
                        callback?.onSyncFailed("no_playlist")
                        return
                    }

                    executor.execute {
                        try {
                            // Step 1: 更新 Room 数据库
                            notifyProgress(callback, 10, "正在更新播放列表...")
                            updatePlaylists(playlists)

                            // Step 2: 下载媒体文件
                            notifyProgress(callback, 20, "正在下载媒体文件...")
                            downloadMediaFiles(playlists, callback)

                            // Step 3: 构建 WebView 播放器 JSON
                            notifyProgress(callback, 95, "正在生成播放器配置...")
                            val playlistJson = buildPlayerJson(playlists)

                            Log.d(TAG, "Sync completed successfully")
                            notifyProgress(callback, 100, "同步完成")

                            callback?.onSyncSuccess(playlistJson, initResponse.schedule)
                        } catch (e: Exception) {
                            Log.e(TAG, "Sync failed", e)
                            callback?.onSyncFailed(e.message ?: "Unknown error")
                        }
                    }
                } else {
                    Log.e(TAG, "Init request failed: ${response.code()}")
                    callback?.onSyncFailed("server_error:${response.code()}")
                }
            }

            override fun onFailure(call: Call<InitResponse>, t: Throwable) {
                Log.e(TAG, "Init request network error", t)
                callback?.onSyncFailed(t.message ?: "Network error")
            }
        })
    }

    /**
     * 执行完整同步流程（协程版本）
     */
    suspend fun performFullSyncAsync(
        onProgress: ((Int, String) -> Unit)? = null
    ): Result<Pair<String, InitResponse.Schedule?>> = withContext(Dispatchers.IO) {
        try {
            Log.d(TAG, "Starting full sync (async) for device: $deviceId")

            val response = apiService.playerInitAsync(ApiService.InitRequest(deviceId))

            if (!response.isSuccessful || response.body() == null) {
                return@withContext Result.failure(Exception("server_error:${response.code()}"))
            }

            val initResponse = response.body()!!
            val playlists = initResponse.playlists

            if (playlists.isNullOrEmpty()) {
                Log.w(TAG, "No playlists assigned to this device")
                return@withContext Result.failure(Exception("no_playlist"))
            }

            // Step 1: 更新 Room 数据库
            withContext(Dispatchers.Main) { onProgress?.invoke(10, "正在更新播放列表...") }
            updatePlaylists(playlists)

            // Step 2: 下载媒体文件
            withContext(Dispatchers.Main) { onProgress?.invoke(20, "正在下载媒体文件...") }
            downloadMediaFilesAsync(playlists, onProgress)

            // Step 3: 构建 WebView 播放器 JSON
            withContext(Dispatchers.Main) { onProgress?.invoke(95, "正在生成播放器配置...") }
            val playlistJson = buildPlayerJson(playlists)

            Log.d(TAG, "Sync completed successfully (async)")
            withContext(Dispatchers.Main) { onProgress?.invoke(100, "同步完成") }

            Result.success(Pair(playlistJson, initResponse.schedule))
        } catch (e: Exception) {
            Log.e(TAG, "Sync failed (async)", e)
            Result.failure(e)
        }
    }

    // ────────────────────────────────────────────────
    //  私有方法：更新 Room DB
    // ────────────────────────────────────────────────

    private fun updatePlaylists(playlists: List<InitResponse.PlaylistData>) {
        val activeIds = mutableListOf<Int>()

        for (pd in playlists) {
            val pe = PlaylistEntity(
                id = pd.id,
                name = pd.name,
                version = pd.version,
                lastUpdated = System.currentTimeMillis()
            )
            database.playlistDao().insertSync(pe)
            activeIds.add(pd.id)

            pd.items?.forEach { item ->
                val mfe = MediaFileEntity(
                    id = item.mediaId,
                    playlistId = pd.id,
                    fileName = item.fileName,
                    fileType = item.fileType,
                    fileUrl = item.fileUrl,
                    displayOrder = item.displayOrder,
                    displayDuration = item.displayDuration,
                    fileSize = item.fileSize,
                    md5Hash = item.md5Hash,
                    isDownloaded = false
                )
                database.mediaFileDao().insertAllSync(listOf(mfe))
            }
        }

        if (activeIds.isNotEmpty()) {
            database.mediaFileDao().deleteInactivePlaylistsSync(activeIds)
        }
        Log.d(TAG, "Playlists updated in DB: ${playlists.size}")
    }

    // ────────────────────────────────────────────────
    //  私有方法：下载媒体文件
    // ────────────────────────────────────────────────

    private fun downloadMediaFiles(
        playlists: List<InitResponse.PlaylistData>,
        callback: SyncCallback?
    ) {
        val mediaDir = File(appContext.filesDir, "media").apply { mkdirs() }

        // 计算总文件数，用于进度报告
        val total = playlists.sumOf { it.items?.size ?: 0 }
        var done = 0

        for (pd in playlists) {
            pd.items?.forEach { item ->
                done++
                val percent = 20 + (done * 70.0 / maxOf(total, 1)).toInt()
                notifyProgress(callback, percent, "下载 ($done/$total): ${item.fileName}")

                val dbList = database.mediaFileDao().getByPlaylistIdSync(pd.id)
                val mfe = dbList.find { it.id == item.mediaId } ?: return@forEach

                if (mfe.isDownloaded && mfe.filePath != null && File(mfe.filePath!!).exists()) {
                    Log.d(TAG, "Already downloaded: ${item.fileName}")
                    return@forEach
                }

                val localFile = File(mediaDir, "${item.mediaId}_${item.fileName}")

                // 检查文件是否已存在且 MD5 匹配
                if (localFile.exists() && verifyMD5(localFile, item.md5Hash)) {
                    val updated = mfe.copy(filePath = localFile.absolutePath, isDownloaded = true)
                    database.mediaFileDao().insertAllSync(listOf(updated))
                    Log.d(TAG, "File verified from disk: ${item.fileName}")
                    return@forEach
                }

                try {
                    downloadFile(item.mediaId, localFile)
                    if (verifyMD5(localFile, item.md5Hash)) {
                        val updated = mfe.copy(filePath = localFile.absolutePath, isDownloaded = true)
                        database.mediaFileDao().insertAllSync(listOf(updated))
                        Log.d(TAG, "Downloaded: ${item.fileName}")
                    } else {
                        Log.e(TAG, "MD5 mismatch: ${item.fileName}")
                        localFile.delete()
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Download failed: ${item.fileName}", e)
                }
            }
        }
    }

    private suspend fun downloadMediaFilesAsync(
        playlists: List<InitResponse.PlaylistData>,
        onProgress: ((Int, String) -> Unit)?
    ) {
        val mediaDir = File(appContext.filesDir, "media").apply { mkdirs() }

        val total = playlists.sumOf { it.items?.size ?: 0 }
        var done = 0

        for (pd in playlists) {
            pd.items?.forEach { item ->
                done++
                val percent = 20 + (done * 70.0 / maxOf(total, 1)).toInt()
                withContext(Dispatchers.Main) {
                    onProgress?.invoke(percent, "下载 ($done/$total): ${item.fileName}")
                }

                val dbList = database.mediaFileDao().getByPlaylistIdSync(pd.id)
                val mfe = dbList.find { it.id == item.mediaId } ?: return@forEach

                if (mfe.isDownloaded && mfe.filePath != null && File(mfe.filePath!!).exists()) {
                    Log.d(TAG, "Already downloaded: ${item.fileName}")
                    return@forEach
                }

                val localFile = File(mediaDir, "${item.mediaId}_${item.fileName}")

                if (localFile.exists() && verifyMD5(localFile, item.md5Hash)) {
                    val updated = mfe.copy(filePath = localFile.absolutePath, isDownloaded = true)
                    database.mediaFileDao().insertAllSync(listOf(updated))
                    Log.d(TAG, "File verified from disk: ${item.fileName}")
                    return@forEach
                }

                try {
                    downloadFile(item.mediaId, localFile)
                    if (verifyMD5(localFile, item.md5Hash)) {
                        val updated = mfe.copy(filePath = localFile.absolutePath, isDownloaded = true)
                        database.mediaFileDao().insertAllSync(listOf(updated))
                        Log.d(TAG, "Downloaded: ${item.fileName}")
                    } else {
                        Log.e(TAG, "MD5 mismatch: ${item.fileName}")
                        localFile.delete()
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Download failed: ${item.fileName}", e)
                }
            }
        }
    }

    // ────────────────────────────────────────────────
    //  私有方法：生成 WebView 播放器 JSON
    // ────────────────────────────────────────────────

    /**
     * 将第一个有下载完成媒体文件的播放列表转换为 WebView 播放器所需的 JSON。
     * file_url 使用 local:/// 前缀（指向 filesDir）。
     */
    private fun buildPlayerJson(playlists: List<InitResponse.PlaylistData>): String {
        return try {
            for (pd in playlists) {
                val itemsArr = JSONArray()
                var hasDownloaded = false

                pd.items?.forEach { item ->
                    val dbList = database.mediaFileDao().getByPlaylistIdSync(pd.id)
                    val mfe = dbList.find { it.id == item.mediaId }

                    val fileUrl = if (mfe != null && mfe.isDownloaded && mfe.filePath != null) {
                        // 已下载 → 转换为 local:/// 相对路径
                        val absPath = mfe.filePath!!
                        val filesDir = appContext.filesDir.absolutePath
                        var rel = if (absPath.startsWith(filesDir)) {
                            absPath.substring(filesDir.length) // e.g. /media/5_file.mp4
                        } else {
                            absPath
                        }
                        // 去掉开头的 /
                        if (rel.startsWith("/")) rel = rel.substring(1)
                        hasDownloaded = true
                        "local:///$rel"
                    } else {
                        // 未下载成功 → 使用服务器 URL
                        item.fileUrl
                    }

                    val obj = JSONObject().apply {
                        put("id", item.id)
                        put("media_id", item.mediaId)
                        put("media_name", item.fileName)
                        put("media_type", item.fileType)
                        put("file_url", fileUrl)
                        put("display_duration", item.displayDuration)
                        put("display_order", item.displayOrder)
                    }
                    itemsArr.put(obj)
                }

                if (hasDownloaded) {
                    return JSONObject().apply {
                        put("id", pd.id)
                        put("name", pd.name)
                        put("items", itemsArr)
                    }.toString()
                }
            }

            // 没有任何已下载文件，使用服务器 URL
            val first = playlists.first()
            val arr = JSONArray()
            first.items?.forEach { item ->
                val obj = JSONObject().apply {
                    put("id", item.id)
                    put("media_id", item.mediaId)
                    put("media_name", item.fileName)
                    put("media_type", item.fileType)
                    put("file_url", item.fileUrl)
                    put("display_duration", item.displayDuration)
                    put("display_order", item.displayOrder)
                }
                arr.put(obj)
            }
            JSONObject().apply {
                put("id", first.id)
                put("name", first.name)
                put("items", arr)
            }.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to build player JSON", e)
            """{"id":0,"name":"error","items":[]}"""
        }
    }

    // ────────────────────────────────────────────────
    //  私有工具方法
    // ────────────────────────────────────────────────

    @Throws(IOException::class)
    private fun downloadFile(mediaId: Int, outputFile: File) {
        val call = apiService.downloadMedia(mediaId)
        val response = call.execute()

        if (response.isSuccessful && response.body() != null) {
            response.body()!!.byteStream().use { input ->
                FileOutputStream(outputFile).use { output ->
                    val buf = ByteArray(8192)
                    var n: Int
                    while (input.read(buf).also { n = it } != -1) {
                        output.write(buf, 0, n)
                    }
                }
            }
        } else {
            throw IOException("Download failed: ${response.code()}")
        }
    }

    private fun verifyMD5(file: File, expectedMd5: String?): Boolean {
        if (expectedMd5.isNullOrEmpty()) return true
        return try {
            val md = MessageDigest.getInstance("MD5")
            FileInputStream(file).use { fis ->
                val buf = ByteArray(4096)
                var n: Int
                while (fis.read(buf).also { n = it } != -1) {
                    md.update(buf, 0, n)
                }
            }
            val digest = md.digest()
            val sb = StringBuilder()
            for (b in digest) {
                sb.append(String.format("%02x", b))
            }
            sb.toString().equals(expectedMd5, ignoreCase = true)
        } catch (e: Exception) {
            Log.e(TAG, "MD5 error", e)
            false
        }
    }

    private fun notifyProgress(callback: SyncCallback?, percent: Int, message: String) {
        callback?.onProgress(percent, message)
    }

    // ────────────────────────────────────────────────
    //  回调接口
    // ────────────────────────────────────────────────

    /**
     * 同步回调接口
     */
    interface SyncCallback {
        /**
         * 同步成功
         * @param playlistJson 可直接注入 WebView 播放器的播放列表 JSON
         * @param schedule     设备定时开关机配置（可为 null）
         */
        fun onSyncSuccess(playlistJson: String, schedule: InitResponse.Schedule?)

        /**
         * 同步失败（网络不可用、服务器错误、未分配播放列表等）
         * @param error 错误描述或错误码："no_playlist" / "server_error:xxx" / 异常消息
         */
        fun onSyncFailed(error: String)

        /**
         * 进度回调（在后台线程调用，需 runOnUiThread 更新 UI）
         * @param percent 0–100
         * @param message 进度描述
         */
        fun onProgress(percent: Int, message: String)
    }
}
