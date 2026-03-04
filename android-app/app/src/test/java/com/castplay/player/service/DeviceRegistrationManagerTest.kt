package com.castplay.player.service

import android.content.Context
import android.content.SharedPreferences
import com.castplay.player.data.model.RegisterResponse
import com.castplay.player.data.model.RegisterResponse.DeviceInfo
import com.castplay.player.network.ApiService
import com.castplay.player.network.RetrofitClient
import io.mockk.*
import io.mockk.impl.annotations.MockK
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import org.junit.Assert.*

/**
 * DeviceRegistrationManager 单元测试
 *
 * 测试覆盖：
 * 1. 首次注册成功场景
 * 2. 重复注册（恢复已有设备）场景
 * 3. 注册失败场景
 * 4. 本地缓存管理
 */
@OptIn(ExperimentalCoroutinesApi::class)
class DeviceRegistrationManagerTest {

    @MockK
    private lateinit var mockContext: Context

    @MockK
    private lateinit var mockAppContext: Context

    @MockK
    private lateinit var mockPrefs: SharedPreferences

    @MockK
    private lateinit var mockEditor: SharedPreferences.Editor

    @MockK
    private lateinit var mockApiService: ApiService

    @MockK
    private lateinit var mockCall: Call<RegisterResponse>

    private lateinit var registrationManager: DeviceRegistrationManager

    @Before
    fun setUp() {
        MockKAnnotations.init(this, relaxed = true)

        // Mock Context
        every { mockContext.applicationContext } returns mockAppContext
        every { mockAppContext.getSharedPreferences(any(), any()) } returns mockPrefs
        every { mockAppContext.contentResolver } returns mockk(relaxed = true)

        // Mock SharedPreferences
        every { mockPrefs.getString(any(), any()) } returns null
        every { mockPrefs.getInt(any(), any()) } returns -1
        every { mockPrefs.edit() } returns mockEditor
        every { mockEditor.putString(any(), any()) } returns mockEditor
        every { mockEditor.putInt(any(), any()) } returns mockEditor
        every { mockEditor.apply() } just Runs

        // Mock RetrofitClient
        mockkObject(RetrofitClient)
        every { RetrofitClient.getApiService() } returns mockApiService
        every { mockApiService.registerDevice(any()) } returns mockCall
    }

    @After
    fun tearDown() {
        unmockkAll()
    }

    // ================================================================
    // 测试：首次注册成功
    // ================================================================

    @Test
    fun `test first registration success returns new device id`() {
        // Given: 首次注册，无缓存 ID
        every { mockPrefs.getString("device_id", null) } returns null

        val expectedDeviceId = "CAS-A1B2"
        val mockResponse = RegisterResponse(
            message = "success",
            device = DeviceInfo(
                id = 1,
                deviceId = expectedDeviceId,
                deviceName = "Test Device",
                hardwareId = null,
                timezone = "Asia/Shanghai",
                status = "online",
                lastOnline = null
            ),
            isNew = true
        )

        // 模拟 API 成功响应
        every { mockCall.enqueue(any()) } answers {
            val callback = firstArg<Callback<RegisterResponse>>()
            callback.onResponse(mockCall, Response.success(mockResponse))
        }

        // When
        var resultDeviceId: String? = null
        var resultIsNew: Boolean? = null

        registrationManager = DeviceRegistrationManager(mockContext)
        registrationManager.register(object : DeviceRegistrationManager.RegistrationCallback {
            override fun onRegistrationSuccess(deviceId: String, isNew: Boolean) {
                resultDeviceId = deviceId
                resultIsNew = isNew
            }

            override fun onRegistrationFailed(error: String) {
                fail("Should not fail: $error")
            }
        })

        // Then
        assertEquals(expectedDeviceId, resultDeviceId)
        assertTrue(resultIsNew == true)

        // 验证 ID 被缓存
        verify { mockEditor.putString("device_id", expectedDeviceId) }
        verify { mockEditor.putInt("server_device_id", 1) }
        verify { mockEditor.apply() }
    }

    // ================================================================
    // 测试：重复注册（同 hardware_id 恢复设备）
    // ================================================================

    @Test
    fun `test repeated registration with same hardware_id returns existing device`() {
        // Given: 有缓存 ID
        val existingDeviceId = "CAS-X9Y8"
        every { mockPrefs.getString("device_id", null) } returns existingDeviceId

        val mockResponse = RegisterResponse(
            message = "success",
            device = DeviceInfo(
                id = 5,
                deviceId = existingDeviceId,
                deviceName = "Existing Device",
                hardwareId = null,
                timezone = "Asia/Shanghai",
                status = "online",
                lastOnline = null
            ),
            isNew = false  // 非新注册
        )

        every { mockCall.enqueue(any()) } answers {
            val callback = firstArg<Callback<RegisterResponse>>()
            callback.onResponse(mockCall, Response.success(mockResponse))
        }

        // When
        var resultIsNew: Boolean? = null

        registrationManager = DeviceRegistrationManager(mockContext)
        registrationManager.register(object : DeviceRegistrationManager.RegistrationCallback {
            override fun onRegistrationSuccess(deviceId: String, isNew: Boolean) {
                resultIsNew = isNew
            }

            override fun onRegistrationFailed(error: String) {
                fail("Should not fail")
            }
        })

        // Then
        assertFalse(resultIsNew == true)  // isNew 应为 false
    }

