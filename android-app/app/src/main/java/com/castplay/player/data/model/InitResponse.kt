package com.castplay.player.data.model

import com.google.gson.annotations.SerializedName

/**
 * 初始化响应模型
 */
data class InitResponse(
    val device: Device?,
    val playlists: List<PlaylistData>?,
    val schedule: Schedule?,
    @SerializedName("websocket_url")
    val websocketUrl: String?
) {
    data class Device(
        val id: Int,
        @SerializedName("device_id")
        val deviceId: String?,
        @SerializedName("device_name")
        val deviceName: String?,
        val timezone: String?
    )

    data class PlaylistData(
        val id: Int,
        val name: String?,
        val version: String?,
        val items: List<PlaylistItemData>?
    )

    data class PlaylistItemData(
        val id: Int,
        @SerializedName("media_id")
        val mediaId: Int,
        @SerializedName("file_name")
        val fileName: String?,
        @SerializedName("file_type")
        val fileType: String?,
        @SerializedName("file_url")
        val fileUrl: String?,
        @SerializedName("display_order")
        val displayOrder: Int = 0,
        @SerializedName("display_duration")
        val displayDuration: Int = 5,
        @SerializedName("file_size")
        val fileSize: Long = 0,
        @SerializedName("md5_hash")
        val md5Hash: String?
    )

    data class Schedule(
        @SerializedName("power_on_time")
        val powerOnTime: String?,
        @SerializedName("power_off_time")
        val powerOffTime: String?,
        val weekdays: List<Int>?,
        val timezone: String?
    )
}
