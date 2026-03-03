package com.castplay.player.viewmodel;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import com.castplay.player.data.model.MediaItem;
import com.castplay.player.data.model.Playlist;

import java.util.ArrayList;
import java.util.List;

/**
 * 播放器 ViewModel
 *
 * 管理播放状态，实现 MVVM 架构，解耦 UI 和业务逻辑。
 *
 * 优势：
 * - 配置变更（如屏幕旋转）时数据不丢失
 * - 便于单元测试
 * - UI 和数据逻辑分离
 */
public class PlayerViewModel extends ViewModel {

    // === 播放状态 ===
    private final MutableLiveData<Boolean> _isPlaying = new MutableLiveData<>(false);
    public final LiveData<Boolean> isPlaying = _isPlaying;

    private final MutableLiveData<Boolean> _isLoading = new MutableLiveData<>(false);
    public final LiveData<Boolean> isLoading = _isLoading;

    // === 当前播放信息 ===
    private final MutableLiveData<Playlist> _currentPlaylist = new MutableLiveData<>();
    public final LiveData<Playlist> currentPlaylist = _currentPlaylist;

    private final MutableLiveData<MediaItem> _currentMedia = new MutableLiveData<>();
    public final LiveData<MediaItem> currentMedia = _currentMedia;

    private final MutableLiveData<Integer> _currentIndex = new MutableLiveData<>(0);
    public final LiveData<Integer> currentIndex = _currentIndex;

    // === 媒体列表 ===
    private final MutableLiveData<List<MediaItem>> _mediaList = new MutableLiveData<>(new ArrayList<>());
    public final LiveData<List<MediaItem>> mediaList = _mediaList;

    // === 错误状态 ===
    private final MutableLiveData<String> _error = new MutableLiveData<>();
    public final LiveData<String> error = _error;

    // === 设备信息 ===
    private final MutableLiveData<String> _deviceId = new MutableLiveData<>();
    public final LiveData<String> deviceId = _deviceId;

    private final MutableLiveData<Boolean> _isConnected = new MutableLiveData<>(false);
    public final LiveData<Boolean> isConnected = _isConnected;

    // =============================================
    // Actions
    // =============================================

    /**
     * 设置设备 ID
     */
    public void setDeviceId(String id) {
        _deviceId.setValue(id);
    }

    /**
     * 设置连接状态
     */
    public void setConnected(boolean connected) {
        _isConnected.setValue(connected);
    }

    /**
     * 加载播放列表
     */
    public void loadPlaylist(Playlist playlist) {
        _currentPlaylist.setValue(playlist);
        if (playlist != null && playlist.getItems() != null) {
            _mediaList.setValue(playlist.getItems());
            _currentIndex.setValue(0);
            if (!playlist.getItems().isEmpty()) {
                _currentMedia.setValue(playlist.getItems().get(0));
            }
        }
    }

    /**
     * 设置媒体列表
     */
    public void setMediaList(List<MediaItem> items) {
        _mediaList.setValue(items);
        _currentIndex.setValue(0);
        if (items != null && !items.isEmpty()) {
            _currentMedia.setValue(items.get(0));
        }
    }

    /**
     * 开始播放
     */
    public void play() {
        _isPlaying.setValue(true);
    }

    /**
     * 暂停播放
     */
    public void pause() {
        _isPlaying.setValue(false);
    }

    /**
     * 播放下一个
     */
    public void playNext() {
        List<MediaItem> items = _mediaList.getValue();
        Integer index = _currentIndex.getValue();

        if (items == null || items.isEmpty() || index == null) {
            return;
        }

        int nextIndex = (index + 1) % items.size();
        _currentIndex.setValue(nextIndex);
        _currentMedia.setValue(items.get(nextIndex));
    }

    /**
     * 播放上一个
     */
    public void playPrevious() {
        List<MediaItem> items = _mediaList.getValue();
        Integer index = _currentIndex.getValue();

        if (items == null || items.isEmpty() || index == null) {
            return;
        }

        int prevIndex = (index - 1 + items.size()) % items.size();
        _currentIndex.setValue(prevIndex);
        _currentMedia.setValue(items.get(prevIndex));
    }

    /**
     * 跳转到指定索引
     */
    public void playAt(int index) {
        List<MediaItem> items = _mediaList.getValue();
        if (items == null || index < 0 || index >= items.size()) {
            return;
        }

        _currentIndex.setValue(index);
        _currentMedia.setValue(items.get(index));
    }

    /**
     * 设置加载状态
     */
    public void setLoading(boolean loading) {
        _isLoading.setValue(loading);
    }

    /**
     * 设置错误信息
     */
    public void setError(String errorMessage) {
        _error.setValue(errorMessage);
    }

    /**
     * 清除错误
     */
    public void clearError() {
        _error.setValue(null);
    }

    /**
     * 获取媒体总数
     */
    public int getMediaCount() {
        List<MediaItem> items = _mediaList.getValue();
        return items != null ? items.size() : 0;
    }

    /**
     * 是否有下一个
     */
    public boolean hasNext() {
        return getMediaCount() > 0;
    }

    /**
     * 是否正在播放
     */
    public boolean isCurrentlyPlaying() {
        Boolean playing = _isPlaying.getValue();
        return playing != null && playing;
    }
}
