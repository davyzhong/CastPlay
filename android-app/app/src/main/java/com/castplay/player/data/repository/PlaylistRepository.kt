package com.castplay.player.data.repository

import android.util.Log
import com.castplay.player.data.db.dao.PlaylistDao
import com.castplay.player.data.db.entity.PlaylistEntity
import com.castplay.player.data.db.entity.PlaylistItemEntity
import com.castplay.player.network.ApiService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 播放列表仓库
 *
 * 负责播放列表的数据获取和缓存
 * 实现 Repository 模式，统一数据来源
 */
@Singleton
class PlaylistRepository @Inject constructor(
    private val api: ApiService,
    private val playlistDao: PlaylistDao
) {

    companion object {
        private const val TAG = "PlaylistRepository"
    }

    /**
     * 获取所有播放列表
     */
    fun getPlaylists(): Flow<Resource<List<PlaylistEntity>>> = flow {
        emit(Resource.Loading())

        try {
            // 返回本地缓存
            val cached = playlistDao.getAllPlaylists()
            emit(Resource.Success(cached))

        } catch (e: Exception) {
            Log.e(TAG, "Error getting playlists", e)
            emit(Resource.Error(e.message ?: "Unknown error"))
        }
    }

    /**
     * 根据 ID 获取播放列表
     */
    suspend fun getPlaylistById(id: Long): PlaylistEntity? {
        return playlistDao.getPlaylistById(id)
    }

    /**
     * 获取播放列表的所有项目
     */
    suspend fun getPlaylistItems(playlistId: Long): List<PlaylistItemEntity> {
        return playlistDao.getPlaylistItems(playlistId)
    }

    /**
     * 保存播放列表
     */
    suspend fun savePlaylist(playlist: PlaylistEntity) {
        playlistDao.insertPlaylist(playlist)
    }

    /**
     * 保存播放列表项目
     */
    suspend fun savePlaylistItems(items: List<PlaylistItemEntity>) {
        playlistDao.insertPlaylistItems(items)
    }

    /**
     * 删除播放列表
     */
    suspend fun deletePlaylist(playlist: PlaylistEntity) {
        playlistDao.deletePlaylist(playlist)
    }

    /**
     * 清空播放列表的所有项目
     */
    suspend fun clearPlaylistItems(playlistId: Long) {
        playlistDao.deletePlaylistItems(playlistId)
    }

    /**
     * 清空所有播放列表
     */
    suspend fun clearAll() {
        playlistDao.deleteAllPlaylists()
    }
}
