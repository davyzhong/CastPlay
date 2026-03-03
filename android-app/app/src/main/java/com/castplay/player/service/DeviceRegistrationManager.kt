package com.castplay.player.service

import android.annotation.SuppressLint
import android.content.Context
import android.content.SharedPreferences
import android.os.Build
import android.provider.Settings
import android.util.Log
import com.castplay.player.data.model.RegisterResponse
import com.castplay.player.network.ApiService
import com.castplay.player.network.RetrofitClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * 设备注册管理器
 *
 * 职责：
 *  1. 首次启动时向服务器注册设备，获取唯一设备 ID
 *  2. 使用 hardware_id (Android ID) 确保同一设备重装后能恢复原 ID
 *  3. 缓存设备 ID 到 SharedPreferences
 */
class DeviceRegistrationManager(context: Context) {

    companion object {
        private const val TAG = "DeviceRegistration"
        private const val PREFS_NAME = "CastPlayPrefs"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_SERVER_ID = "server_device_id"  // 服务器分配的数字 ID
    }

    private val appContext: Context = context.applicationContext
    private val prefs: SharedPreferences = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val apiService: ApiService = RetrofitClient.getApiService()

    /**
     * 获取已注册的设备 ID（本地缓存）
     *
     * @return 设备 ID，未注册返回 null
     */
    fun getCachedDeviceId(): String? = prefs.getString(KEY_DEVICE_ID, null)

    /**
     * 获取服务器分配的数字 ID
     */
    fun getServerDeviceId(): Int = prefs.getInt(KEY_SERVER_ID, -1)

    /**
     * 是否已完成首次注册
     */
    fun isRegistered(): Boolean = getCachedDeviceId() != null

    /**
     * 执行设备注册（回调版本，兼容旧代码）
     *
     * @param callback 注册回调
     */
    fun register(callback: RegistrationCallback?) {
        val cachedId = getCachedDeviceId()
        val hardwareId = getHardwareId()

        Log.d(TAG, "Starting registration, cachedId=$cachedId, hardwareId=$hardwareId")

        val request = ApiService.RegisterRequest(
            deviceId = cachedId,
            hardwareId = hardwareId,
            deviceName = getDeviceName()
        )

        apiService.registerDevice(request).enqueue(object : Callback<RegisterResponse> {
            override fun onResponse(call: Call<RegisterResponse>, response: Response<RegisterResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val resp = response.body()!!
                    val device = resp.device

                    if (device != null) {
                        // 保存设备 ID
                        val deviceId = device.deviceId
                        prefs.edit()
                            .putString(KEY_DEVICE_ID, deviceId)
                            .putInt(KEY_SERVER_ID, device.id)
                            .apply()

                        Log.i(TAG, "Registration success: $deviceId (new=${resp.isNew})")
                        callback?.onRegistrationSuccess(deviceId ?: "", resp.isNew)
                    } else {
                        callback?.onRegistrationFailed("Device info is null")
                    }
                } else {
                    val error = "Server error: ${response.code()}"
                    Log.e(TAG, "Registration failed: $error")
                    callback?.onRegistrationFailed(error)
                }
            }

            override fun onFailure(call: Call<RegisterResponse>, t: Throwable) {
                Log.e(TAG, "Registration network error", t)
                callback?.onRegistrationFailed(t.message ?: "Unknown error")
            }
        })
    }

    /**
     * 执行设备注册（协程版本）
     */
    suspend fun registerAsync(): Result<Pair<String, Boolean>> = withContext(Dispatchers.IO) {
        try {
            val cachedId = getCachedDeviceId()
            val hardwareId = getHardwareId()

            Log.d(TAG, "Starting registration (async), cachedId=$cachedId, hardwareId=$hardwareId")

            val request = ApiService.RegisterRequest(
                deviceId = cachedId,
                hardwareId = hardwareId,
                deviceName = getDeviceName()
            )

            val response = apiService.registerDeviceAsync(request)

            if (response.isSuccessful && response.body() != null) {
                val resp = response.body()!!
                val device = resp.device

                if (device != null) {
                    // 保存设备 ID
                    val deviceId = device.deviceId ?: ""
                    prefs.edit()
                        .putString(KEY_DEVICE_ID, deviceId)
                        .putInt(KEY_SERVER_ID, device.id)
                        .apply()

                    Log.i(TAG, "Registration success (async): $deviceId (new=${resp.isNew})")
                    Result.success(Pair(deviceId, resp.isNew))
                } else {
                    Result.failure(Exception("Device info is null"))
                }
            } else {
                Result.failure(Exception("Server error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Registration error (async)", e)
            Result.failure(e)
        }
    }

    /**
     * 获取设备硬件 ID (Android ID)
     */
    @SuppressLint("HardwareIds")
    private fun getHardwareId(): String {
        return Settings.Secure.getString(
            appContext.contentResolver,
            Settings.Secure.ANDROID_ID
        )
    }

    /**
     * 生成设备名称
     */
    private fun getDeviceName(): String {
        val manufacturer = Build.MANUFACTURER
        val model = Build.MODEL
        return if (model.startsWith(manufacturer)) {
            model.capitalize()
        } else {
            "${manufacturer.capitalize()} $model"
        }
    }

    private fun String.capitalize(): String {
        return if (isEmpty()) this else this[0].uppercaseChar() + substring(1)
    }

    /**
     * 注册回调接口
     */
    interface RegistrationCallback {
        /**
         * 注册成功
         *
         * @param deviceId 服务器分配的设备 ID（如 CAS-A1B2）
         * @param isNew 是否为新注册（false 表示恢复已有设备）
         */
        fun onRegistrationSuccess(deviceId: String, isNew: Boolean)

        /**
         * 注册失败
         *
         * @param error 错误信息
         */
        fun onRegistrationFailed(error: String)
    }
}
