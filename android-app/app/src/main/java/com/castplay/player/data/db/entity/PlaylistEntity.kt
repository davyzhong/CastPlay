package com.castplay.player.data.db.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 播放列表实体
 */
@Entity(tableName = "playlist")
data class PlaylistEntity(
    @PrimaryKey
    val id: Int,
    val name: String?,
    val version: String?, // 版本号，用于检查更新
    val lastUpdated: Long = 0
)
