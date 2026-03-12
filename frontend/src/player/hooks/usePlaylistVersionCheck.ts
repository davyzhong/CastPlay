/**
 * 播放列表版本检查 Hook
 * 启动时和定期轮询检查播放列表是否有更新
 */
import { useEffect, useState } from 'react';
import axios from 'axios';

export const usePlaylistVersionCheck = (
    deviceId: string | null,
    playlistId: number | null,
    currentVersion: string | null
) => {
    const [needsUpdate, setNeedsUpdate] = useState(false);
    const [lastChecked, setLastChecked] = useState<Date | null>(null);

    useEffect(() => {
        if (!deviceId || !playlistId || !currentVersion) return;

        /**
         * 检查版本
         */
        const checkVersion = async () => {
            try {
                const response = await axios.post(`/api/player/playlist/${playlistId}/check`, {
                    version: currentVersion
                });

                setNeedsUpdate(response.data.needs_update);
                setLastChecked(new Date());

                if (response.data.needs_update) {
                    console.log('Playlist updated on server, need to refresh');
                    // 如果有更新，刷新页面重新加载
                    window.location.reload();
                }
            } catch (error) {
                console.debug('Version check failed (offline):', error);
            }
        };

        // 启动时检查一次
        checkVersion();

        // 每 30 分钟检查一次（可选）
        const interval = setInterval(checkVersion, 30 * 60 * 1000);
        return () => clearInterval(interval);
    }, [deviceId, playlistId, currentVersion]);

    return { needsUpdate, lastChecked };
};
