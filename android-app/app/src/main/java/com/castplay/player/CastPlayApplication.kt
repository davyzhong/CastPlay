package com.castplay.player

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * CastPlay 应用入口
 *
 * 使用 @HiltAndroidApp 注解启用 Hilt 依赖注入
 */
@HiltAndroidApp
class CastPlayApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        // 应用初始化逻辑
    }
}
