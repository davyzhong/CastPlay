package com.castplay.player.data.model;

import com.google.gson.annotations.SerializedName;
import java.util.List;

/**
 * 初始化响应模型
 */
public class InitResponse {

    private Device device;
    private List<PlaylistData> playlists;
    private Schedule schedule;

    @SerializedName("websocket_url")
    private String websocketUrl;

    public Device getDevice() {
        return device;
    }

    public List<PlaylistData> getPlaylists() {
        return playlists;
    }

    public Schedule getSchedule() {
        return schedule;
    }

    public String getWebsocketUrl() {
        return websocketUrl;
    }

    public static class Device {
        private int id;

        @SerializedName("device_id")
        private String deviceId;

        @SerializedName("device_name")
        private String deviceName;

        private String timezone;

        public int getId() {
            return id;
        }

        public String getDeviceId() {
            return deviceId;
        }

        public String getDeviceName() {
            return deviceName;
        }

        public String getTimezone() {
            return timezone;
        }
    }

    public static class PlaylistData {
        private int id;
        private String name;
        private String version;
        private List<PlaylistItemData> items;

        public int getId() {
            return id;
        }

        public String getName() {
            return name;
        }

        public String getVersion() {
            return version;
        }

        public List<PlaylistItemData> getItems() {
            return items;
        }
    }

    public static class PlaylistItemData {
        private int id;

        @SerializedName("media_id")
        private int mediaId;

        @SerializedName("file_name")
        private String fileName;

        @SerializedName("file_type")
        private String fileType;

        @SerializedName("file_url")
        private String fileUrl;

        @SerializedName("display_order")
        private int displayOrder;

        @SerializedName("display_duration")
        private int displayDuration;

        @SerializedName("file_size")
        private long fileSize;

        @SerializedName("md5_hash")
        private String md5Hash;

        public int getId() {
            return id;
        }

        public int getMediaId() {
            return mediaId;
        }

        public String getFileName() {
            return fileName;
        }

        public String getFileType() {
            return fileType;
        }

        public String getFileUrl() {
            return fileUrl;
        }

        public int getDisplayOrder() {
            return displayOrder;
        }

        public int getDisplayDuration() {
            return displayDuration;
        }

        public long getFileSize() {
            return fileSize;
        }

        public String getMd5Hash() {
            return md5Hash;
        }
    }

    public static class Schedule {
        @SerializedName("power_on_time")
        private String powerOnTime;

        @SerializedName("power_off_time")
        private String powerOffTime;

        private List<Integer> weekdays;
        private String timezone;

        public String getPowerOnTime() {
            return powerOnTime;
        }

        public String getPowerOffTime() {
            return powerOffTime;
        }

        public List<Integer> getWeekdays() {
            return weekdays;
        }

        public String getTimezone() {
            return timezone;
        }
    }
}
