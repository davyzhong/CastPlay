package com.castplay.player.network;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import com.castplay.player.BuildConfig;

import org.json.JSONObject;

import java.net.URI;
import java.util.Random;

import io.socket.client.IO;
import io.socket.client.Socket;
import io.socket.emitter.Emitter;

/**
 * WebSocket 连接管理器 (Socket.IO 版本)
 *
 * 使用 Socket.IO 协议与后端 Flask-SocketIO 通信，确保协议一致性。
 *
 * 功能：
 * - Socket.IO 协议支持（自动重连、心跳）
 * - 事件驱动通信
 * - 房间加入/离开
 */
public class WebSocketManager {
    private static final String TAG = "WebSocketManager";
    private static WebSocketManager instance;

    // 重连配置
    private static final int INITIAL_RETRY_DELAY_MS = 1000;
    private static final int MAX_RETRY_DELAY_MS = 60000;
    private static final int MAX_RETRY_COUNT = 10;

    private Socket socket;
    private String deviceId;
    private WebSocketListener listener;
    private Handler mainHandler;

    // 连接状态
    private int retryCount = 0;
    private boolean isConnected = false;

    private WebSocketManager() {
        mainHandler = new Handler(Looper.getMainLooper());
    }

    public static synchronized WebSocketManager getInstance() {
        if (instance == null) {
            instance = new WebSocketManager();
        }
        return instance;
    }

    /**
     * 连接 Socket.IO 服务器
     */
    public void connect(String deviceId, WebSocketListener listener) {
        this.deviceId = deviceId;
        this.listener = listener;

        if (socket != null && socket.connected()) {
            Log.d(TAG, "Already connected");
            return;
        }

        try {
            // 构建 Socket.IO URL (移除 /socket.io/ 后缀，Socket.IO 客户端会自动添加)
            String baseUrl = BuildConfig.WS_URL
                    .replace("/socket.io/", "")
                    .replace("/socket.io", "")
                    .replace("ws://", "http://")
                    .replace("wss://", "https://");

            IO.Options options = new IO.Options();
            options.transports = new String[]{"websocket"};  // 仅使用 WebSocket 传输
            options.reconnection = true;
            options.reconnectionAttempts = MAX_RETRY_COUNT;
            options.reconnectionDelay = INITIAL_RETRY_DELAY_MS;
            options.reconnectionDelayMax = MAX_RETRY_DELAY_MS;
            options.timeout = 20000;

            socket = IO.socket(URI.create(baseUrl), options);
            setupEventListeners();
            socket.connect();

            Log.d(TAG, "Connecting to: " + baseUrl);
        } catch (Exception e) {
            Log.e(TAG, "Failed to create socket", e);
        }
    }

    /**
     * 设置事件监听器
     */
    private void setupEventListeners() {
        // 连接成功
        socket.on(Socket.EVENT_CONNECT, args -> {
            Log.d(TAG, "Socket.IO connected");
            isConnected = true;
            retryCount = 0;

            // 发送设备注册事件
            registerDevice();
        });

        // 连接断开
        socket.on(Socket.EVENT_DISCONNECT, args -> {
            Log.d(TAG, "Socket.IO disconnected");
            isConnected = false;
        });

        // 连接错误
        socket.on(Socket.EVENT_CONNECT_ERROR, args -> {
            Log.e(TAG, "Socket.IO connection error: " + (args.length > 0 ? args[0] : "unknown"));
            isConnected = false;
            retryCount++;

            if (retryCount >= MAX_RETRY_COUNT && listener != null) {
                mainHandler.post(() -> listener.onConnectionFailed());
            }
        });

        // 重连尝试
        socket.on(Socket.EVENT_RECONNECT_ATTEMPT, args -> {
            int attempt = (int) args[0];
            Log.d(TAG, "Reconnect attempt: " + attempt);
        });

        // 重连成功
        socket.on(Socket.EVENT_RECONNECT, args -> {
            Log.d(TAG, "Socket.IO reconnected");
            isConnected = true;
            retryCount = 0;
            registerDevice();
        });

        // === 业务事件 ===

        // 设备注册确认
        socket.on("registered", args -> {
            Log.d(TAG, "Device registered confirmation");
            if (listener != null) {
                mainHandler.post(() -> listener.onRegistered());
            }
        });

        // 播放列表更新
        socket.on("playlist_update", args -> {
            try {
                JSONObject data = (JSONObject) args[0];
                int playlistId = data.optInt("playlist_id");
                Log.d(TAG, "Playlist update: " + playlistId);

                if (listener != null) {
                    mainHandler.post(() -> listener.onPlaylistUpdate(playlistId));
                }
            } catch (Exception e) {
                Log.e(TAG, "Failed to handle playlist_update", e);
            }
        });

        // 定时配置更新
        socket.on("schedule_update", args -> {
            Log.d(TAG, "Schedule update");
            if (listener != null) {
                mainHandler.post(() -> listener.onScheduleUpdate());
            }
        });

        // 强制同步
        socket.on("force_sync", args -> {
            Log.d(TAG, "Force sync");
            if (listener != null) {
                mainHandler.post(() -> listener.onForceSync());
            }
        });

        // 重启命令
        socket.on("reboot", args -> {
            Log.d(TAG, "Reboot command");
            if (listener != null) {
                mainHandler.post(() -> listener.onReboot());
            }
        });

        // 心跳响应
        socket.on("heartbeat_ack", args -> {
            Log.d(TAG, "Heartbeat acknowledged");
        });
    }

    /**
     * 发送设备注册事件
     */
    private void registerDevice() {
        if (socket == null || !socket.connected()) {
            return;
        }

        try {
            JSONObject data = new JSONObject();
            data.put("device_id", deviceId);
            socket.emit("device_register", data);
            Log.d(TAG, "Sent device_register: " + deviceId);
        } catch (Exception e) {
            Log.e(TAG, "Failed to register device", e);
        }
    }

    /**
     * 发送心跳
     */
    public void sendHeartbeat() {
        if (socket == null || !socket.connected()) {
            return;
        }

        try {
            JSONObject data = new JSONObject();
            data.put("device_id", deviceId);
            socket.emit("heartbeat", data);
            Log.d(TAG, "Sent heartbeat");
        } catch (Exception e) {
            Log.e(TAG, "Failed to send heartbeat", e);
        }
    }

    /**
     * 断开连接
     */
    public void disconnect() {
        if (socket != null) {
            socket.disconnect();
            socket.off();  // 移除所有监听器
            socket = null;
        }
        isConnected = false;
        retryCount = 0;
    }

    /**
     * 是否已连接
     */
    public boolean isConnected() {
        return socket != null && socket.connected();
    }

    /**
     * WebSocket 事件监听器
     */
    public interface WebSocketListener {
        void onRegistered();

        void onPlaylistUpdate(int playlistId);

        void onScheduleUpdate();

        void onForceSync();

        void onReboot();

        /**
         * 连接失败（达到最大重试次数）
         */
        default void onConnectionFailed() {}
    }
}
