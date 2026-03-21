/**
 * 播放列表选择模态框
 * 支持多选、全选/取消全选、至少保留一个限制
 */
import React from 'react';
import { List, Button, Typography, Spin, Alert, Checkbox, Space, Divider } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { usePlaylistSelection, PlaylistInfo } from '../hooks/usePlaylistSelection';

const { Text, Title } = Typography;

interface PlaylistSelectionModalProps {
  deviceId: string | null;
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
    selectedIds,
    isLoading,
    error,
    toggleSelection,
    selectAll,
    deselectAll,
    confirmSelection,
    skipSelection,
  } = usePlaylistSelection(deviceId);

  // 处理确认
  const handleConfirm = () => {
    if (selectedIds.length === 0) {
      return;
    }
    confirmSelection();
    onCompleted();
  };

  // 处理跳过
  const handleSkip = () => {
    skipSelection();
    onCompleted();
  };

  // 检查是否全选
  const isAllSelected = availablePlaylists.length > 0 &&
    selectedIds.length === availablePlaylists.length;

  // 检查是否只剩一个
  const isLastOne = selectedIds.length === 1;

  if (!visible) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      zIndex: 999,
    }}>
      <div style={{
        maxWidth: 600,
        width: '90%',
        maxHeight: '80vh',
        background: 'white',
        borderRadius: 16,
        overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
      }}>
        {/* 标题 */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <Space>
            <Title level={4} style={{ margin: 0 }}>选择播放列表</Title>
            <Text type="secondary" style={{ fontSize: 14 }}>
              ({selectedIds.length}/{availablePlaylists.length} 已选)
            </Text>
          </Space>
        </div>

        {/* 内容 */}
        <div style={{ padding: 20, maxHeight: '50vh', overflow: 'auto' }}>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Spin size="large" />
              <p style={{ marginTop: 16, color: '#666' }}>正在加载播放列表...</p>
            </div>
          ) : error ? (
            <Alert
              message={error}
              type="warning"
              showIcon
              action={
                <Button size="small" onClick={handleSkip}>
                  使用全部播放列表
                </Button>
              }
            />
          ) : availablePlaylists.length === 0 ? (
            <Alert
              message="暂无可用播放列表"
              description="请联系管理员分配播放列表到当前设备"
              type="info"
              showIcon
            />
          ) : (
            <>
              {/* 说明文字 */}
              <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
                请选择要播放的播放列表。未选择的播放列表将不会进入播放序列。
              </Text>

              {/* 全选/取消全选按钮 */}
              <Space style={{ marginBottom: 12 }}>
                <Button
                  size="small"
                  icon={<CheckCircleOutlined />}
                  onClick={selectAll}
                  disabled={isAllSelected}
                >
                  全选
                </Button>
                <Button
                  size="small"
                  icon={<CloseCircleOutlined />}
                  onClick={deselectAll}
                  disabled={selectedIds.length <= 1}
                >
                  取消全选
                </Button>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  （至少保留一个播放列表）
                </Text>
              </Space>

              <Divider style={{ margin: '12px 0' }} />

              {/* 播放列表列表 */}
              <List
                dataSource={availablePlaylists}
                renderItem={(playlist: PlaylistInfo) => {
                  const isSelected = selectedIds.includes(playlist.id);
                  const isDisabled = isLastOne && isSelected;

                  return (
                    <List.Item
                      style={{
                        padding: '12px 16px',
                        background: isSelected ? '#e6f7ff' : 'transparent',
                        borderRadius: 8,
                        marginBottom: 8,
                        cursor: isDisabled ? 'not-allowed' : 'pointer',
                        transition: 'background 0.2s',
                      }}
                      onClick={() => {
                        if (!isDisabled) {
                          toggleSelection(playlist.id);
                        }
                      }}
                    >
                      <List.Item.Meta
                        avatar={
                          <Checkbox
                            checked={isSelected}
                            disabled={isDisabled}
                            onChange={(e) => {
                              e.stopPropagation();
                              if (!isDisabled) {
                                toggleSelection(playlist.id);
                              }
                            }}
                          />
                        }
                        title={
                          <Space>
                            <Text strong>{playlist.name}</Text>
                            {isSelected && (
                              <Text type="success" style={{ fontSize: 12 }}>
                                ✓ 已选
                              </Text>
                            )}
                          </Space>
                        }
                        description={
                          <Space split={<Text type="secondary">•</Text>}>
                            <Text type="secondary">
                              {playlist.media_count} 个媒体
                            </Text>
                            <Text type="secondary">
                              {(playlist.total_size_mb / 1024).toFixed(2)} GB
                            </Text>
                            {playlist.thumbnail_url && (
                              <img
                                src={playlist.thumbnail_url}
                                alt=""
                                style={{
                                  width: 40,
                                  height: 40,
                                  objectFit: 'cover',
                                  borderRadius: 4,
                                }}
                              />
                            )}
                          </Space>
                        }
                      />
                    </List.Item>
                  );
                }}
                locale={{ emptyText: '暂无可用播放列表' }}
              />

              {/* 底部提示 */}
              <Divider style={{ margin: '12px 0' }} />
              <Text type="secondary" style={{ fontSize: 12, display: 'block', textAlign: 'center' }}>
                💡 选择将自动保存，下次启动时恢复
              </Text>
            </>
          )}
        </div>

        {/* 底部按钮 */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
        }}>
          <Button onClick={handleSkip}>
            使用全部播放列表
          </Button>
          <Button
            type="primary"
            onClick={handleConfirm}
            disabled={selectedIds.length === 0 || isLoading}
          >
            确认选择
          </Button>
        </div>
      </div>
    </div>
  );
};

// 默认导出（兼容旧代码）
export default PlaylistSelectionModal;
