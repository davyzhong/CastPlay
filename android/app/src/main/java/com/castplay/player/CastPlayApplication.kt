package com.castplay.player

import android.app.Application
import android.app.DownloadManager
import android.content.Context
import android.util.Log

/**
 * CastPlay 应用程序类
 * 初始化全局组件
 */
class CastPlayApplication : Application() {

    companion object {
        private const val TAG = "CastPlayApp"
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "CastPlay Application starting...")

        // 初始化缓存管理器
        CacheManager.getInstance(this)

        // 设置全局异常处理
        setupExceptionHandler()

        // 初始化网络监控
        initNetworkMonitor()
    }

    /**
     * 设置全局异常处理
     */
    private fun setupExceptionHandler() {
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Log.e(TAG, "Uncaught exception in thread ${thread.name}", throwable)
            // 可以在此上报错误
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }

    /**
     * 初始化网络监控
     */
    private fun initNetworkMonitor() {
        // 网络状态变化时会发送广播
        // 播放器前端会监听 online/offline 事件
    }
}
