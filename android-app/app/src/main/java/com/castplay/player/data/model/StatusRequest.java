package com.castplay.player.data.model;

import com.google.gson.annotations.SerializedName;

/**
 * 状态上报请求模型
 */
public class StatusRequest {

    @SerializedName("device_id")
    private String deviceId;

    private String status;

    public StatusRequest(String deviceId, String status) {
        this.deviceId = deviceId;
        this.status = status;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public String getStatus() {
        return status;
    }
}
