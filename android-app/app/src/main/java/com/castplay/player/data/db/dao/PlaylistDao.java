package com.castplay.player.data.db.dao;

import androidx.room.*;
import com.castplay.player.data.db.entity.PlaylistEntity;
import java.util.List;

/**
 * 播放列表 DAO
 */
@Dao
public interface PlaylistDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insert(PlaylistEntity playlist);

    @Update
    void update(PlaylistEntity playlist);

    @Delete
    void delete(PlaylistEntity playlist);

    @Query("SELECT * FROM playlist")
    List<PlaylistEntity> getAll();

    @Query("SELECT * FROM playlist WHERE id = :id")
    PlaylistEntity getById(int id);

    @Query("DELETE FROM playlist")
    void deleteAll();
}