    // ================================================================
    // 测试：服务器返回错误
    // ================================================================

    @Test
    fun `test registration fails when server returns error`() {
        // Given: 服务器返回 500 错误
        val errorResponse = Response.error<RegisterResponse>(
            500,
            okhttp3.ResponseBody.create(null, "Server Error")
        )

        every { mockCall.enqueue(any()) } answers {
            val callback = firstArg<Callback<RegisterResponse>>()
            callback.onResponse(mockCall, errorResponse)
        }

        // When
        var errorMessage: String? = null

        registrationManager = DeviceRegistrationManager(mockContext)
        registrationManager.register(object : DeviceRegistrationManager.RegistrationCallback {
            override fun onRegistrationSuccess(deviceId: String, isNew: Boolean) {
                fail("Should not succeed")
            }

            override fun onRegistrationFailed(error: String) {
                errorMessage = error
            }
        })

        // Then
        assertNotNull(errorMessage)
        assertTrue(errorMessage!!.contains("500"))
    }

    // ================================================================
    // 测试：网络错误
    // ================================================================

    @Test
    fun `test registration fails on network error`() {
        // Given: 网络异常
        val networkError = java.net.UnknownHostException("No network")

        every { mockCall.enqueue(any()) } answers {
            val callback = firstArg<Callback<RegisterResponse>>()
            callback.onFailure(mockCall, networkError)
        }

        // When
        var errorMessage: String? = null

        registrationManager = DeviceRegistrationManager(mockContext)
        registrationManager.register(object : DeviceRegistrationManager.RegistrationCallback {
            override fun onRegistrationSuccess(deviceId: String, isNew: Boolean) {
                fail("Should not succeed")
            }

            override fun onRegistrationFailed(error: String) {
                errorMessage = error
            }
        })

        // Then
        assertNotNull(errorMessage)
        assertTrue(errorMessage!!.contains("No network"))
    }

    // ================================================================
    // 测试：本地缓存
    // ================================================================

    @Test
    fun `test getCachedDeviceId returns cached value`() {
        // Given
        val cachedId = "CAS-CACHED"
        every { mockPrefs.getString("device_id", null) } returns cachedId

        // When
        registrationManager = DeviceRegistrationManager(mockContext)
        val result = registrationManager.getCachedDeviceId()

        // Then
        assertEquals(cachedId, result)
    }

    @Test
    fun `test isRegistered returns true when device id is cached`() {
        // Given
        every { mockPrefs.getString("device_id", null) } returns "CAS-TEST"

        // When
        registrationManager = DeviceRegistrationManager(mockContext)
        val result = registrationManager.isRegistered()

        // Then
        assertTrue(result)
    }

    @Test
    fun `test isRegistered returns false when no cached device id`() {
        // Given
        every { mockPrefs.getString("device_id", null) } returns null

        // When
        registrationManager = DeviceRegistrationManager(mockContext)
        val result = registrationManager.isRegistered()

        // Then
        assertFalse(result)
    }

    // ================================================================
    // 测试：协程版本注册
    // ================================================================

    @Test
    fun `test registerAsync success`() = runTest {
        // Given
        val expectedDeviceId = "CAS-ASYNC"
        val mockResponse = RegisterResponse(
            message = "success",
            device = DeviceInfo(
                id = 10,
                deviceId = expectedDeviceId,
                deviceName = "Async Device",
                hardwareId = null,
                timezone = "Asia/Shanghai",
                status = "online",
                lastOnline = null
            ),
            isNew = true
        )

        coEvery { mockApiService.registerDeviceAsync(any()) } returns Response.success(mockResponse)

        // When
        registrationManager = DeviceRegistrationManager(mockContext)
        val result = registrationManager.registerAsync()

        // Then
        assertTrue(result.isSuccess)
        val (deviceId, isNew) = result.getOrThrow()
        assertEquals(expectedDeviceId, deviceId)
        assertTrue(isNew)
    }

    @Test
    fun `test registerAsync failure`() = runTest {
        // Given
        coEvery { mockApiService.registerDeviceAsync(any()) } returns Response.error(
            500,
            okhttp3.ResponseBody.create(null, "")
        )

        // When
        registrationManager = DeviceRegistrationManager(mockContext)
        val result = registrationManager.registerAsync()

        // Then
        assertTrue(result.isFailure)
    }
}
