package com.castplay.player.data.model;

import com.google.gson.annotations.SerializedName;

/**
 * 设备注册响应
 */
public class RegisterResponse {

    private String message;
    private DeviceInfo device;

    @SerializedName("is_new")
    private boolean isNew;

    public String getMessage() {
        return message;
    }

    public DeviceInfo getDevice() {
        return device;
    }

    public boolean isNew() {
        return isNew;
    }

    /**
     * 设备信息
     */
    public static class DeviceInfo {
        private int id;

        @SerializedName("device_id")
        private String deviceId;

        @SerializedName("device_name")
        private String deviceName;

        @SerializedName("hardware_id")
        private String hardwareId;

        private String timezone;
        private String status;

        @SerializedName("last_online")
        private String lastOnline;

        public int getId() {
            return id;
        }

        public String getDeviceId() {
            return deviceId;
        }

        public String getDeviceName() {
            return deviceName;
        }

        public String getHardwareId() {
            return hardwareId;
        }

        public String getTimezone() {
            return timezone;
        }

        public String getStatus() {
            return status;
        }

        public String getLastOnline() {
            return lastOnline;
        }
    }
}
