package com.castplay.player.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.castplay.player.data.db.entity.MediaFileEntity
import com.castplay.player.data.db.entity.PlaylistEntity
import com.castplay.player.data.model.RegisterResponse
import com.castplay.player.data.repository.DeviceRepository
import com.castplay.player.data.repository.MediaRepository
import com.castplay.player.data.repository.PlaylistRepository
import com.castplay.player.data.repository.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 播放器 ViewModel
 *
 * 使用 Hilt 注入，管理播放器的 UI 状态
 */
@HiltViewModel
class PlayerViewModel @Inject constructor(
    private val deviceRepository: DeviceRepository,
    private val mediaRepository: MediaRepository,
    private val playlistRepository: PlaylistRepository
) : ViewModel() {

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

    // 当前播放状态
    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    init {
        // 初始化时加载保存的设备 ID
        _deviceId.value = deviceRepository.getSavedDeviceId()
    }

    /**
     * 注册设备
     */
    fun registerDevice(deviceName: String? = null) {
        viewModelScope.launch {
            deviceRepository.registerDevice(deviceName = deviceName).collect { resource ->
                _registrationState.value = resource

                if (resource is Resource.Success) {
                    _deviceId.value = resource.data.device.deviceId
                }
            }
        }
    }

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
     * 设置播放状态
     */
    fun setPlayingState(isPlaying: Boolean) {
        _isPlaying.value = isPlaying
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
}
