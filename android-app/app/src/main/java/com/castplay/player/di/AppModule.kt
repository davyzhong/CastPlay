package com.castplay.player.di

import android.content.Context
import com.castplay.player.data.db.AppDatabase
import com.castplay.player.data.db.dao.MediaFileDao
import com.castplay.player.data.db.dao.PlaylistDao
import com.castplay.player.network.ApiService
import com.castplay.player.network.RetrofitClient
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt 依赖注入模块
 *
 * 提供应用级别的单例依赖
 */
@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    /**
     * 提供 ApiService 实例
     */
    @Provides
    @Singleton
    fun provideApiService(): ApiService {
        return RetrofitClient.getInstance().create(ApiService::class.java)
    }

    /**
     * 提供数据库实例
     */
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return AppDatabase.getInstance(context)
    }

    /**
     * 提供 MediaFileDao
     */
    @Provides
    fun provideMediaFileDao(database: AppDatabase): MediaFileDao {
        return database.mediaFileDao()
    }

    /**
     * 提供 PlaylistDao
     */
    @Provides
    fun providePlaylistDao(database: AppDatabase): PlaylistDao {
        return database.playlistDao()
    }
}
