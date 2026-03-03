package com.castplay.player.data.model

import com.google.gson.annotations.SerializedName

/**
 * 设备注册响应
 */
data class RegisterResponse(
    val message: String?,
    val device: DeviceInfo?,
    @SerializedName("is_new")
    val isNew: Boolean = false
) {
    /**
     * 设备信息
     */
    data class DeviceInfo(
        val id: Int,
        @SerializedName("device_id")
        val deviceId: String?,
        @SerializedName("device_name")
        val deviceName: String?,
        @SerializedName("hardware_id")
        val hardwareId: String?,
        val timezone: String?,
        val status: String?,
        @SerializedName("last_online")
        val lastOnline: String?
    )
}
