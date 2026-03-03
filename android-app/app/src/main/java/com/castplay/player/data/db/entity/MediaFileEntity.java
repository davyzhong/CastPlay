package com.castplay.player.data.db.entity;

import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

/**
 * 媒体文件实体
 *
 * 版本历史:
 * - v1: 初始版本
 * - v2: 添加 playbackSpeed 字段
 * - v3: 添加 lastPlayedAt 字段
 */
@Entity(tableName = "media_file")
public class MediaFileEntity {

    @PrimaryKey
    private int id;

    private int playlistId;
    private String fileName;
    private String fileType; // image/video/ppt
    private String filePath; // 本地文件路径
    private String fileUrl; // 服务器下载URL
    private int displayOrder;
    private int displayDuration;
    private long fileSize;
    private String md5Hash;
    private boolean isDownloaded;

    // v2 新增: 播放速度
    @ColumnInfo(name = "playback_speed", defaultValue = "1.0")
    private float playbackSpeed = 1.0f;

    // v3 新增: 最后播放时间
    @ColumnInfo(name = "last_played_at", defaultValue = "0")
    private long lastPlayedAt = 0;

    // Getters and Setters
    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public int getPlaylistId() {
        return playlistId;
    }

    public void setPlaylistId(int playlistId) {
        this.playlistId = playlistId;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getFileType() {
        return fileType;
    }

    public void setFileType(String fileType) {
        this.fileType = fileType;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public String getFileUrl() {
        return fileUrl;
    }

    public void setFileUrl(String fileUrl) {
        this.fileUrl = fileUrl;
    }

    public int getDisplayOrder() {
        return displayOrder;
    }

    public void setDisplayOrder(int displayOrder) {
        this.displayOrder = displayOrder;
    }

    public int getDisplayDuration() {
        return displayDuration;
    }

    public void setDisplayDuration(int displayDuration) {
        this.displayDuration = displayDuration;
    }

    public long getFileSize() {
        return fileSize;
    }

    public void setFileSize(long fileSize) {
        this.fileSize = fileSize;
    }

    public String getMd5Hash() {
        return md5Hash;
    }

    public void setMd5Hash(String md5Hash) {
        this.md5Hash = md5Hash;
    }

    public boolean isDownloaded() {
        return isDownloaded;
    }

    public void setDownloaded(boolean downloaded) {
        isDownloaded = downloaded;
    }

    // v2 新增
    public float getPlaybackSpeed() {
        return playbackSpeed;
    }

    public void setPlaybackSpeed(float playbackSpeed) {
        this.playbackSpeed = playbackSpeed;
    }

    // v3 新增
    public long getLastPlayedAt() {
        return lastPlayedAt;
    }

    public void setLastPlayedAt(long lastPlayedAt) {
        this.lastPlayedAt = lastPlayedAt;
    }
}
