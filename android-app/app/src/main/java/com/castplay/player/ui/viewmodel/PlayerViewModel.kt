package com.castplay.player.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.castplay.player.data.db.entity.MediaFileEntity
import com.castplay.player.data.db.entity.PlaylistEntity
import com.castplay.player.data.model.MediaItem
import com.castplay.player.data.model.RegisterResponse
import com.castplay.player.data.repository.DeviceRepository
import com.castplay.player.data.repository.MediaRepository
import com.castplay.player.data.repository.PlaylistRepository
import com.castplay.player.data.repository.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 播放器 ViewModel (合并版本)
 *
 * 使用 Hilt 注入，管理播放器的 UI 状态和播放控制
 * 整合了 Repository 数据层和播放控制功能
 */
@HiltViewModel
class PlayerViewModel @Inject constructor(
    private val deviceRepository: DeviceRepository,
    private val mediaRepository: MediaRepository,
    private val playlistRepository: PlaylistRepository
) : ViewModel() {

    // =============================================
    // UI State (统一状态管理)
    // =============================================

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

    private val _uiState = MutableStateFlow(PlayerUiState())
    val uiState: StateFlow<PlayerUiState> = _uiState.asStateFlow()

    // =============================================
    // Repository 数据状态
    // =============================================

    // 设备注册状态
    private val _registrationState = MutableStateFlow<Resource<RegisterResponse>?>(null)
    val registrationState: StateFlow<Resource<RegisterResponse>?> = _registrationState.asStateFlow()

    // 设备 ID
    private val _deviceId = MutableStateFlow<String?>(null)
    val deviceId: StateFlow<String?> = _deviceId.asStateFlow()

    // 播放列表
    private val _playlists = MutableStateFlow<Resource<List<PlaylistEntity>>>(Resource.Loading())
    val playlists: StateFlow<Resource<List<PlaylistEntity>>> = _playlists.asStateFlow()

    // 媒体文件
    private val _mediaFiles = MutableStateFlow<Resource<List<MediaFileEntity>>>(Resource.Loading())
    val mediaFiles: StateFlow<Resource<List<MediaFileEntity>>> = _mediaFiles.asStateFlow()

    // 当前播放状态 (保持兼容)
    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    init {
        // 初始化时加载保存的设备 ID
        val savedDeviceId = deviceRepository.getSavedDeviceId()
        _deviceId.value = savedDeviceId
        _uiState.update { it.copy(deviceId = savedDeviceId) }
    }

    // =============================================
    // 设备管理
    // =============================================

    /**
     * 注册设备
     */
    fun registerDevice(deviceName: String? = null) {
        viewModelScope.launch {
            deviceRepository.registerDevice(deviceName = deviceName).collect { resource ->
                _registrationState.value = resource

                if (resource is Resource.Success) {
                    val newDeviceId = resource.data.device.deviceId
                    _deviceId.value = newDeviceId
                    _uiState.update { it.copy(deviceId = newDeviceId) }
                }
            }
        }
    }

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
        _uiState.update { it.copy(isConnected = connected) }
    }

    /**
     * 检查设备是否已注册
     */
    fun isDeviceRegistered(): Boolean {
        return deviceRepository.isDeviceRegistered()
    }

    /**
     * 获取保存的设备 ID
     */
    fun getSavedDeviceId(): String? {
        return deviceRepository.getSavedDeviceId()
    }

    // =============================================
    // 数据加载
    // =============================================

    /**
     * 加载播放列表
     */
    fun loadPlaylists() {
        viewModelScope.launch {
            playlistRepository.getPlaylists().collect { resource ->
                _playlists.value = resource
            }
        }
    }

    /**
     * 加载媒体文件
     */
    fun loadMediaFiles() {
        viewModelScope.launch {
            mediaRepository.getMediaFiles().collect { resource ->
                _mediaFiles.value = resource
            }
        }
    }

    /**
     * 设置媒体列表
     */
    fun setMediaList(items: List<MediaItem>) {
        val firstItem = items.firstOrNull()
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
        val firstItem = items.firstOrNull()
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

    // =============================================
    // 播放控制
    // =============================================

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
     * 设置播放状态
     */
    fun setPlayingState(isPlaying: Boolean) {
        _isPlaying.value = isPlaying
        _uiState.update { it.copy(isPlaying = isPlaying) }
    }

    /**
     * 播放下一个
     */
    fun playNext() {
        val state = _uiState.value
        if (state.mediaList.isEmpty()) return

        val nextIndex = (state.currentIndex + 1) % state.mediaList.size
        val nextMedia = state.mediaList[nextIndex]

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

        _uiState.update { it.copy(currentIndex = prevIndex, currentMedia = prevMedia) }
    }

    /**
     * 跳转到指定索引
     */
    fun playAt(index: Int) {
        val state = _uiState.value
        if (index < 0 || index >= state.mediaList.size) return

        val media = state.mediaList[index]
        _uiState.update { it.copy(currentIndex = index, currentMedia = media) }
    }

    // =============================================
    // 状态管理
    // =============================================

    /**
     * 设置加载状态
     */
    fun setLoading(loading: Boolean) {
        _uiState.update { it.copy(isLoading = loading) }
    }

    /**
     * 设置错误信息
     */
    fun setError(errorMessage: String) {
        _uiState.update { it.copy(error = errorMessage) }
    }

    /**
     * 清除错误
     */
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }

    // =============================================
    // 辅助方法
    // =============================================

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
