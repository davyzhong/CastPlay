package com.castplay.player.data.db;

import android.content.Context;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import com.castplay.player.data.db.dao.*;
import com.castplay.player.data.db.entity.*;

/**
 * Room 数据库
 */
@Database(entities = {
        DeviceEntity.class,
        MediaFileEntity.class,
        PlaylistEntity.class
}, version = 1, exportSchema = false)
public abstract class AppDatabase extends RoomDatabase {

    private static volatile AppDatabase INSTANCE;
    private static final String DATABASE_NAME = "castplay.db";

    public abstract MediaFileDao mediaFileDao();

    public abstract PlaylistDao playlistDao();

    public static AppDatabase getInstance(Context context) {
        if (INSTANCE == null) {
            synchronized (AppDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = Room.databaseBuilder(
                            context.getApplicationContext(),
                            AppDatabase.class,
                            DATABASE_NAME)
                            .fallbackToDestructiveMigration()
                            .build();
                }
            }
        }
        return INSTANCE;
    }
}
