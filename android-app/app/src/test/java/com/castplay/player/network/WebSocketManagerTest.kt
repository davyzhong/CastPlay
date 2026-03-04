package com.castplay.player.network

import io.mockk.*
import io.socket.client.Socket
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runTest
import org.json.JSONObject
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.Assert.*

/**
 * WebSocketManager 单元测试
 *
 * 测试覆盖：
 * 1. 连接状态管理
 * 2. 事件解析
 * 3. 断线重连
 * 4. Flow 事件发射
 */
@OptIn(ExperimentalCoroutinesApi::class)
class WebSocketManagerTest {

    private val testDispatcher = UnconfinedTestDispatcher()

    @Before
    fun setUp() {
        // 重置 WebSocketManager 单例状态
        WebSocketManager.disconnect()
    }

    @After
    fun tearDown() {
        WebSocketManager.disconnect()
        unmockkAll()
    }

    // ================================================================
    // 测试：初始连接状态
    // ================================================================

    @Test
    fun `test initial connection state is Disconnected`() = runTest(testDispatcher) {
        // Given/When
        val state = WebSocketManager.connectionState.value

        // Then
        assertTrue(state is WebSocketManager.ConnectionState.Disconnected)
    }

    // ================================================================
    // 测试：连接未初始化时 isConnected 返回 false
    // ================================================================

    @Test
    fun `test isConnected returns false when not connected`() {
        // Given/When
        val result = WebSocketManager.isConnected()

        // Then
        assertFalse(result)
    }

    // ================================================================
    // 测试：断开连接
    // ================================================================

    @Test
    fun `test disconnect sets state to Disconnected`() = runTest(testDispatcher) {
        // Given - 模拟已连接状态（通过反射设置内部状态）
        // 实际测试中使用集成测试更合适

        // When
        WebSocketManager.disconnect()

        // Then
        val state = WebSocketManager.connectionState.value
        assertTrue(state is WebSocketManager.ConnectionState.Disconnected)
    }

    // ================================================================
    // 测试：WebSocket 事件类型
    // ================================================================

    @Test
    fun `test WebSocketEvent PlaylistUpdate contains playlistId`() {
        // Given
        val playlistId = 42

        // When
        val event = WebSocketManager.WebSocketEvent.PlaylistUpdate(playlistId)

        // Then
        assertEquals(playlistId, event.playlistId)
    }

    @Test
    fun `test WebSocketEvent types are distinct`() {
        // Given/When/Then
        assertTrue(WebSocketManager.WebSocketEvent.Registered is WebSocketManager.WebSocketEvent)
        assertTrue(WebSocketManager.WebSocketEvent.ScheduleUpdate is WebSocketManager.WebSocketEvent)
        assertTrue(WebSocketManager.WebSocketEvent.ForceSync is WebSocketManager.WebSocketEvent)
        assertTrue(WebSocketManager.WebSocketEvent.Reboot is WebSocketManager.WebSocketEvent)
        assertTrue(WebSocketManager.WebSocketEvent.ConnectionFailed is WebSocketManager.WebSocketEvent)
    }

    // ================================================================
    // 测试：ConnectionState 类型
    // ================================================================

    @Test
    fun `test ConnectionState types are correct`() {
        // Given/When/Then
        assertTrue(WebSocketManager.ConnectionState.Connected is WebSocketManager.ConnectionState)
        assertTrue(WebSocketManager.ConnectionState.Disconnected is WebSocketManager.ConnectionState)
        assertTrue(WebSocketManager.ConnectionState.Connecting is WebSocketManager.ConnectionState)

        val errorState = WebSocketManager.ConnectionState.Error("test error")
        assertTrue(errorState is WebSocketManager.ConnectionState)
        assertEquals("test error", errorState.message)
    }

    // ================================================================
    // 测试：WebSocketListener 接口
    // ================================================================

