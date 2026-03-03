package com.castplay.player.service;

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.provider.Settings;
import android.util.Log;

import com.castplay.player.data.model.RegisterResponse;
import com.castplay.player.network.ApiService;
import com.castplay.player.network.RetrofitClient;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 设备注册管理器
 *
 * 职责：
 *  1. 首次启动时向服务器注册设备，获取唯一设备 ID
 *  2. 使用 hardware_id (Android ID) 确保同一设备重装后能恢复原 ID
 *  3. 缓存设备 ID 到 SharedPreferences
 */
public class DeviceRegistrationManager {

    private static final String TAG = "DeviceRegistration";
    private static final String PREFS_NAME = "CastPlayPrefs";
    private static final String KEY_DEVICE_ID = "device_id";
    private static final String KEY_SERVER_ID = "server_device_id";  // 服务器分配的数字 ID

    private final Context context;
    private final SharedPreferences prefs;
    private final ApiService apiService;

    public DeviceRegistrationManager(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.apiService = RetrofitClient.getInstance().getApiService();
    }

    /**
     * 获取已注册的设备 ID（本地缓存）
     *
     * @return 设备 ID，未注册返回 null
     */
    public String getCachedDeviceId() {
        return prefs.getString(KEY_DEVICE_ID, null);
    }

    /**
     * 获取服务器分配的数字 ID
     */
    public int getServerDeviceId() {
        return prefs.getInt(KEY_SERVER_ID, -1);
    }

    /**
     * 是否已完成首次注册
     */
    public boolean isRegistered() {
        return getCachedDeviceId() != null;
    }

    /**
     * 执行设备注册
     *
     * @param callback 注册回调
     */
    public void register(RegistrationCallback callback) {
        String cachedId = getCachedDeviceId();
        String hardwareId = getHardwareId();

        Log.d(TAG, "Starting registration, cachedId=" + cachedId + ", hardwareId=" + hardwareId);

        ApiService.RegisterRequest request = new ApiService.RegisterRequest();
        request.setHardwareId(hardwareId);
        request.setDeviceName(getDeviceName());

        // 如果有缓存的 ID，带上以便服务器识别
        if (cachedId != null) {
            request.setDeviceId(cachedId);
        }

        apiService.registerDevice(request).enqueue(new Callback<RegisterResponse>() {
            @Override
            public void onResponse(Call<RegisterResponse> call, Response<RegisterResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    RegisterResponse resp = response.body();
                    RegisterResponse.DeviceInfo device = resp.getDevice();

                    // 保存设备 ID
                    String deviceId = device.getDeviceId();
                    prefs.edit()
                        .putString(KEY_DEVICE_ID, deviceId)
                        .putInt(KEY_SERVER_ID, device.getId())
                        .apply();

                    Log.i(TAG, "Registration success: " + deviceId + " (new=" + resp.isNew() + ")");

                    if (callback != null) {
                        callback.onRegistrationSuccess(deviceId, resp.isNew());
                    }
                } else {
                    String error = "Server error: " + response.code();
                    Log.e(TAG, "Registration failed: " + error);
                    if (callback != null) {
                        callback.onRegistrationFailed(error);
                    }
                }
            }

            @Override
            public void onFailure(Call<RegisterResponse> call, Throwable t) {
                Log.e(TAG, "Registration network error", t);
                if (callback != null) {
                    callback.onRegistrationFailed(t.getMessage());
                }
            }
        });
    }

    /**
     * 获取设备硬件 ID (Android ID)
     */
    @SuppressLint("HardwareIds")
    private String getHardwareId() {
        return Settings.Secure.getString(
            context.getContentResolver(),
            Settings.Secure.ANDROID_ID
        );
    }

    /**
     * 生成设备名称
     */
    private String getDeviceName() {
        String manufacturer = Build.MANUFACTURER;
        String model = Build.MODEL;
        if (model.startsWith(manufacturer)) {
            return capitalize(model);
        }
        return capitalize(manufacturer) + " " + model;
    }

    private String capitalize(String str) {
        if (str == null || str.isEmpty()) return str;
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }

    /**
     * 注册回调接口
     */
    public interface RegistrationCallback {
        /**
         * 注册成功
         *
         * @param deviceId 服务器分配的设备 ID（如 CAS-A1B2）
         * @param isNew 是否为新注册（false 表示恢复已有设备）
         */
        void onRegistrationSuccess(String deviceId, boolean isNew);

        /**
         * 注册失败
         *
         * @param error 错误信息
         */
        void onRegistrationFailed(String error);
    }
}
