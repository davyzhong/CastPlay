package com.castplay.player.network

import android.os.Handler
import android.os.Looper
import android.util.Log
import com.castplay.player.BuildConfig
import io.socket.client.IO
import io.socket.client.Socket
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONObject
import java.net.URI

/**
 * WebSocket 连接管理器 (Socket.IO 版本)
 *
 * 使用 Socket.IO 协议与后端 Flask-SocketIO 通信，确保协议一致性。
 *
 * 功能：
 * - Socket.IO 协议支持（自动重连、心跳）
 * - 事件驱动通信
 * - Flow 支持响应式编程
 * - 房间加入/离开
 */
object WebSocketManager {
    private const val TAG = "WebSocketManager"

    // 重连配置
    private const val INITIAL_RETRY_DELAY_MS = 1000L
    private const val MAX_RETRY_DELAY_MS = 60000L
    private const val MAX_RETRY_COUNT = 10

    private var socket: Socket? = null
    private var deviceId: String? = null
    private var listener: WebSocketListener? = null
    private val mainHandler = Handler(Looper.getMainLooper())

    // 连接状态
    private var retryCount = 0

    // Flow 状态
    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _events = MutableSharedFlow<WebSocketEvent>(extraBufferCapacity = 16)
    val events: SharedFlow<WebSocketEvent> = _events.asSharedFlow()

    /**
     * 连接状态
     */
    sealed class ConnectionState {
        object Connected : ConnectionState()
        object Disconnected : ConnectionState()
        object Connecting : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }

    /**
     * WebSocket 事件
     */
    sealed class WebSocketEvent {
        object Registered : WebSocketEvent()
        data class PlaylistUpdate(val playlistId: Int) : WebSocketEvent()
        object ScheduleUpdate : WebSocketEvent()
        object ForceSync : WebSocketEvent()
        object Reboot : WebSocketEvent()
        object ConnectionFailed : WebSocketEvent()
    }

    /**
     * 连接 Socket.IO 服务器
     */
    fun connect(deviceId: String, listener: WebSocketListener? = null) {
        this.deviceId = deviceId
        this.listener = listener

        socket?.let {
            if (it.connected()) {
                Log.d(TAG, "Already connected")
                return
            }
        }

        try {
            _connectionState.value = ConnectionState.Connecting

            // 构建 Socket.IO URL (移除 /socket.io/ 后缀，Socket.IO 客户端会自动添加)
            val baseUrl = BuildConfig.WS_URL
                .replace("/socket.io/", "")
                .replace("/socket.io", "")
                .replace("ws://", "http://")
                .replace("wss://", "https://")

            val options = IO.Options().apply {
                transports = arrayOf("websocket")  // 仅使用 WebSocket 传输
                reconnection = true
                reconnectionAttempts = MAX_RETRY_COUNT
                reconnectionDelay = INITIAL_RETRY_DELAY_MS
                reconnectionDelayMax = MAX_RETRY_DELAY_MS
                timeout = 20000
            }

            socket = IO.socket(URI.create(baseUrl), options).also { s ->
                setupEventListeners(s)
                s.connect()
            }

            Log.d(TAG, "Connecting to: $baseUrl")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create socket", e)
            _connectionState.value = ConnectionState.Error(e.message ?: "Unknown error")
        }
    }

