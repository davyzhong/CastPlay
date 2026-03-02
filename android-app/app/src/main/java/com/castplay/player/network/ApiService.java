package com.castplay.player.network;

import com.castplay.player.data.model.InitResponse;
import com.castplay.player.data.model.StatusRequest;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.*;

/**
 * API 服务接口
 */
public interface ApiService {

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
}