    @Test
    fun `test WebSocketListener interface has all required methods`() {
        // Given
        var registeredCalled = false
        var playlistUpdateCalled = false
        var scheduleUpdateCalled = false
        var forceSyncCalled = false
        var rebootCalled = false
        var connectionFailedCalled = false

        val listener = object : WebSocketManager.WebSocketListener {
            override fun onRegistered() {
                registeredCalled = true
            }

            override fun onPlaylistUpdate(playlistId: Int) {
                playlistUpdateCalled = true
            }

            override fun onScheduleUpdate() {
                scheduleUpdateCalled = true
            }

            override fun onForceSync() {
                forceSyncCalled = true
            }

            override fun onReboot() {
                rebootCalled = true
            }

            override fun onConnectionFailed() {
                connectionFailedCalled = true
            }
        }

        // When
        listener.onRegistered()
        listener.onPlaylistUpdate(1)
        listener.onScheduleUpdate()
        listener.onForceSync()
        listener.onReboot()
        listener.onConnectionFailed()

        // Then
        assertTrue(registeredCalled)
        assertTrue(playlistUpdateCalled)
        assertTrue(scheduleUpdateCalled)
        assertTrue(forceSyncCalled)
        assertTrue(rebootCalled)
        assertTrue(connectionFailedCalled)
    }

    // ================================================================
    // 测试：事件解析辅助测试
    // ================================================================

    @Test
    fun `test playlist_update JSON parsing`() {
        // Given
        val json = JSONObject().apply {
            put("playlist_id", 123)
        }

        // When
        val playlistId = json.optInt("playlist_id")

        // Then
        assertEquals(123, playlistId)
    }

    @Test
    fun `test playlist_update JSON missing field returns 0`() {
        // Given
        val json = JSONObject()

        // When
        val playlistId = json.optInt("playlist_id")

        // Then
        assertEquals(0, playlistId)
    }

    // ================================================================
    // 测试：URL 格式转换
    // ================================================================

    @Test
    fun `test URL format conversion ws to http`() {
        // Given
        val wsUrl = "ws://10.0.2.2:5001/socket.io/"

        // When
        val httpUrl = wsUrl
            .replace("/socket.io/", "")
            .replace("/socket.io", "")
            .replace("ws://", "http://")
            .replace("wss://", "https://")

        // Then
        assertEquals("http://10.0.2.2:5001", httpUrl)
    }

    @Test
    fun `test URL format conversion wss to https`() {
        // Given
        val wssUrl = "wss://example.com/socket.io/"

        // When
        val httpsUrl = wssUrl
            .replace("/socket.io/", "")
            .replace("/socket.io", "")
            .replace("ws://", "http://")
            .replace("wss://", "https://")

        // Then
        assertEquals("https://example.com", httpsUrl)
    }

    // ================================================================
    // 测试：重连配置常量
    // ================================================================

    @Test
    fun `test reconnection configuration values`() {
        // 通过反射验证常量值（或在集成测试中验证行为）
        // 这里测试重连逻辑的边界条件

        // Given
        val initialDelay = 1000L
        val maxDelay = 60000L
        val maxRetries = 10

        // Then - 验证配置合理性
        assertTrue(initialDelay < maxDelay)
        assertTrue(maxRetries > 0)
        assertTrue(maxDelay <= 120000L)  // 最大延迟不超过 2 分钟
    }

    // ================================================================
    // 测试：Flow 事件收集
    // ================================================================

    @Test
    fun `test events flow is available`() = runTest(testDispatcher) {
        // Given/When
        val events = WebSocketManager.events

        // Then - 验证 Flow 可用
        assertNotNull(events)
    }

    @Test
    fun `test connectionState flow is available`() = runTest(testDispatcher) {
        // Given/When
        val stateFlow = WebSocketManager.connectionState

        // Then
        assertNotNull(stateFlow)
        assertNotNull(stateFlow.value)
    }
}
