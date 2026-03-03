package com.castplay.player.data.db.dao

import androidx.room.*
import com.castplay.player.data.db.entity.PlaylistEntity
import kotlinx.coroutines.flow.Flow

/**
 * 播放列表 DAO
 */
@Dao
interface PlaylistDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(playlist: PlaylistEntity)

    @Update
    suspend fun update(playlist: PlaylistEntity)

    @Delete
    suspend fun delete(playlist: PlaylistEntity)

    @Query("SELECT * FROM playlist")
    suspend fun getAll(): List<PlaylistEntity>

    @Query("SELECT * FROM playlist WHERE id = :id")
    suspend fun getById(id: Int): PlaylistEntity?

    @Query("DELETE FROM playlist")
    suspend fun deleteAll()

    // Flow 观察数据变化
    @Query("SELECT * FROM playlist")
    fun observeAll(): Flow<List<PlaylistEntity>>

    // 同步方法（用于兼容旧代码）
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    fun insertSync(playlist: PlaylistEntity)

    @Query("SELECT * FROM playlist")
    fun getAllSync(): List<PlaylistEntity>

    @Query("SELECT * FROM playlist WHERE id = :id")
    fun getByIdSync(id: Int): PlaylistEntity?
}
