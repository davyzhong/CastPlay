package com.castplay.player.data.repository

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import com.castplay.player.data.model.RegisterResponse
import com.castplay.player.network.ApiService
import com.castplay.player.network.RegisterRequest
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 设备仓库
 *
 * 负责设备注册、状态管理等
 */
@Singleton
class DeviceRepository @Inject constructor(
    private val api: ApiService,
    @ApplicationContext private val context: Context
) {

    companion object {
        private const val TAG = "DeviceRepository"
        private const val PREFS_NAME = "CastPlayPrefs"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_HARDWARE_ID = "hardware_id"
        private const val KEY_IS_REGISTERED = "is_registered"
    }

    private val prefs: SharedPreferences by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    /**
     * 获取保存的设备 ID
     */
    fun getSavedDeviceId(): String? {
        return prefs.getString(KEY_DEVICE_ID, null)
    }

    /**
     * 检查设备是否已注册
     */
    fun isDeviceRegistered(): Boolean {
        return prefs.getBoolean(KEY_IS_REGISTERED, false)
    }

    /**
     * 注册设备
     */
    fun registerDevice(
        deviceId: String? = null,
        hardwareId: String? = null,
        deviceName: String? = null
    ): Flow<Resource<RegisterResponse>> = flow {
        emit(Resource.Loading())

        try {
            val request = RegisterRequest(
                deviceId = deviceId ?: getSavedDeviceId(),
                hardwareId = hardwareId ?: getHardwareId(),
                deviceName = deviceName
            )

            val response = api.registerDevice(request)

            if (response.isSuccessful && response.body() != null) {
                val registerResponse = response.body()!!

                // 保存设备信息
                saveDeviceInfo(
                    registerResponse.device.deviceId,
                    request.hardwareId
                )

                emit(Resource.Success(registerResponse))
            } else {
                emit(Resource.Error("Registration failed: ${response.message()}"))
            }

        } catch (e: Exception) {
            Log.e(TAG, "Error registering device", e)
            emit(Resource.Error(e.message ?: "Unknown error"))
        }
    }

    /**
     * 获取硬件 ID（Android ID）
     */
    @Suppress("HardwareIds")
    private fun getHardwareId(): String {
        val savedHardwareId = prefs.getString(KEY_HARDWARE_ID, null)
        if (savedHardwareId != null) {
            return savedHardwareId
        }

        val androidId = android.provider.Settings.Secure.getString(
            context.contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        )

        // 保存 hardware_id
        prefs.edit().putString(KEY_HARDWARE_ID, androidId).apply()

        return androidId
    }

    /**
     * 保存设备信息
     */
    private fun saveDeviceInfo(deviceId: String, hardwareId: String?) {
        prefs.edit()
            .putString(KEY_DEVICE_ID, deviceId)
            .putBoolean(KEY_IS_REGISTERED, true)
            .apply()

        if (hardwareId != null) {
            prefs.edit().putString(KEY_HARDWARE_ID, hardwareId).apply()
        }
    }

    /**
     * 清除设备信息
     */
    fun clearDeviceInfo() {
        prefs.edit()
            .remove(KEY_DEVICE_ID)
            .putBoolean(KEY_IS_REGISTERED, false)
            .apply()
    }
}
