/**
 * 播放列表选择模态框
 * 首次安装时让用户选择播放列表
 */
import React from 'react';
import { Modal, List, Button, Typography, Spin, Alert } from 'antd';
import { usePlaylistSelection, PlaylistInfo } from '../hooks/usePlaylistSelection';

const { Text } = Typography;

interface PlaylistSelectionModalProps {
    deviceId: string;
    visible: boolean;
    onCompleted: () => void;
}

export const PlaylistSelectionModal: React.FC<PlaylistSelectionModalProps> = ({
    deviceId,
    visible,
    onCompleted
}) => {
    const {
        availablePlaylists,
        selectedPlaylist: _selectedPlaylist,
        isLoading,
        isDownloading,
        error,
        selectPlaylist,
        skipSelection
    } = usePlaylistSelection(deviceId);

    const handleSelect = async (playlist: PlaylistInfo) => {
        await selectPlaylist(playlist);
        onCompleted();
    };

    const handleSkip = () => {
        skipSelection();
        onCompleted();
    };

    return (
        <Modal
            title="选择播放列表"
            open={visible && !isDownloading}
            footer={[
                <Button key="skip" onClick={handleSkip}>
                    稍后再说
                </Button>,
            ]}
            closable={false}
            width={500}
        >
            {isLoading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                    <p style={{ marginTop: 16 }}>正在加载播放列表...</p>
                </div>
            ) : error ? (
                <Alert
                    message={error}
                    type="warning"
                    showIcon
                    action={
                        <Button size="small" onClick={handleSkip}>
                            使用默认播放列表
                        </Button>
                    }
                />
            ) : (
                <>
                    <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                        请选择一个播放列表进行下载，也可以稍后再说
                    </Text>

                    <List
                        dataSource={availablePlaylists}
                        loading={isLoading}
                        renderItem={(playlist) => (
                            <List.Item
                                actions={[
                                    <Button
                                        type="primary"
                                        size="small"
                                        onClick={() => handleSelect(playlist)}
                                        disabled={isDownloading}
                                    >
                                        选择
                                    </Button>
                                ]}
                            >
                                <List.Item.Meta
                                    title={<Text strong>{playlist.name}</Text>}
                                    description={
                                        <Text type="secondary">
                                            {playlist.media_count}个媒体 • {(playlist.total_size_mb / 1024).toFixed(2)} GB
                                        </Text>
                                    }
                                />
                            </List.Item>
                        )}
                        locale={{ emptyText: '暂无可用播放列表' }}
                    />
                </>
            )}
        </Modal>
    );
};
