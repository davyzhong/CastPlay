package com.castplay.player.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * 定时任务广播接收器
 */
class ScheduleReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "ScheduleReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        Log.d(TAG, "Received action: $action")

        when (action) {
            "com.castplay.player.POWER_ON" -> {
                // 开机逻辑 - 启动 MainActivity
                val launchIntent = Intent(context, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(launchIntent)
                Log.d(TAG, "Power ON - Starting MainActivity")
            }

            "com.castplay.player.POWER_OFF" -> {
                // 关机逻辑 - 关闭应用
                // Android 不支持应用自行关机，这里可以停止播放并显示黑屏
                val broadcastIntent = Intent("com.castplay.player.STOP_PLAYBACK")
                context.sendBroadcast(broadcastIntent)
                Log.d(TAG, "Power OFF - Stopping playback")
            }
        }
    }
}
