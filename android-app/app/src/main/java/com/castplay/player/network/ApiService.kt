package com.castplay.player.network

import com.castplay.player.data.model.InitResponse
import com.castplay.player.data.model.RegisterResponse
import com.castplay.player.data.model.StatusRequest
import com.google.gson.annotations.SerializedName
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Response
import retrofit2.http.*

/**
 * API 服务接口
 */
interface ApiService {

    /**
     * 设备注册
     */
    @POST("devices/register")
    fun registerDevice(@Body request: RegisterRequest): Call<RegisterResponse>

    /**
     * 设备注册（协程版本）
     */
    @POST("devices/register")
    suspend fun registerDeviceAsync(@Body request: RegisterRequest): Response<RegisterResponse>

    /**
     * 播放端初始化
     */
    @POST("player/init")
    fun playerInit(@Body request: InitRequest): Call<InitResponse>

    /**
     * 播放端初始化（协程版本）
     */
    @POST("player/init")
    suspend fun playerInitAsync(@Body request: InitRequest): Response<InitResponse>

    /**
     * 下载媒体文件
     */
    @GET("player/media/{id}/download")
    @Streaming
    fun downloadMedia(@Path("id") mediaId: Int): Call<ResponseBody>

    /**
     * 下载媒体文件（协程版本）
     */
    @GET("player/media/{id}/download")
    @Streaming
    suspend fun downloadMediaAsync(@Path("id") mediaId: Int): Response<ResponseBody>

    /**
     * 下载转换后的文件
     */
    @GET("player/media/{id}/converted")
    @Streaming
    fun downloadConverted(@Path("id") mediaId: Int): Call<ResponseBody>

    /**
     * 下载转换后的文件（协程版本）
     */
    @GET("player/media/{id}/converted")
    @Streaming
    suspend fun downloadConvertedAsync(@Path("id") mediaId: Int): Response<ResponseBody>

    /**
     * 上报播放状态
     */
    @POST("player/status")
    fun reportStatus(@Body request: StatusRequest): Call<Void>

    /**
     * 上报播放状态（协程版本）
     */
    @POST("player/status")
    suspend fun reportStatusAsync(@Body request: StatusRequest): Response<Unit>

    /**
     * 初始化请求
     */
    data class InitRequest(
        @SerializedName("device_id")
        val deviceId: String
    )

    /**
     * 设备注册请求
     */
    data class RegisterRequest(
        @SerializedName("device_id")
        var deviceId: String? = null,      // 已有设备 ID（首次注册不传）
        @SerializedName("hardware_id")
        var hardwareId: String? = null,    // 硬件标识（Android ID）
        @SerializedName("device_name")
        var deviceName: String? = null,    // 设备名称
        var timezone: String = "Asia/Shanghai"  // 时区
    )
}
