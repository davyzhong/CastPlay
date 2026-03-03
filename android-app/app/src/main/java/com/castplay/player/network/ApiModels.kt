package com.castplay.player.network

import com.google.gson.annotations.SerializedName

/**
 * 设备注册请求
 */
data class RegisterRequest(
    @SerializedName("device_id")
    val deviceId: String? = null,

    @SerializedName("hardware_id")
    val hardwareId: String? = null,

    @SerializedName("device_name")
    val deviceName: String? = null,

    val timezone: String = "Asia/Shanghai"
)

/**
 * 播放器初始化请求
 */
data class InitRequest(
    @SerializedName("device_id")
    val deviceId: String
)

/**
 * 状态上报请求
 */
data class StatusRequest(
    @SerializedName("device_id")
    val deviceId: String,

    val status: String = "online",

    @SerializedName("current_playlist_id")
    val currentPlaylistId: Int? = null,

    @SerializedName("current_media_id")
    val currentMediaId: Int? = null
)
