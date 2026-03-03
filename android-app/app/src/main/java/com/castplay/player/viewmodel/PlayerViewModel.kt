package com.castplay.player.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.castplay.player.data.model.MediaItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

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
class PlayerViewModel : ViewModel() {

    // === StateFlow (推荐) ===
    private val _uiState = MutableStateFlow(PlayerUiState())
    val uiState: StateFlow<PlayerUiState> = _uiState.asStateFlow()

    /**
     * 播放器 UI 状态
     */
    data class PlayerUiState(
        val isPlaying: Boolean = false,
        val isLoading: Boolean = false,
        val currentMedia: MediaItem? = null,
        val currentIndex: Int = 0,
        val mediaList: List<MediaItem> = emptyList(),
        val deviceId: String? = null,
        val isConnected: Boolean = false,
        val error: String? = null,
        val playlistId: Int? = null,
        val playlistName: String? = null
    )

    // === LiveData (兼容旧代码) ===
    private val _isPlaying = MutableLiveData(false)
    val isPlaying: LiveData<Boolean> = _isPlaying

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _currentMedia = MutableLiveData<MediaItem?>()
    val currentMedia: LiveData<MediaItem?> = _currentMedia

    private val _currentIndex = MutableLiveData(0)
    val currentIndex: LiveData<Int> = _currentIndex

    private val _mediaList = MutableLiveData<List<MediaItem>>(emptyList())
    val mediaList: LiveData<List<MediaItem>> = _mediaList

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    private val _deviceId = MutableLiveData<String?>()
    val deviceId: LiveData<String?> = _deviceId

    private val _isConnected = MutableLiveData(false)
    val isConnected: LiveData<Boolean> = _isConnected

    // =============================================
    // Actions (StateFlow 版本)
    // =============================================

    /**
     * 设置设备 ID
     */
    fun setDeviceId(id: String) {
        _deviceId.value = id
        _uiState.update { it.copy(deviceId = id) }
    }

    /**
     * 设置连接状态
     */
    fun setConnected(connected: Boolean) {
        _isConnected.value = connected
        _uiState.update { it.copy(isConnected = connected) }
    }

    /**
     * 设置媒体列表
     */
    fun setMediaList(items: List<MediaItem>) {
        _mediaList.value = items
        _currentIndex.value = 0
        val firstItem = items.firstOrNull()
        _currentMedia.value = firstItem

        _uiState.update { state ->
            state.copy(
                mediaList = items,
                currentIndex = 0,
                currentMedia = firstItem
            )
        }
    }

    /**
     * 设置播放列表
     */
    fun setPlaylist(id: Int, name: String, items: List<MediaItem>) {
        _mediaList.value = items
        _currentIndex.value = 0
        val firstItem = items.firstOrNull()
        _currentMedia.value = firstItem

        _uiState.update { state ->
            state.copy(
                playlistId = id,
                playlistName = name,
                mediaList = items,
                currentIndex = 0,
                currentMedia = firstItem
            )
        }
    }

    /**
     * 开始播放
     */
    fun play() {
        _isPlaying.value = true
        _uiState.update { it.copy(isPlaying = true) }
    }

    /**
     * 暂停播放
     */
    fun pause() {
        _isPlaying.value = false
        _uiState.update { it.copy(isPlaying = false) }
    }

    /**
     * 播放下一个
     */
    fun playNext() {
        val state = _uiState.value
        if (state.mediaList.isEmpty()) return

        val nextIndex = (state.currentIndex + 1) % state.mediaList.size
        val nextMedia = state.mediaList[nextIndex]

        _currentIndex.value = nextIndex
        _currentMedia.value = nextMedia

        _uiState.update { it.copy(currentIndex = nextIndex, currentMedia = nextMedia) }
    }

    /**
     * 播放上一个
     */
    fun playPrevious() {
        val state = _uiState.value
        if (state.mediaList.isEmpty()) return

        val prevIndex = (state.currentIndex - 1 + state.mediaList.size) % state.mediaList.size
        val prevMedia = state.mediaList[prevIndex]

        _currentIndex.value = prevIndex
        _currentMedia.value = prevMedia

        _uiState.update { it.copy(currentIndex = prevIndex, currentMedia = prevMedia) }
    }

    /**
     * 跳转到指定索引
     */
    fun playAt(index: Int) {
        val state = _uiState.value
        if (index < 0 || index >= state.mediaList.size) return

        val media = state.mediaList[index]

        _currentIndex.value = index
        _currentMedia.value = media

        _uiState.update { it.copy(currentIndex = index, currentMedia = media) }
    }

    /**
     * 设置加载状态
     */
    fun setLoading(loading: Boolean) {
        _isLoading.value = loading
        _uiState.update { it.copy(isLoading = loading) }
    }

    /**
     * 设置错误信息
     */
    fun setError(errorMessage: String) {
        _error.value = errorMessage
        _uiState.update { it.copy(error = errorMessage) }
    }

    /**
     * 清除错误
     */
    fun clearError() {
        _error.value = null
        _uiState.update { it.copy(error = null) }
    }

    /**
     * 获取媒体总数
     */
    fun getMediaCount(): Int = _uiState.value.mediaList.size

    /**
     * 是否有下一个
     */
    fun hasNext(): Boolean = getMediaCount() > 0

    /**
     * 是否正在播放
     */
    fun isCurrentlyPlaying(): Boolean = _uiState.value.isPlaying
}