    /**
     * 设置事件监听器
     */
    private fun setupEventListeners(socket: Socket) {
        // 连接成功
        socket.on(Socket.EVENT_CONNECT) {
            Log.d(TAG, "Socket.IO connected")
            _connectionState.value = ConnectionState.Connected
            retryCount = 0

            // 发送设备注册事件
            registerDevice()
        }

        // 连接断开
        socket.on(Socket.EVENT_DISCONNECT) {
            Log.d(TAG, "Socket.IO disconnected")
            _connectionState.value = ConnectionState.Disconnected
        }

        // 连接错误
        socket.on(Socket.EVENT_CONNECT_ERROR) { args ->
            val errorMsg = if (args.isNotEmpty()) args[0].toString() else "unknown"
            Log.e(TAG, "Socket.IO connection error: $errorMsg")
            _connectionState.value = ConnectionState.Error(errorMsg)
            retryCount++

            if (retryCount >= MAX_RETRY_COUNT) {
                listener?.let { mainHandler.post { it.onConnectionFailed() } }
                _events.tryEmit(WebSocketEvent.ConnectionFailed)
            }
        }

        // 重连尝试
        socket.on(Socket.EVENT_RECONNECT_ATTEMPT) { args ->
            val attempt = args[0] as? Int ?: 0
            Log.d(TAG, "Reconnect attempt: $attempt")
        }

        // 重连成功
        socket.on(Socket.EVENT_RECONNECT) {
            Log.d(TAG, "Socket.IO reconnected")
            _connectionState.value = ConnectionState.Connected
            retryCount = 0
            registerDevice()
        }

        // === 业务事件 ===

        // 设备注册确认
        socket.on("registered") {
            Log.d(TAG, "Device registered confirmation")
            listener?.let { mainHandler.post { it.onRegistered() } }
            _events.tryEmit(WebSocketEvent.Registered)
        }

        // 播放列表更新
        socket.on("playlist_update") { args ->
            try {
                val data = args[0] as JSONObject
                val playlistId = data.optInt("playlist_id")
                Log.d(TAG, "Playlist update: $playlistId")

                listener?.let { mainHandler.post { it.onPlaylistUpdate(playlistId) } }
                _events.tryEmit(WebSocketEvent.PlaylistUpdate(playlistId))
            } catch (e: Exception) {
                Log.e(TAG, "Failed to handle playlist_update", e)
            }
        }

        // 定时配置更新
        socket.on("schedule_update") {
            Log.d(TAG, "Schedule update")
            listener?.let { mainHandler.post { it.onScheduleUpdate() } }
            _events.tryEmit(WebSocketEvent.ScheduleUpdate)
        }

        // 强制同步
        socket.on("force_sync") {
            Log.d(TAG, "Force sync")
            listener?.let { mainHandler.post { it.onForceSync() } }
            _events.tryEmit(WebSocketEvent.ForceSync)
        }

        // 重启命令
        socket.on("reboot") {
            Log.d(TAG, "Reboot command")
            listener?.let { mainHandler.post { it.onReboot() } }
            _events.tryEmit(WebSocketEvent.Reboot)
        }

        // 心跳响应
        socket.on("heartbeat_ack") {
            Log.d(TAG, "Heartbeat acknowledged")
        }
    }

    /**
     * 发送设备注册事件
     */
    private fun registerDevice() {
        val s = socket ?: return
        if (!s.connected()) return

        try {
            val data = JSONObject().apply {
                put("device_id", deviceId)
            }
            s.emit("device_register", data)
            Log.d(TAG, "Sent device_register: $deviceId")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to register device", e)
        }
    }

    /**
     * 发送心跳
     */
    fun sendHeartbeat() {
        val s = socket ?: return
        if (!s.connected()) return

        try {
            val data = JSONObject().apply {
                put("device_id", deviceId)
            }
            s.emit("heartbeat", data)
            Log.d(TAG, "Sent heartbeat")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to send heartbeat", e)
        }
    }

    /**
     * 断开连接
     */
    fun disconnect() {
        socket?.apply {
            disconnect()
            off()  // 移除所有监听器
        }
        socket = null
        _connectionState.value = ConnectionState.Disconnected
        retryCount = 0
    }

    /**
     * 是否已连接
     */
    fun isConnected(): Boolean = socket?.connected() == true

    /**
     * WebSocket 事件监听器（兼容旧代码）
     */
    interface WebSocketListener {
        fun onRegistered()
        fun onPlaylistUpdate(playlistId: Int)
        fun onScheduleUpdate()
        fun onForceSync()
        fun onReboot()

        /**
         * 连接失败（达到最大重试次数）
         */
        fun onConnectionFailed() {}
    }
}
