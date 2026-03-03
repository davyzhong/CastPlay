package com.castplay.player.data.repository

import android.util.Log
import com.castplay.player.data.db.dao.MediaFileDao
import com.castplay.player.data.db.entity.MediaFileEntity
import com.castplay.player.network.ApiService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 媒体文件仓库
 *
 * 负责媒体文件的数据获取和缓存
 * 实现 Repository 模式，统一数据来源
 */
@Singleton
class MediaRepository @Inject constructor(
    private val api: ApiService,
    private val mediaFileDao: MediaFileDao
) {

    companion object {
        private const val TAG = "MediaRepository"
    }

    /**
     * 获取所有媒体文件
     *
     * 策略：先返回本地缓存，然后从网络更新
     */
    fun getMediaFiles(): Flow<Resource<List<MediaFileEntity>>> = flow {
        emit(Resource.Loading())

        try {
            // 先返回本地缓存
            val cached = mediaFileDao.getAllMediaFiles()
            if (cached.isNotEmpty()) {
                emit(Resource.Success(cached))
            }

            // TODO: 从网络获取媒体列表并更新本地缓存
            // 目前媒体文件是通过播放列表同步的

        } catch (e: Exception) {
            Log.e(TAG, "Error getting media files", e)
            emit(Resource.Error(e.message ?: "Unknown error"))
        }
    }

    /**
     * 根据 ID 获取媒体文件
     */
    suspend fun getMediaFileById(id: Long): MediaFileEntity? {
        return mediaFileDao.getMediaFileById(id)
    }

    /**
     * 保存媒体文件到本地缓存
     */
    suspend fun saveMediaFile(mediaFile: MediaFileEntity) {
        mediaFileDao.insertMediaFile(mediaFile)
    }

    /**
     * 批量保存媒体文件
     */
    suspend fun saveMediaFiles(mediaFiles: List<MediaFileEntity>) {
        mediaFileDao.insertMediaFiles(mediaFiles)
    }

    /**
     * 删除媒体文件
     */
    suspend fun deleteMediaFile(mediaFile: MediaFileEntity) {
        mediaFileDao.deleteMediaFile(mediaFile)
    }

    /**
     * 清空所有媒体文件缓存
     */
    suspend fun clearAll() {
        mediaFileDao.deleteAllMediaFiles()
    }
}
