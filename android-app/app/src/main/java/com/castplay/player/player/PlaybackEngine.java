package com.castplay.player.player;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;

import com.bumptech.glide.Glide;
import com.bumptech.glide.load.resource.drawable.DrawableTransitionOptions;
import com.castplay.player.data.model.MediaItem;
import com.google.android.exoplayer2.ExoPlayer;
import com.google.android.exoplayer2.PlaybackException;
import com.google.android.exoplayer2.Player;
import com.google.android.exoplayer2.ui.StyledPlayerView;

import java.io.File;
import java.util.List;

/**
 * 播放引擎 - 混合媒体播放（图片+视频）
 */
public class PlaybackEngine {
    private static final String TAG = "PlaybackEngine";

    private Context context;
    private List<MediaItem> playlist;
    private int currentIndex = 0;
    private boolean isPlaying = false;
    private boolean isPaused = false;

    // UI 组件
    private ImageView imageView;
    private StyledPlayerView playerView;
    private ProgressBar progressBar;
    private TextView statusText;

    // 播放器
    private ExoPlayer exoPlayer;
    private Handler handler;
    private Runnable nextRunnable;

    // 回调接口
    private PlaybackCallback callback;

    public PlaybackEngine(Context context, ImageView imageView, StyledPlayerView playerView) {
        this.context = context;
        this.imageView = imageView;
        this.playerView = playerView;
        this.handler = new Handler(Looper.getMainLooper());

        initializePlayer();
    }

    /**
     * 设置进度显示组件
     */
    public void setProgressViews(ProgressBar progressBar, TextView statusText) {
        this.progressBar = progressBar;
        this.statusText = statusText;
    }

    /**
     * 设置回调
     */
    public void setCallback(PlaybackCallback callback) {
        this.callback = callback;
    }

    /**
     * 初始化播放器
     */
    private void initializePlayer() {
        exoPlayer = new ExoPlayer.Builder(context).build();
        playerView.setPlayer(exoPlayer);
        playerView.setUseController(false); // 隐藏控制器

        exoPlayer.addListener(new Player.Listener() {
            @Override
            public void onPlaybackStateChanged(int playbackState) {
                switch (playbackState) {
                    case Player.STATE_READY:
                        Log.d(TAG, "Video ready");
                        hideProgress();
                        break;
                    case Player.STATE_ENDED:
                        Log.d(TAG, "Video ended, playing next");
                        playNext();
                        break;
                    case Player.STATE_BUFFERING:
                        Log.d(TAG, "Buffering...");
                        showProgress("正在加载...");
                        break;
                }
            }

            @Override
            public void onPlayerError(PlaybackException error) {
                Log.e(TAG, "Player error: " + error.getMessage());
                hideProgress();
                // 出错时播放下一个
                handler.postDelayed(() -> playNext(), 2000);
            }
        });
    }

    /**
     * 设置播放列表
     */
    public void setPlaylist(List<MediaItem> playlist) {
        this.playlist = playlist;
        this.currentIndex = 0;
        Log.d(TAG, "Playlist set with " + (playlist != null ? playlist.size() : 0) + " items");
    }

    /**
     * 开始播放
     */
    public void play() {
        if (playlist == null || playlist.isEmpty()) {
            Log.w(TAG, "Playlist is empty");
            showEmptyState();
            return;
        }

        isPlaying = true;
        isPaused = false;
        playCurrent();
    }

    /**
     * 播放当前项
     */
    private void playCurrent() {
        if (!isPlaying || playlist == null || playlist.isEmpty()) {
            return;
        }

        // 取消之前的定时器
        cancelNextTimer();

        MediaItem item = playlist.get(currentIndex);
        Log.d(TAG, "Playing item " + currentIndex + ": " + item.getFileName() + " (" + item.getFileType() + ")");

        // 通知回调
        if (callback != null) {
            callback.onPlaybackStarted(currentIndex, item);
        }

        // 检查文件是否存在
        File file = new File(item.getFilePath());
        if (!file.exists()) {
            Log.e(TAG, "File not found: " + item.getFilePath());
            playNext();
            return;
        }

        String fileType = item.getFileType();
        if ("image".equals(fileType)) {
            playImage(item);
        } else if ("video".equals(fileType) || "ppt".equals(fileType)) {
            playVideo(item);
        } else {
            Log.w(TAG, "Unknown file type: " + fileType);
            playNext();
        }
    }

