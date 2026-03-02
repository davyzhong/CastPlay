package com.castplay.player.network;

import android.util.Log;
import com.castplay.player.BuildConfig;
import okhttp3.*;
import org.json.JSONObject;

/**
 * WebSocket 连接管理器
 */
public class WebSocketManager {
    private static final String TAG = "WebSocketManager";
    private static WebSocketManager instance;

    private OkHttpClient client;
    private WebSocket webSocket;
    private String deviceId;
    private WebSocketListener listener;

    private WebSocketManager() {
        client = new OkHttpClient.Builder()
                .retryOnConnectionFailure(true)
                .build();
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
        this.deviceId = deviceId;
        this.listener = listener;

        Request request = new Request.Builder()
                .url(BuildConfig.WS_URL)
                .build();

        webSocket = client.newWebSocket(request, new okhttp3.WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                Log.d(TAG, "WebSocket connected");

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
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                Log.e(TAG, "WebSocket error", t);

                // 自动重连
                reconnect();
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
     * 重连
     */
    private void reconnect() {
        // 延迟5秒后重连
        new android.os.Handler(android.os.Looper.getMainLooper())
                .postDelayed(() -> connect(deviceId, listener), 5000);
    }

    /**
     * 断开连接
     */
    public void disconnect() {
        if (webSocket != null) {
            webSocket.close(1000, "Client disconnect");
            webSocket = null;
        }
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
    }
}
