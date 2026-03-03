package com.castplay.player.network;

import com.castplay.player.data.model.InitResponse;
import com.castplay.player.data.model.RegisterResponse;
import com.castplay.player.data.model.StatusRequest;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.*;

/**
 * API 服务接口
 */
public interface ApiService {

    /**
     * 设备注册
     */
    @POST("devices/register")
    Call<RegisterResponse> registerDevice(@Body RegisterRequest request);

    /**
     * 播放端初始化
     */
    @POST("player/init")
    Call<InitResponse> playerInit(@Body InitRequest request);

    /**
     * 下载媒体文件
     */
    @GET("player/media/{id}/download")
    @Streaming
    Call<ResponseBody> downloadMedia(@Path("id") int mediaId);

    /**
     * 下载转换后的文件
     */
    @GET("player/media/{id}/converted")
    @Streaming
    Call<ResponseBody> downloadConverted(@Path("id") int mediaId);

    /**
     * 上报播放状态
     */
    @POST("player/status")
    Call<Void> reportStatus(@Body StatusRequest request);

    /**
     * 初始化请求
     */
    class InitRequest {
        private String device_id;

        public InitRequest(String deviceId) {
            this.device_id = deviceId;
        }

        public String getDeviceId() {
            return device_id;
        }
    }

    /**
     * 设备注册请求
     */
    class RegisterRequest {
        private String device_id;     // 已有设备 ID（首次注册不传）
        private String hardware_id;   // 硬件标识（Android ID）
        private String device_name;   // 设备名称
        private String timezone;      // 时区

        public RegisterRequest() {
            this.timezone = "Asia/Shanghai";
        }

        public void setDeviceId(String deviceId) {
            this.device_id = deviceId;
        }

        public void setHardwareId(String hardwareId) {
            this.hardware_id = hardwareId;
        }

        public void setDeviceName(String deviceName) {
            this.device_name = deviceName;
        }

        public void setTimezone(String timezone) {
            this.timezone = timezone;
        }
    }
}