    /**
     * 播放图片
     */
    private void playImage(MediaItem item) {
        // 停止视频播放
        if (exoPlayer.isPlaying()) {
            exoPlayer.stop();
        }

        // 隐藏视频视图，显示图片视图
        playerView.setVisibility(View.GONE);
        imageView.setVisibility(View.VISIBLE);

        // 加载图片（淡入效果）
        Glide.with(context)
                .load(new File(item.getFilePath()))
                .transition(DrawableTransitionOptions.withCrossFade(500))
                .centerCrop()
                .into(imageView);

        // 定时切换到下一个
        int duration = item.getDisplayDuration() * 1000; // 转换为毫秒
        if (duration <= 0) {
            duration = 5000; // 默认5秒
        }
        
        nextRunnable = this::playNext;
        handler.postDelayed(nextRunnable, duration);
        
        Log.d(TAG, "Image will display for " + duration + "ms");
    }

    /**
     * 播放视频
     */
    private void playVideo(MediaItem item) {
        // 隐藏图片视图，显示视频视图
        imageView.setVisibility(View.GONE);
        playerView.setVisibility(View.VISIBLE);

        // 加载视频
        com.google.android.exoplayer2.MediaItem mediaItem = 
                com.google.android.exoplayer2.MediaItem.fromUri("file://" + item.getFilePath());
        exoPlayer.setMediaItem(mediaItem);
        exoPlayer.prepare();
        exoPlayer.play();
        
        Log.d(TAG, "Video playback started: " + item.getFilePath());
    }

    /**
     * 播放下一个
     */
    private void playNext() {
        if (!isPlaying || playlist == null || playlist.isEmpty()) {
            return;
        }

        currentIndex = (currentIndex + 1) % playlist.size();
        Log.d(TAG, "Moving to next item: " + currentIndex);
        playCurrent();
    }

    /**
     * 取消下一个定时器
     */
    private void cancelNextTimer() {
        if (nextRunnable != null) {
            handler.removeCallbacks(nextRunnable);
            nextRunnable = null;
        }
    }

    /**
     * 暂停播放
     */
    public void pause() {
        isPaused = true;
        if (exoPlayer != null && exoPlayer.isPlaying()) {
            exoPlayer.pause();
        }
        cancelNextTimer();
        Log.d(TAG, "Playback paused");
    }

    /**
     * 恢复播放
     */
    public void resume() {
        if (!isPaused) {
            return;
        }
        
        isPaused = false;
        MediaItem currentItem = getCurrentItem();
        
        if (currentItem != null) {
            String fileType = currentItem.getFileType();
            if ("video".equals(fileType) || "ppt".equals(fileType)) {
                // 视频继续播放
                if (exoPlayer != null && !exoPlayer.isPlaying()) {
                    exoPlayer.play();
                }
            } else {
                // 图片重新开始定时
                int remaining = currentItem.getDisplayDuration() * 1000;
                nextRunnable = this::playNext;
                handler.postDelayed(nextRunnable, remaining);
            }
        }
        
        Log.d(TAG, "Playback resumed");
    }

    /**
     * 获取当前播放项
     */
    public MediaItem getCurrentItem() {
        if (playlist != null && currentIndex >= 0 && currentIndex < playlist.size()) {
            return playlist.get(currentIndex);
        }
        return null;
    }

    /**
     * 停止播放
     */
    public void stop() {
        isPlaying = false;
        isPaused = false;
        
        if (exoPlayer != null) {
            exoPlayer.stop();
        }
        cancelNextTimer();
        currentIndex = 0;
        
        Log.d(TAG, "Playback stopped");
    }

    /**
     * 释放资源
     */
    public void release() {
        isPlaying = false;
        isPaused = false;
        
        if (exoPlayer != null) {
            exoPlayer.release();
            exoPlayer = null;
        }
        cancelNextTimer();
        handler.removeCallbacksAndMessages(null);
        
        Log.d(TAG, "PlaybackEngine released");
    }

    /**
     * 显示加载进度
     */
    private void showProgress(String message) {
        if (progressBar != null) {
            progressBar.setVisibility(View.VISIBLE);
        }
        if (statusText != null) {
            statusText.setText(message);
            statusText.setVisibility(View.VISIBLE);
        }
    }

    /**
     * 隐藏加载进度
     */
    private void hideProgress() {
        if (progressBar != null) {
            progressBar.setVisibility(View.GONE);
        }
        if (statusText != null) {
            statusText.setVisibility(View.GONE);
        }
    }

    /**
     * 显示空状态
     */
    private void showEmptyState() {
        imageView.setVisibility(View.GONE);
        playerView.setVisibility(View.GONE);
        
        if (statusText != null) {
            statusText.setText("暂无播放内容");
            statusText.setVisibility(View.VISIBLE);
        }
    }

    /**
     * 播放回调接口
     */
    public interface PlaybackCallback {
        void onPlaybackStarted(int index, MediaItem item);
        void onPlaybackCompleted();
        void onPlaybackError(String error);
    }
}
