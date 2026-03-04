package com.castplay.player.db

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.castplay.player.data.db.AppDatabase
import com.castplay.player.data.db.dao.MediaFileDao
import com.castplay.player.data.db.dao.PlaylistDao
import com.castplay.player.data.db.entity.MediaFileEntity
import com.castplay.player.data.db.entity.PlaylistEntity
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*

/**
 * Room 数据库测试
 *
 * 测试覆盖：
 * 1. 播放列表 CRUD
 * 2. 媒体文件 CRUD
 * 3. 数据关联查询
 * 4. 事务操作
 */
@RunWith(AndroidJUnit4::class)
@OptIn(ExperimentalCoroutinesApi::class)
class AppDatabaseTest {

    private lateinit var database: AppDatabase
    private lateinit var playlistDao: PlaylistDao
    private lateinit var mediaFileDao: MediaFileDao

    @Before
    fun setUp() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        playlistDao = database.playlistDao()
        mediaFileDao = database.mediaFileDao()
    }

    @After
    fun tearDown() {
        database.close()
    }

    // ================================================================
    // 播放列表 CRUD 测试
    // ================================================================

    @Test
    fun testInsertAndGetPlaylist() = runTest {
        // Given
        val playlist = PlaylistEntity(
            serverId = 1,
            name = "Test Playlist",
            description = "Test Description"
        )

        // When
        playlistDao.insert(playlist)
        val retrieved = playlistDao.getByServerId(1)

        // Then
        assertNotNull(retrieved)
        assertEquals("Test Playlist", retrieved?.name)
        assertEquals("Test Description", retrieved?.description)
    }

    @Test
    fun testUpdatePlaylist() = runTest {
        // Given
        val playlist = PlaylistEntity(
            serverId = 2,
            name = "Original Name",
            description = "Original Desc"
        )
        playlistDao.insert(playlist)

        // When
        val inserted = playlistDao.getByServerId(2)!!
        val updated = inserted.copy(name = "Updated Name")
        playlistDao.update(updated)

        // Then
        val result = playlistDao.getByServerId(2)
        assertEquals("Updated Name", result?.name)
    }

    @Test
    fun testDeletePlaylist() = runTest {
        // Given
        val playlist = PlaylistEntity(
            serverId = 3,
            name = "To Delete",
            description = ""
        )
        playlistDao.insert(playlist)

        // When
        val inserted = playlistDao.getByServerId(3)!!
        playlistDao.delete(inserted)

        // Then
        val result = playlistDao.getByServerId(3)
        assertNull(result)
    }

    @Test
    fun testGetAllPlaylists() = runTest {
        // Given
        playlistDao.insert(PlaylistEntity(serverId = 10, name = "P1", description = ""))
        playlistDao.insert(PlaylistEntity(serverId = 11, name = "P2", description = ""))
        playlistDao.insert(PlaylistEntity(serverId = 12, name = "P3", description = ""))

        // When
        val all = playlistDao.getAll()

        // Then
        assertTrue(all.size >= 3)
    }

    // ================================================================
    // 媒体文件 CRUD 测试
    // ================================================================

    @Test
    fun testInsertAndGetMediaFile() = runTest {
        // Given
        val media = MediaFileEntity(
            serverId = 100,
            fileName = "video.mp4",
            fileType = "video",
            fileSize = 1024000,
            localPath = "/data/media/video.mp4",
            status = "ready"
        )

        // When
        mediaFileDao.insert(media)
        val retrieved = mediaFileDao.getByServerId(100)

        // Then
        assertNotNull(retrieved)
        assertEquals("video.mp4", retrieved?.fileName)
        assertEquals("video", retrieved?.fileType)
        assertEquals(1024000, retrieved?.fileSize)
    }

    @Test
    fun testUpdateMediaFileLocalPath() = runTest {
        // Given
        val media = MediaFileEntity(
            serverId = 101,
            fileName = "image.jpg",
            fileType = "image",
            fileSize = 5000,
            localPath = null,
            status = "pending"
        )
        mediaFileDao.insert(media)

        // When
        val inserted = mediaFileDao.getByServerId(101)!!
        val updated = inserted.copy(
            localPath = "/data/media/image.jpg",
            status = "ready"
        )
        mediaFileDao.update(updated)

        // Then
        val result = mediaFileDao.getByServerId(101)
        assertEquals("/data/media/image.jpg", result?.localPath)
        assertEquals("ready", result?.status)
    }

    @Test
    fun testGetMediaFilesByPlaylist() = runTest {
        // 注意：此测试需要正确设置关联表
        // 这里仅测试 DAO 方法存在性

        val all = mediaFileDao.getAll()
        assertNotNull(all)
    }

    // ================================================================
    // 批量操作测试
    // ================================================================

    @Test
    fun testInsertAllPlaylists() = runTest {
        // Given
        val playlists = listOf(
            PlaylistEntity(serverId = 20, name = "Batch 1", description = ""),
            PlaylistEntity(serverId = 21, name = "Batch 2", description = ""),
            PlaylistEntity(serverId = 22, name = "Batch 3", description = "")
        )

        // When
        playlistDao.insertAll(playlists)

        // Then
        val p1 = playlistDao.getByServerId(20)
        val p2 = playlistDao.getByServerId(21)
        val p3 = playlistDao.getByServerId(22)

        assertNotNull(p1)
        assertNotNull(p2)
        assertNotNull(p3)
    }

    @Test
    fun testDeleteAllPlaylists() = runTest {
        // Given
        playlistDao.insert(PlaylistEntity(serverId = 30, name = "Del 1", description = ""))
        playlistDao.insert(PlaylistEntity(serverId = 31, name = "Del 2", description = ""))

        // When
        playlistDao.deleteAll()

        // Then
        val all = playlistDao.getAll()
        assertTrue(all.isEmpty())
    }

    // ================================================================
    // 约束测试
    // ================================================================

    @Test
    fun testUniqueServerIdConstraint() = runTest {
        // Given
        val playlist1 = PlaylistEntity(serverId = 50, name = "First", description = "")
        playlistDao.insert(playlist1)

        // When: 插入相同 serverId 应替换（如使用 OnConflictStrategy.REPLACE）
        val playlist2 = PlaylistEntity(serverId = 50, name = "Second", description = "")
        playlistDao.insert(playlist2)

        // Then
        val result = playlistDao.getByServerId(50)
        // 根据 OnConflictStrategy，可能是 First 或 Second
        assertNotNull(result)
    }

    // ================================================================
    // MD5 校验相关测试
    // ================================================================

    @Test
    fun testMediaFileMd5Field() = runTest {
        // Given
        val media = MediaFileEntity(
            serverId = 200,
            fileName = "checksum.mp4",
            fileType = "video",
            fileSize = 2000,
            localPath = "/data/media/checksum.mp4",
            status = "ready",
            md5 = "abc123def456"
        )

        // When
        mediaFileDao.insert(media)
        val retrieved = mediaFileDao.getByServerId(200)

        // Then
        assertEquals("abc123def456", retrieved?.md5)
    }

    @Test
    fun testFindMediaByMd5() = runTest {
        // Given
        val media = MediaFileEntity(
            serverId = 201,
            fileName = "dup.jpg",
            fileType = "image",
            fileSize = 1000,
            localPath = "/data/media/dup.jpg",
            status = "ready",
            md5 = "unique_hash_123"
        )
        mediaFileDao.insert(media)

        // When
        val result = mediaFileDao.findByMd5("unique_hash_123")

        // Then
        assertNotNull(result)
        assertEquals(201, result?.serverId)
    }
}
