package com.castplay.player.data.db.dao

import androidx.room.*
import com.castplay.player.data.db.entity.MediaFileEntity
import kotlinx.coroutines.flow.Flow

/**
 * 媒体文件 DAO
 */
@Dao
interface MediaFileDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(mediaFile: MediaFileEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(mediaFiles: List<MediaFileEntity>)

    @Update
    suspend fun update(mediaFile: MediaFileEntity)

    @Delete
    suspend fun delete(mediaFile: MediaFileEntity)

    @Query("SELECT * FROM media_file WHERE playlistId = :playlistId ORDER BY displayOrder ASC")
    suspend fun getByPlaylistId(playlistId: Int): List<MediaFileEntity>

    @Query("SELECT * FROM media_file WHERE isDownloaded = 0")
    suspend fun getPendingDownloads(): List<MediaFileEntity>

    @Query("SELECT DISTINCT playlistId FROM media_file ORDER BY playlistId ASC")
    suspend fun getAllPlaylistIds(): List<Int>

    @Query("DELETE FROM media_file WHERE playlistId NOT IN (:activePlaylistIds)")
    suspend fun deleteInactivePlaylists(activePlaylistIds: List<Int>)

    @Query("DELETE FROM media_file")
    suspend fun deleteAll()

    // Flow 观察数据变化
    @Query("SELECT * FROM media_file WHERE playlistId = :playlistId ORDER BY displayOrder ASC")
    fun observeByPlaylistId(playlistId: Int): Flow<List<MediaFileEntity>>

    // 同步方法（用于兼容旧代码）
    @Query("SELECT * FROM media_file WHERE playlistId = :playlistId ORDER BY displayOrder ASC")
    fun getByPlaylistIdSync(playlistId: Int): List<MediaFileEntity>

    @Query("SELECT * FROM media_file WHERE isDownloaded = 0")
    fun getPendingDownloadsSync(): List<MediaFileEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    fun insertAllSync(mediaFiles: List<MediaFileEntity>)

    @Query("DELETE FROM media_file WHERE playlistId NOT IN (:activePlaylistIds)")
    fun deleteInactivePlaylistsSync(activePlaylistIds: List<Int>)

    @Query("DELETE FROM media_file")
    fun deleteAllSync()
}
