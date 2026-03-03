package com.castplay.player.service

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import com.castplay.player.data.model.InitResponse
import java.util.Calendar

/**
 * 定时管理器 - 负责定时开关机
 */
class ScheduleManager(context: Context) {

    companion object {
        private const val TAG = "ScheduleManager"
        private const val POWER_ON_REQUEST_CODE = 1001
        private const val POWER_OFF_REQUEST_CODE = 1002
    }

    private val appContext: Context = context.applicationContext
    private val alarmManager: AlarmManager =
        context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

    /**
     * 设置定时任务
     */
    fun setSchedule(schedule: InitResponse.Schedule?) {
        if (schedule == null) {
            Log.w(TAG, "Schedule is null")
            return
        }

        // 取消现有定时任务
        cancelSchedule()

        // 解析开机时间
        schedule.powerOnTime?.let { powerOnTime ->
            parseTime(powerOnTime)?.let { powerOnCal ->
                if (isWeekdayEnabled(powerOnCal, schedule.weekdays)) {
                    schedulePowerOn(powerOnCal)
                }
            }
        }

        // 解析关机时间
        schedule.powerOffTime?.let { powerOffTime ->
            parseTime(powerOffTime)?.let { powerOffCal ->
                if (isWeekdayEnabled(powerOffCal, schedule.weekdays)) {
                    schedulePowerOff(powerOffCal)
                }
            }
        }

        Log.d(TAG, "Schedule set: ON=${schedule.powerOnTime}, OFF=${schedule.powerOffTime}")
    }

    /**
     * 解析时间字符串
     */
    private fun parseTime(timeStr: String): Calendar? {
        return try {
            val parts = timeStr.split(":")
            val hour = parts[0].toInt()
            val minute = parts[1].toInt()

            Calendar.getInstance().apply {
                set(Calendar.HOUR_OF_DAY, hour)
                set(Calendar.MINUTE, minute)
                set(Calendar.SECOND, 0)
                set(Calendar.MILLISECOND, 0)

                // 如果时间已过，设置为明天
                if (before(Calendar.getInstance())) {
                    add(Calendar.DAY_OF_MONTH, 1)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse time: $timeStr", e)
            null
        }
    }

    /**
     * 检查是否在工作日
     */
    private fun isWeekdayEnabled(calendar: Calendar, weekdays: List<Int>?): Boolean {
        if (weekdays.isNullOrEmpty()) {
            return true
        }

        val dayOfWeek = calendar.get(Calendar.DAY_OF_WEEK)
        // Calendar.DAY_OF_WEEK: 1=Sunday, 2=Monday, ...
        // 转换为: 1=Monday, 7=Sunday
        val day = if (dayOfWeek == Calendar.SUNDAY) 7 else dayOfWeek - 1

        return weekdays.contains(day)
    }

    /**
     * 设置开机定时
     */
    private fun schedulePowerOn(calendar: Calendar) {
        val intent = Intent("com.castplay.player.POWER_ON")
        val pendingIntent = PendingIntent.getBroadcast(
            appContext,
            POWER_ON_REQUEST_CODE,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                calendar.timeInMillis,
                pendingIntent
            )
        } else {
            alarmManager.setExact(
                AlarmManager.RTC_WAKEUP,
                calendar.timeInMillis,
                pendingIntent
            )
        }

        Log.d(TAG, "Power ON scheduled at: ${calendar.time}")
    }

    /**
     * 设置关机定时
     */
    private fun schedulePowerOff(calendar: Calendar) {
        val intent = Intent("com.castplay.player.POWER_OFF")
        val pendingIntent = PendingIntent.getBroadcast(
            appContext,
            POWER_OFF_REQUEST_CODE,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                calendar.timeInMillis,
                pendingIntent
            )
        } else {
            alarmManager.setExact(
                AlarmManager.RTC_WAKEUP,
                calendar.timeInMillis,
                pendingIntent
            )
        }

        Log.d(TAG, "Power OFF scheduled at: ${calendar.time}")
    }

    /**
     * 取消定时任务
     */
    fun cancelSchedule() {
        // 取消开机定时
        val powerOnIntent = Intent("com.castplay.player.POWER_ON")
        val powerOnPendingIntent = PendingIntent.getBroadcast(
            appContext,
            POWER_ON_REQUEST_CODE,
            powerOnIntent,
            PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE
        )
        powerOnPendingIntent?.let { alarmManager.cancel(it) }

        // 取消关机定时
        val powerOffIntent = Intent("com.castplay.player.POWER_OFF")
        val powerOffPendingIntent = PendingIntent.getBroadcast(
            appContext,
            POWER_OFF_REQUEST_CODE,
            powerOffIntent,
            PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE
        )
        powerOffPendingIntent?.let { alarmManager.cancel(it) }

        Log.d(TAG, "Schedule cancelled")
    }
}
