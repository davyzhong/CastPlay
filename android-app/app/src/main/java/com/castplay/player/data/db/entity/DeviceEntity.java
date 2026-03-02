package com.castplay.player.data.db.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

/**
 * 设备信息实体
 */
@Entity(tableName = "device")
public class DeviceEntity {

    @PrimaryKey(autoGenerate = true)
    private int id;

    private String deviceId;
    private String deviceName;
    private String timezone;

    // Getters and Setters
    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public void setDeviceId(String deviceId) {
        this.deviceId = deviceId;
    }

    public String getDeviceName() {
        return deviceName;
    }

    public void setDeviceName(String deviceName) {
        this.deviceName = deviceName;
    }

    public String getTimezone() {
        return timezone;
    }

    public void setTimezone(String timezone) {
        this.timezone = timezone;
    }
}
