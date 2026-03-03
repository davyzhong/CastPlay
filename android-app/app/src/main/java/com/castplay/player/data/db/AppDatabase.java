package com.castplay.player.data.db;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.migration.Migration;
import androidx.sqlite.db.SupportSQLiteDatabase;

import com.castplay.player.data.db.dao.*;
import com.castplay.player.data.db.entity.*;

/**
 * Room 数据库
 *
 * 版本历史:
 * - v1: 初始版本，包含 DeviceEntity, MediaFileEntity, PlaylistEntity
 * - v2: MediaFileEntity 添加 playback_speed 字段
 * - v3: MediaFileEntity 添加 last_played_at 字段
 */
@Database(entities = {
        DeviceEntity.class,
        MediaFileEntity.class,
        PlaylistEntity.class
}, version = 3, exportSchema = true)
public abstract class AppDatabase extends RoomDatabase {

    private static volatile AppDatabase INSTANCE;
    private static final String DATABASE_NAME = "castplay.db";

    public abstract MediaFileDao mediaFileDao();

    public abstract PlaylistDao playlistDao();

    // ============= 迁移定义 =============

    /**
     * v1 → v2: 添加播放速度字段
     */
    static final Migration MIGRATION_1_2 = new Migration(1, 2) {
        @Override
        public void migrate(@NonNull SupportSQLiteDatabase database) {
            database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN playback_speed REAL NOT NULL DEFAULT 1.0"
            );
        }
    };

    /**
     * v2 → v3: 添加最后播放时间
     */
    static final Migration MIGRATION_2_3 = new Migration(2, 3) {
        @Override
        public void migrate(@NonNull SupportSQLiteDatabase database) {
            database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN last_played_at INTEGER NOT NULL DEFAULT 0"
            );
        }
    };

    /**
     * 跨版本迁移: v1 → v3 (合并多个迁移)
     */
    static final Migration MIGRATION_1_3 = new Migration(1, 3) {
        @Override
        public void migrate(@NonNull SupportSQLiteDatabase database) {
            database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN playback_speed REAL NOT NULL DEFAULT 1.0"
            );
            database.execSQL(
                    "ALTER TABLE media_file ADD COLUMN last_played_at INTEGER NOT NULL DEFAULT 0"
            );
        }
    };

    // ============= 数据库实例 =============

    public static AppDatabase getInstance(Context context) {
        if (INSTANCE == null) {
            synchronized (AppDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = buildDatabase(context);
                }
            }
        }
        return INSTANCE;
    }

    private static AppDatabase buildDatabase(Context context) {
        return Room.databaseBuilder(
                        context.getApplicationContext(),
                        AppDatabase.class,
                        DATABASE_NAME)
                // 添加所有迁移
                .addMigrations(
                        MIGRATION_1_2,
                        MIGRATION_2_3,
                        MIGRATION_1_3  // 跨版本迁移
                )
                // 降级时重建（从新版本降级到旧版本）
                .fallbackToDestructiveMigrationOnDowngrade()
                .build();
    }

    /**
     * 仅测试用：内存数据库
     */
    public static AppDatabase getTestInstance(Context context) {
        return Room.inMemoryDatabaseBuilder(
                        context.getApplicationContext(),
                        AppDatabase.class)
                .allowMainThreadQueries()
                .build();
    }
}
