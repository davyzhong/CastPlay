package com.castplay.player.network;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import com.castplay.player.BuildConfig;

import okhttp3.*;
import org.json.JSONObject;

import java.util.Random;

/**
 * WebSocket 连接管理器
 *
 * 功能：
 * - 自动重连（指数退避）
 * - 心跳保活
 * - 连接状态管理
 */
public class WebSocketManager {
    private static final String TAG = "WebSocketManager";
    private static WebSocketManager instance;

    // 重连配置
    private static final int INITIAL_RETRY_DELAY_MS = 1000;  // 初始重连延迟 1秒
    private static final int MAX_RETRY_DELAY_MS = 60000;     // 最大重连延迟 60秒
    private static final int MAX_RETRY_COUNT = 10;           // 最大重试次数
    private static final double JITTER_FACTOR = 0.3;         // 随机抖动因子 30%

    private OkHttpClient client;
    private WebSocket webSocket;
    private String deviceId;
    private WebSocketListener listener;
    private Handler mainHandler;
    private Random random;

    // 连接状态
    private int retryCount = 0;
    private int currentRetryDelay = INITIAL_RETRY_DELAY_MS;
    private boolean isConnecting = false;
    private boolean shouldReconnect = true;  // 是否应该重连

    private WebSocketManager() {
        client = new OkHttpClient.Builder()
                .retryOnConnectionFailure(true)
                .build();
        mainHandler = new Handler(Looper.getMainLooper());
        random = new Random();
    }

    public static synchronized WebSocketManager getInstance() {
        if (instance == null) {
            instance = new WebSocketManager();
        }
        return instance;
    }

    /**
     * 连接 WebSocket
     */
    public void connect(String deviceId, WebSocketListener listener) {
        if (isConnecting) {
            Log.d(TAG, "Already connecting, skip");
            return;
        }

        this.deviceId = deviceId;
        this.listener = listener;
        this.shouldReconnect = true;
        this.isConnecting = true;

        Request request = new Request.Builder()
                .url(BuildConfig.WS_URL)
                .build();

        webSocket = client.newWebSocket(request, new okhttp3.WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                Log.d(TAG, "WebSocket connected");
                isConnecting = false;

                // 连接成功，重置重试计数器
                resetRetryState();

                // 发送设备注册消息
                try {
                    JSONObject register = new JSONObject();
                    register.put("device_id", deviceId);
                    webSocket.send(register.toString());
                } catch (Exception e) {
                    Log.e(TAG, "Failed to send register", e);
                }
            }

            @Override
            public void onMessage(WebSocket webSocket, String text) {
                Log.d(TAG, "Received message: " + text);
                handleMessage(text);
            }

            @Override
            public void onClosing(WebSocket webSocket, int code, String reason) {
                Log.d(TAG, "WebSocket closing: " + reason);
                isConnecting = false;
            }

            @Override
            public void onClosed(WebSocket webSocket, int code, String reason) {
                Log.d(TAG, "WebSocket closed: " + code + " - " + reason);
                isConnecting = false;

                // 非正常关闭时重连
                if (code != 1000 && shouldReconnect) {
                    scheduleReconnect();
                }
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                Log.e(TAG, "WebSocket error", t);
                isConnecting = false;

                // 自动重连
                if (shouldReconnect) {
                    scheduleReconnect();
                }
            }
        });
    }

    /**
     * 处理收到的消息
     */
    private void handleMessage(String message) {
        try {
            JSONObject json = new JSONObject(message);
            String event = json.optString("event");

            if (listener != null) {
                switch (event) {
                    case "registered":
                        listener.onRegistered();
                        break;
                    case "playlist_update":
                        int playlistId = json.optInt("playlist_id");
                        listener.onPlaylistUpdate(playlistId);
                        break;
                    case "schedule_update":
                        listener.onScheduleUpdate();
                        break;
                    case "force_sync":
                        listener.onForceSync();
                        break;
                    case "reboot":
                        listener.onReboot();
                        break;
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Failed to handle message", e);
        }
    }

    /**
     * 发送心跳
     */
    public void sendHeartbeat() {
        if (webSocket != null) {
            try {
                JSONObject heartbeat = new JSONObject();
                heartbeat.put("device_id", deviceId);
                webSocket.send(heartbeat.toString());
            } catch (Exception e) {
                Log.e(TAG, "Failed to send heartbeat", e);
            }
        }
    }

    /**
     * 重置重试状态
     */
    private void resetRetryState() {
        retryCount = 0;
        currentRetryDelay = INITIAL_RETRY_DELAY_MS;
    }

    /**
     * 调度重连（指数退避 + 随机抖动）
     */
    private void scheduleReconnect() {
        if (!shouldReconnect) {
            Log.d(TAG, "Reconnect disabled, skip");
            return;
        }

        if (retryCount >= MAX_RETRY_COUNT) {
            Log.w(TAG, "Max retry count reached (" + MAX_RETRY_COUNT + "), giving up");
            if (listener != null) {
                mainHandler.post(() -> listener.onConnectionFailed());
            }
            return;
        }

        retryCount++;

        // 计算延迟：指数退避 + 随机抖动
        int baseDelay = Math.min(currentRetryDelay, MAX_RETRY_DELAY_MS);
        int jitter = (int) (baseDelay * JITTER_FACTOR * (random.nextDouble() * 2 - 1));  // +/- 30%
        int actualDelay = Math.max(baseDelay + jitter, INITIAL_RETRY_DELAY_MS);

        Log.d(TAG, "Scheduling reconnect #" + retryCount + " in " + actualDelay + "ms");

        mainHandler.postDelayed(() -> {
            if (shouldReconnect) {
                connect(deviceId, listener);
            }
        }, actualDelay);

        // 下次延迟加倍（指数退避）
        currentRetryDelay = Math.min(currentRetryDelay * 2, MAX_RETRY_DELAY_MS);
    }

    /**
     * 断开连接
     */
    public void disconnect() {
        shouldReconnect = false;  // 阻止自动重连
        mainHandler.removeCallbacksAndMessages(null);  // 取消待定重连

        if (webSocket != null) {
            webSocket.close(1000, "Client disconnect");
            webSocket = null;
        }

        isConnecting = false;
        resetRetryState();
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
