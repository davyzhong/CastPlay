package com.castplay.player.service;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;
import com.castplay.player.data.model.InitResponse;

import java.util.Calendar;
import java.util.List;

/**
 * 定时管理器 - 负责定时开关机
 */
public class ScheduleManager {
    private static final String TAG = "ScheduleManager";
    private static final int POWER_ON_REQUEST_CODE = 1001;
    private static final int POWER_OFF_REQUEST_CODE = 1002;

    private Context context;
    private AlarmManager alarmManager;

    public ScheduleManager(Context context) {
        this.context = context;
        this.alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
    }

    /**
     * 设置定时任务
     */
    public void setSchedule(InitResponse.Schedule schedule) {
        if (schedule == null) {
            Log.w(TAG, "Schedule is null");
            return;
        }

        // 取消现有定时任务
        cancelSchedule();

        // 解析开机时间
        if (schedule.getPowerOnTime() != null) {
            Calendar powerOnCal = parseTime(schedule.getPowerOnTime());
            if (powerOnCal != null && isWeekdayEnabled(powerOnCal, schedule.getWeekdays())) {
                schedulePowerOn(powerOnCal);
            }
        }

        // 解析关机时间
        if (schedule.getPowerOffTime() != null) {
            Calendar powerOffCal = parseTime(schedule.getPowerOffTime());
            if (powerOffCal != null && isWeekdayEnabled(powerOffCal, schedule.getWeekdays())) {
                schedulePowerOff(powerOffCal);
            }
        }

        Log.d(TAG, "Schedule set: ON=" + schedule.getPowerOnTime() + ", OFF=" + schedule.getPowerOffTime());
    }

    /**
     * 解析时间字符串
     */
    private Calendar parseTime(String timeStr) {
        try {
            String[] parts = timeStr.split(":");
            int hour = Integer.parseInt(parts[0]);
            int minute = Integer.parseInt(parts[1]);

            Calendar calendar = Calendar.getInstance();
            calendar.set(Calendar.HOUR_OF_DAY, hour);
            calendar.set(Calendar.MINUTE, minute);
            calendar.set(Calendar.SECOND, 0);
            calendar.set(Calendar.MILLISECOND, 0);

            // 如果时间已过，设置为明天
            if (calendar.before(Calendar.getInstance())) {
                calendar.add(Calendar.DAY_OF_MONTH, 1);
            }

            return calendar;
        } catch (Exception e) {
            Log.e(TAG, "Failed to parse time: " + timeStr, e);
            return null;
        }
    }

    /**
     * 检查是否在工作日
     */
    private boolean isWeekdayEnabled(Calendar calendar, List<Integer> weekdays) {
        if (weekdays == null || weekdays.isEmpty()) {
            return true;
        }

        int dayOfWeek = calendar.get(Calendar.DAY_OF_WEEK);
        // Calendar.DAY_OF_WEEK: 1=Sunday, 2=Monday, ...
        // 转换为: 1=Monday, 7=Sunday
        int day = (dayOfWeek == Calendar.SUNDAY) ? 7 : dayOfWeek - 1;

        return weekdays.contains(day);
    }

    /**
     * 设置开机定时
     */
    private void schedulePowerOn(Calendar calendar) {
        Intent intent = new Intent("com.castplay.player.POWER_ON");
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context,
                POWER_ON_REQUEST_CODE,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP,
                    calendar.getTimeInMillis(),
                    pendingIntent);
        } else {
            alarmManager.setExact(
                    AlarmManager.RTC_WAKEUP,
                    calendar.getTimeInMillis(),
                    pendingIntent);
        }

        Log.d(TAG, "Power ON scheduled at: " + calendar.getTime());
    }

    /**
     * 设置关机定时
     */
    private void schedulePowerOff(Calendar calendar) {
        Intent intent = new Intent("com.castplay.player.POWER_OFF");
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context,
                POWER_OFF_REQUEST_CODE,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP,
                    calendar.getTimeInMillis(),
                    pendingIntent);
        } else {
            alarmManager.setExact(
                    AlarmManager.RTC_WAKEUP,
                    calendar.getTimeInMillis(),
                    pendingIntent);
        }

        Log.d(TAG, "Power OFF scheduled at: " + calendar.getTime());
    }

    /**
     * 取消定时任务
     */
    public void cancelSchedule() {
        // 取消开机定时
        Intent powerOnIntent = new Intent("com.castplay.player.POWER_ON");
        PendingIntent powerOnPendingIntent = PendingIntent.getBroadcast(
                context,
                POWER_ON_REQUEST_CODE,
                powerOnIntent,
                PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (powerOnPendingIntent != null) {
            alarmManager.cancel(powerOnPendingIntent);
        }

        // 取消关机定时
        Intent powerOffIntent = new Intent("com.castplay.player.POWER_OFF");
        PendingIntent powerOffPendingIntent = PendingIntent.getBroadcast(
                context,
                POWER_OFF_REQUEST_CODE,
                powerOffIntent,
                PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (powerOffPendingIntent != null) {
            alarmManager.cancel(powerOffPendingIntent);
        }

        Log.d(TAG, "Schedule cancelled");
    }
}
