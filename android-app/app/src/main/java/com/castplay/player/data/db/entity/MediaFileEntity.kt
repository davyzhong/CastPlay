package com.castplay.player.data.db.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 媒体文件实体
 *
 * 版本历史:
 * - v1: 初始版本
 * - v2: 添加 playbackSpeed 字段
 * - v3: 添加 lastPlayedAt 字段
 */
@Entity(tableName = "media_file")
data class MediaFileEntity(
    @PrimaryKey
    val id: Int,
    val playlistId: Int,
    val fileName: String?,
    val fileType: String?, // image/video/ppt
    val filePath: String?, // 本地文件路径
    val fileUrl: String?, // 服务器下载URL
    val displayOrder: Int = 0,
    val displayDuration: Int = 5,
    val fileSize: Long = 0,
    val md5Hash: String? = null,
    val isDownloaded: Boolean = false,

    // v2 新增: 播放速度
    @ColumnInfo(name = "playback_speed", defaultValue = "1.0")
    val playbackSpeed: Float = 1.0f,

    // v3 新增: 最后播放时间
    @ColumnInfo(name = "last_played_at", defaultValue = "0")
    val lastPlayedAt: Long = 0
)
