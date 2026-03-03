package com.castplay.player.data.db.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 设备信息实体
 */
@Entity(tableName = "device")
data class DeviceEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val deviceId: String?,
    val deviceName: String?,
    val timezone: String?
)
