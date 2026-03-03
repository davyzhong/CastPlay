package com.castplay.player.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.castplay.player.data.db.dao.MediaFileDao
import com.castplay.player.data.db.dao.PlaylistDao
import com.castplay.player.data.db.entity.DeviceEntity
import com.castplay.player.data.db.entity.MediaFileEntity
import com.castplay.player.data.db.entity.PlaylistEntity

/**
 * Room 数据库
 *
 * 版本历史:
 * - v1: 初始版本，包含 DeviceEntity, MediaFileEntity, PlaylistEntity
 * - v2: MediaFileEntity 添加 playback_speed 字段
 * - v3: MediaFileEntity 添加 last_played_at 字段
 */
@Database(
    entities = [
        DeviceEntity::class,
        MediaFileEntity::class,
        PlaylistEntity::class
    ],
    version = 3,
    exportSchema = true
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun mediaFileDao(): MediaFileDao
    abstract fun playlistDao(): PlaylistDao

    companion object {
        private const val DATABASE_NAME = "castplay.db"

        @Volatile
        private var INSTANCE: AppDatabase? = null

        // ============= 迁移定义 =============

        /**
         * v1 → v2: 添加播放速度字段
         */
        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN playback_speed REAL NOT NULL DEFAULT 1.0"
                )
            }
        }

        /**
         * v2 → v3: 添加最后播放时间
         */
        private val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN last_played_at INTEGER NOT NULL DEFAULT 0"
                )
            }
        }

        /**
         * 跨版本迁移: v1 → v3 (合并多个迁移)
         */
        private val MIGRATION_1_3 = object : Migration(1, 3) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN playback_speed REAL NOT NULL DEFAULT 1.0"
                )
                database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN last_played_at INTEGER NOT NULL DEFAULT 0"
                )
            }
        }

        // ============= 数据库实例 =============

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: buildDatabase(context).also { INSTANCE = it }
            }
        }

        private fun buildDatabase(context: Context): AppDatabase {
            return Room.databaseBuilder(
                context.applicationContext,
                AppDatabase::class.java,
                DATABASE_NAME
            )
                // 添加所有迁移
                .addMigrations(
                    MIGRATION_1_2,
                    MIGRATION_2_3,
                    MIGRATION_1_3  // 跨版本迁移
                )
                // 降级时重建（从新版本降级到旧版本）
                .fallbackToDestructiveMigrationOnDowngrade()
                .build()
        }

        /**
         * 仅测试用：内存数据库
         */
        fun getTestInstance(context: Context): AppDatabase {
            return Room.inMemoryDatabaseBuilder(
                context.applicationContext,
                AppDatabase::class.java
            )
                .allowMainThreadQueries()
                .build()
        }
    }
}
