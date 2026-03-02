package com.castplay.player.data.db.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

/**
 * 播放列表实体
 */
@Entity(tableName = "playlist")
public class PlaylistEntity {

    @PrimaryKey
    private int id;

    private String name;
    private String version; // 版本号，用于检查更新
    private long lastUpdated;

    // Getters and Setters
    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public long getLastUpdated() {
        return lastUpdated;
    }

    public void setLastUpdated(long lastUpdated) {
        this.lastUpdated = lastUpdated;
    }
}
