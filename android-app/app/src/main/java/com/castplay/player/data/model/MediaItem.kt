package com.castplay.player.data.model

/**
 * 媒体项模型
 */
data class MediaItem(
    val id: Int,
    val fileName: String,
    val fileType: String,
    val filePath: String,
    val displayDuration: Int
)
