package com.castplay.player.data.model;

/**
 * 媒体项模型
 */
public class MediaItem {
    private int id;
    private String fileName;
    private String fileType;
    private String filePath;
    private int displayDuration;

    public MediaItem(int id, String fileName, String fileType, String filePath, int displayDuration) {
        this.id = id;
        this.fileName = fileName;
        this.fileType = fileType;
        this.filePath = filePath;
        this.displayDuration = displayDuration;
    }

    public int getId() {
        return id;
    }

    public String getFileName() {
        return fileName;
    }

    public String getFileType() {
        return fileType;
    }

    public String getFilePath() {
        return filePath;
    }

    public int getDisplayDuration() {
        return displayDuration;
    }
}
