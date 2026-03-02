package com.castplay.player.data.db.dao;

import androidx.room.*;
import com.castplay.player.data.db.entity.MediaFileEntity;
import java.util.List;

/**
 * 媒体文件 DAO
 */
@Dao
public interface MediaFileDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insert(MediaFileEntity mediaFile);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertAll(List<MediaFileEntity> mediaFiles);

    @Update
    void update(MediaFileEntity mediaFile);

    @Delete
    void delete(MediaFileEntity mediaFile);

    @Query("SELECT * FROM media_file WHERE playlistId = :playlistId ORDER BY displayOrder ASC")
    List<MediaFileEntity> getByPlaylistId(int playlistId);

    @Query("SELECT * FROM media_file WHERE isDownloaded = 0")
    List<MediaFileEntity> getPendingDownloads();

    @Query("SELECT DISTINCT playlistId FROM media_file ORDER BY playlistId ASC")
    List<Integer> getAllPlaylistIds();

    @Query("DELETE FROM media_file WHERE playlistId NOT IN (:activePlaylistIds)")
    void deleteInactivePlaylists(List<Integer> activePlaylistIds);

    @Query("DELETE FROM media_file")
    void deleteAll();
}
