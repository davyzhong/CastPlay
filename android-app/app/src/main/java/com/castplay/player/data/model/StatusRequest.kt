package com.castplay.player.data.model

import com.google.gson.annotations.SerializedName

/**
 * 状态上报请求模型
 */
data class StatusRequest(
    @SerializedName("device_id")
    val deviceId: String,
    val status: String
)
