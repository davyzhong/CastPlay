package com.castplay.player.receiver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * 定时任务广播接收器
 */
public class ScheduleReceiver extends BroadcastReceiver {
    private static final String TAG = "ScheduleReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        Log.d(TAG, "Received action: " + action);

        if ("com.castplay.player.POWER_ON".equals(action)) {
            // 开机逻辑 - 启动MainActivity
            Intent launchIntent = new Intent(context, com.castplay.player.MainActivity.class);
            launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(launchIntent);
            Log.d(TAG, "Power ON - Starting MainActivity");

        } else if ("com.castplay.player.POWER_OFF".equals(action)) {
            // 关机逻辑 - 关闭应用
            // Android 不支持应用自行关机，这里可以停止播放并显示黑屏
            Intent broadcastIntent = new Intent("com.castplay.player.STOP_PLAYBACK");
            context.sendBroadcast(broadcastIntent);
            Log.d(TAG, "Power OFF - Stopping playback");
        }
    }
}
