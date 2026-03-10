/**
 * 播放列表页面
 * 支持批量添加媒体、拖拽排序、媒体预览、播放列表预览
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  InputNumber,
  Select,
  Card,
  Typography,
  Tag,
  App,
  Image,
  Popconfirm,
  Row,
  Col,
  Tooltip,
  Checkbox,
  Input,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  HolderOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  CloseCircleOutlined,
  DesktopOutlined,
  LoadingOutlined,
  CheckOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type {
  Playlist,
  PlaylistDetail,
  Device,
  PlaylistItem,
  MediaFile,
  DeviceAssignment,
} from '../types';
import {
  getPlaylistList,
  createPlaylist,
  getPlaylistDetail,
  deletePlaylist,
  removeItemFromPlaylist,
  assignPlaylistToDevice,
  unassignPlaylistFromDevice,
  reorderPlaylistItems,
  addItemsToPlaylistBatch,
  updatePlaylistItem,
  updatePlaylist,
} from '../api/playlist';
import { getMediaList, getMediaFileUrl, getThumbnail } from '../api/media';
import { getDeviceList } from '../api/device';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const { Title } = Typography;

// 可拖拽的行组件
interface SortableRowProps {
  item: PlaylistItem;
  onRemove: (id: number) => void;
  mediaFiles: MediaFile[];
  onUpdateDuration: (itemId: number, duration: number) => void;
  updatingItemId: number | null;
}

const SortablePlaylistItem: React.FC<SortableRowProps> = ({
  item,
  onRemove,
  mediaFiles,
  onUpdateDuration,
  updatingItemId
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    display: 'flex',
    alignItems: 'center',
    padding: '12px',
    borderBottom: '1px solid #f0f0f0',
    backgroundColor: isDragging ? '#fafafa' : 'white',
  };

  const getFileTypeColor = (type: string) => {
    switch (type) {
      case 'image': return 'green';
      case 'video': return 'blue';
      case 'ppt': return 'orange';
      default: return 'default';
    }
  };

  // 根据 media_id 查找对应的媒体信息（用于缩略图）
  const media = mediaFiles.find(m => m.id === item.media_id);
  const isUpdating = updatingItemId === item.id;

  // 渲染缩略图
  const renderThumbnail = () => {
    if (media?.thumbnail_path) {
      return (
        <Image
          src={media.thumbnail_path}
          alt={item.file_name}
          width={160}
          height={120}
          style={{ borderRadius: 4, objectFit: 'cover' }}
          fallback={`data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='120' viewBox='0 0 160 120'%3E%3Crect fill='%23f0f0f0' width='160' height='120'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E加载失败%3C/text%3E%3C/svg%3E`}
          preview={{
            src: media.file_type === 'image' ? getMediaFileUrl(media.id) : undefined,
          }}
        />
      );
    }

    // 无缩略图时显示类型图标占位符
    const typeConfig: Record<string, { color: string; icon: string }> = {
      image: { color: '#52c41a', icon: '🖼️' },
      video: { color: '#1890ff', icon: '🎬' },
      ppt: { color: '#fa8c16', icon: '📊' },
    };
    const config = typeConfig[item.file_type] || { color: '#999', icon: '📄' };

    return (
      <div
        style={{
          width: 160,
          height: 120,
          backgroundColor: config.color,
          borderRadius: 4,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '40px',
          color: '#fff',
        }}
        title={item.file_name}
      >
        {config.icon}
      </div>
    );
  };

  return (
    <div ref={setNodeRef} style={style}>
      {/* 拖拽手柄 */}
      <div {...attributes} {...listeners} style={{ cursor: 'grab', marginRight: 12 }}>
        <HolderOutlined />
      </div>

      {/* 序号 */}
      <div style={{ width: 40, textAlign: 'center' }}>
        <Tag color="purple">{item.display_order + 1}</Tag>
      </div>

      {/* 缩略图 */}
      <div style={{ width: 180, marginRight: 12 }}>
        {renderThumbnail()}
      </div>

      {/* 文件信息 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <Tooltip title={item.file_name}>
          <div style={{
            fontWeight: 500,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {item.file_name}
          </div>
        </Tooltip>
        <Space style={{ marginTop: 4 }} size="small">
          <Tag color={getFileTypeColor(item.file_type)}>{item.file_type.toUpperCase()}</Tag>
          <span style={{ color: '#666', whiteSpace: 'nowrap' }}>时长:</span>
          <InputNumber
            size="small"
            min={1}
            max={3600}
            value={item.display_duration}
            onBlur={(e) => {
              const value = parseInt(e.target.value);
              if (value && value !== item.display_duration && value >= 1 && value <= 3600) {
                onUpdateDuration(item.id, value);
              }
            }}
            onPressEnter={(e) => {
              const value = parseInt((e.target as HTMLInputElement).value);
              if (value && value !== item.display_duration && value >= 1 && value <= 3600) {
                onUpdateDuration(item.id, value);
                (e.target as HTMLInputElement).blur();
              }
            }}
            style={{ width: 60 }}
            disabled={isUpdating}
          />
          <span style={{ color: '#666' }}>秒</span>
          {isUpdating && <LoadingOutlined style={{ color: '#1890ff' }} />}
        </Space>
      </div>

      {/* 操作按钮 */}
      <Popconfirm
        title="确定要移除这个媒体项吗？"
        onConfirm={() => onRemove(item.id)}
        okText="确定"
        cancelText="取消"
      >
        <Button size="small" danger icon={<DeleteOutlined />}>
          删除
        </Button>
      </Popconfirm>
    </div>
  );
};

const PlaylistListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [addItemModalVisible, setAddItemModalVisible] = useState(false);
  const [playlistPreviewVisible, setPlaylistPreviewVisible] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState<PlaylistDetail | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [availableDevices, setAvailableDevices] = useState<Device[]>([]);
  const [selectedMediaIds, setSelectedMediaIds] = useState<number[]>([]);
  const [previewIndex, setPreviewIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewSpeed, setPreviewSpeed] = useState(1);
  const [batchPreviewMedia, setBatchPreviewMedia] = useState<MediaFile | null>(null);
  const [deviceInfoModalVisible, setDeviceInfoModalVisible] = useState(false);
  const [selectedPlaylistForDevices, setSelectedPlaylistForDevices] = useState<Playlist | null>(null);
  const [mediaSearchText, setMediaSearchText] = useState('');
  const [updatingItemId, setUpdatingItemId] = useState<number | null>(null);

  // 新增：播放列表设备信息状态
  const [playlistDevicesMap, setPlaylistDevicesMap] = useState<Record<number, DeviceAssignment[]>>({});
  const [devicesInfoLoading, setDevicesInfoLoading] = useState(false);

  // 播放列表名称编辑状态
  const [editingPlaylistId, setEditingPlaylistId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState<string>('');
  const [editNameLoading, setEditNameLoading] = useState(false);

  // 切换媒体选中状态
  const toggleMediaSelection = (mediaId: number) => {
    setSelectedMediaIds(prev =>
      prev.includes(mediaId)
        ? prev.filter(id => id !== mediaId)
        : [...prev, mediaId]
    );
  };

  // 批量获取播放列表的设备信息
  const fetchPlaylistDevices = async (playlistList: Playlist[]) => {
    if (playlistList.length === 0) return;

    setDevicesInfoLoading(true);
    const devicesMap: Record<number, DeviceAssignment[]> = {};

    await Promise.all(
      playlistList.map(async (playlist) => {
        try {
          const detail = await getPlaylistDetail(playlist.id);
          devicesMap[playlist.id] = (detail as unknown as { devices: DeviceAssignment[] }).devices || [];
        } catch {
          // 忽略错误
        }
      })
    );

    setPlaylistDevicesMap(devicesMap);
    setDevicesInfoLoading(false);
  };

  // 播放列表加载后获取设备信息
  useEffect(() => {
    if (playlists.length > 0) {
      fetchPlaylistDevices(playlists);
    }
  }, [playlists.map(p => p.id).join(',')]);

  // 缩略图渲染函数（复用 MediaList.tsx 模式）
  const renderMediaThumbnail = (media: MediaFile, size: { width: number; height: number } = { width: 120, height: 90 }) => {
    const { width, height } = size;

    // 使用缩略图 API 获取正确的 URL
    const thumbnailUrl = getThumbnail(media.id);

    return (
      <Image
        src={thumbnailUrl}
        alt={media.file_name}
        width={width}
        height={height}
        style={{ borderRadius: 4, objectFit: 'cover' }}
        fallback={`data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='${width}' height='${height}' viewBox='0 0 ${width} ${height}'%3E%3Crect fill='%23f0f0f0' width='${width}' height='${height}'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E加载失败%3C/text%3E%3C/svg%3E`}
        preview={false}
      />
    );
  };

  // 过滤后的媒体列表
  const filteredMediaFiles = mediaFiles.filter(media =>
    media.file_name.toLowerCase().includes(mediaSearchText.toLowerCase())
  );

  // 拖拽传感器配置
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const fetchPlaylists = async () => {
    setLoading(true);
    try {
      const resp = await getPlaylistList({ limit: 100 });
      setPlaylists(resp.items || []);
    } catch (error: unknown) {
      console.error('Fetch playlists error:', error);
      message.error('获取播放列表失败');
      setPlaylists([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMediaFiles = async () => {
    try {
      const response = await getMediaList({ limit: 100 });
      setMediaFiles(response.items || []);
    } catch (error: any) {
      console.error('Fetch media files error:', error);
      setMediaFiles([]);
    }
  };

  const fetchDevices = async () => {
    try {
      const response = await getDeviceList({ limit: 100 });
      setAvailableDevices(response.items || []);
    } catch (error: any) {
      console.error('Fetch devices error:', error);
      setAvailableDevices([]);
    }
  };

  useEffect(() => {
    fetchPlaylists();
    fetchMediaFiles();
    fetchDevices();
  }, []);

  const handleCreatePlaylist = async () => {
    try {
      await createPlaylist({
        name: `播放列表 ${new Date().getTime()}`,
      });
      message.success('播放列表创建成功');
      await fetchPlaylists();
    } catch (error: unknown) {
      console.error('Create playlist error:', error);
      message.error('创建播放列表失败');
    }
  };

  const handleDeletePlaylist = async (playlist: Playlist) => {
    modal.confirm({
      title: '确认删除',
      content: `确定要删除播放列表 "${playlist.name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deletePlaylist(playlist.id);
          message.success('播放列表删除成功');
          await fetchPlaylists();
        } catch (error: any) {
          console.error('Delete playlist error:', error);
          message.error('删除播放列表失败');
        }
      },
    });
  };

  const handleShowDetail = async (playlist: { id: number }) => {
    setLoading(true);
    try {
      const response = await getPlaylistDetail(playlist.id);
      setSelectedPlaylist(response);
      setDetailModalVisible(true);
    } catch (error: any) {
      console.error('Fetch playlist detail error:', error);
      message.error('获取播放列表详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 批量添加媒体
  const handleBatchAddItems = async (values: { display_duration: number }) => {
    if (!selectedPlaylist || selectedMediaIds.length === 0) return;

    try {
      const result = await addItemsToPlaylistBatch(selectedPlaylist.id, {
        media_ids: selectedMediaIds,
        display_duration: values.display_duration,
      });
      message.success(`成功添加 ${result.added_count} 个媒体`);
      if (result.failed_media_ids.length > 0) {
        message.warning(`${result.failed_media_ids.length} 个媒体添加失败`);
      }
      setSelectedMediaIds([]);
      setAddItemModalVisible(false);
      await handleShowDetail(selectedPlaylist);
    } catch (error: any) {
      console.error('Batch add items error:', error);
      message.error('批量添加媒体失败');
    }
  };

  const handleRemoveItem = async (itemId: number) => {
    if (!selectedPlaylist) return;

    try {
      await removeItemFromPlaylist(selectedPlaylist.id, itemId);
      message.success('媒体项已移除');
      await handleShowDetail(selectedPlaylist);
    } catch (error: any) {
      console.error('Remove item error:', error);
      message.error('移除媒体项失败');
    }
  };

  // 更新单个项的显示时长
  const handleUpdateItemDuration = async (itemId: number, duration: number) => {
    if (!selectedPlaylist) return;

    setUpdatingItemId(itemId);
    try {
      await updatePlaylistItem(selectedPlaylist.id, itemId, { display_duration: duration });

      // 更新本地状态
      setSelectedPlaylist(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map(item =>
            item.id === itemId ? { ...item, display_duration: duration } : item
          )
        };
      });

      message.success('时长已更新');
    } catch (error: any) {
      console.error('Update item duration error:', error);
      message.error('更新时长失败');
    } finally {
      setUpdatingItemId(null);
    }
  };

  // 拖拽结束处理
  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      if (!selectedPlaylist) return;

      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const oldIndex = selectedPlaylist.items.findIndex((item) => item.id === active.id);
      const newIndex = selectedPlaylist.items.findIndex((item) => item.id === over.id);

      const newItems = arrayMove(selectedPlaylist.items, oldIndex, newIndex);

      // 更新本地状态
      setSelectedPlaylist({
        ...selectedPlaylist,
        items: newItems.map((item, index) => ({
          ...item,
          display_order: index,
        })),
      });

      // 调用后端 API 保存顺序
      try {
        await reorderPlaylistItems(selectedPlaylist.id, {
          items: newItems.map((item, index) => ({
            id: item.id,
            order: index,
          })),
        });
        message.success('排序已保存');
      } catch (error: any) {
        console.error('Reorder error:', error);
        message.error('保存排序失败');
        // 恢复原始顺序
        await handleShowDetail(selectedPlaylist);
      }
    },
    [selectedPlaylist, message]
  );

  // 取消编辑名称
  const handleCancelEditName = () => {
    setEditingPlaylistId(null);
    setEditingName('');
  };

  // 保存播放列表名称
  const handleSaveName = async (playlistId: number) => {
    const trimmedName = editingName.trim();
    if (!trimmedName) {
      message.warning('播放列表名称不能为空');
      return;
    }

    setEditNameLoading(true);
    try {
      await updatePlaylist(playlistId, { name: trimmedName });
      message.success('名称已更新');
      handleCancelEditName();
      fetchPlaylists();
    } catch (error: any) {
      console.error('Update playlist name error:', error);
      message.error(error.message || '更新失败');
    } finally {
      setEditNameLoading(false);
    }
  };

  const handleAssignToDevice = async () => {
    if (!selectedPlaylist || !selectedDevice) return;

    try {
      await assignPlaylistToDevice(selectedPlaylist.id, selectedDevice);
      message.success('播放列表已分配到设备');
      await fetchPlaylists();
    } catch (error: any) {
      console.error('Assign playlist error:', error);
      message.error('分配失败');
    }
  };

  const handleUnassignDevice = async (deviceId: number) => {
    if (!selectedPlaylist) return;

    modal.confirm({
      title: '确认取消分配',
      content: '确定要取消该设备的播放列表分配吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await unassignPlaylistFromDevice(selectedPlaylist.id, deviceId);
          message.success('已取消设备分配');
          await handleShowDetail(selectedPlaylist);
        } catch (error: any) {
          console.error('Unassign playlist error:', error);
          message.error('取消分配失败');
        }
      },
    });
  };

  // 播放列表预览
  const handlePlaylistPreview = () => {
    if (!selectedPlaylist || selectedPlaylist.items.length === 0) {
      message.warning('播放列表为空');
      return;
    }
    setPreviewIndex(0);
    setPlaylistPreviewVisible(true);
    setIsPlaying(true);
  };

  // 自动播放下一个
  useEffect(() => {
    if (!isPlaying || !playlistPreviewVisible || !selectedPlaylist) return;

    const currentItem = selectedPlaylist.items[previewIndex];
    if (!currentItem) {
      setIsPlaying(false);
      return;
    }

    const timer = setTimeout(() => {
      if (previewIndex < selectedPlaylist.items.length - 1) {
        setPreviewIndex(previewIndex + 1);
      } else {
        // 播放完毕，可以选择循环或停止
        setIsPlaying(false);
        message.info('播放列表播放完毕');
      }
    }, (currentItem.display_duration * 1000) / previewSpeed);

    return () => clearTimeout(timer);
  }, [isPlaying, playlistPreviewVisible, previewIndex, selectedPlaylist, previewSpeed]);

  const columns: ColumnsType<Playlist> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '名称',
      dataIndex: 'name',
      render: (name: string, record: Playlist) => {
        // 系统默认播放列表不可编辑名称
        if (record.is_system) {
          return (
            <Space>
              {name}
              <Tag color="gold">系统默认</Tag>
            </Space>
          );
        }

        // 编辑模式
        if (editingPlaylistId === record.id) {
          return (
            <Space.Compact style={{ width: '100%' }}>
              <Input
                value={editingName}
                onChange={(e) => setEditingName(e.target.value)}
                onPressEnter={() => handleSaveName(record.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    handleCancelEditName();
                  }
                }}
                style={{ width: 200 }}
                autoFocus
                placeholder="输入播放列表名称"
              />
              <Button
                type="primary"
                icon={<CheckOutlined />}
                loading={editNameLoading}
                onClick={() => handleSaveName(record.id)}
              />
              <Button
                icon={<CloseOutlined />}
                onClick={handleCancelEditName}
              />
            </Space.Compact>
          );
        }

        // 正常显示模式
        return (
          <Space>
            <Typography.Text
              style={{ cursor: 'pointer' }}
              onClick={() => {
                setEditingPlaylistId(record.id);
                setEditingName(record.name);
              }}
            >
              {name}
            </Typography.Text>
            <Tooltip title="点击编辑名称">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => {
                  setEditingPlaylistId(record.id);
                  setEditingName(record.name);
                }}
                style={{ color: '#999' }}
              />
            </Tooltip>
          </Space>
        );
      },
    },
    {
      title: '媒体数量',
      dataIndex: 'item_count',
      width: 120,
      render: (count: number) => (
        <Tag color="blue">{count || 0}</Tag>
      ),
    },
    {
      title: '分配设备',
      key: 'assigned_devices',
      width: 250,
      render: (_: any, record: Playlist) => {
        // 系统默认播放列表显示"全部设备"
        if (record.is_system) {
          return (
            <Tag color="gold" icon={<DesktopOutlined />}>
              全部设备（默认）
            </Tag>
          );
        }

        if (devicesInfoLoading) {
          return <LoadingOutlined spin style={{ color: '#1890ff' }} />;
        }

        const devices = playlistDevicesMap[record.id] || [];

        if (devices.length === 0) {
          return (
            <Tooltip title="点击分配设备">
              <Tag
                color="default"
                style={{ cursor: 'pointer' }}
                onClick={async () => {
                  try {
                    const detail = await getPlaylistDetail(record.id);
                    setSelectedPlaylistForDevices(detail as unknown as Playlist);
                  } catch (error) {
                    console.error('Failed to get playlist detail:', error);
                    setSelectedPlaylistForDevices(record);
                  }
                  setDeviceInfoModalVisible(true);
                }}
              >
                <DesktopOutlined /> 未分配
              </Tag>
            </Tooltip>
          );
        }

        return (
          <div
            style={{ cursor: 'pointer' }}
            onClick={async () => {
              try {
                const detail = await getPlaylistDetail(record.id);
                setSelectedPlaylistForDevices(detail as unknown as Playlist);
              } catch (error) {
                console.error('Failed to get playlist detail:', error);
                setSelectedPlaylistForDevices(record);
              }
              setDeviceInfoModalVisible(true);
            }}
          >
            {devices.slice(0, 3).map((device) => (
              <div key={device.id} style={{ marginBottom: 4, fontSize: 12 }}>
                <Space size={4}>
                  <DesktopOutlined
                    style={{
                      color: device.device_status === 'online' ? '#52c41a' : '#999'
                    }}
                  />
                  <span style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block' }}>
                    {device.device_name}
                  </span>
                  <Tag
                    color={device.is_active ? 'success' : 'default'}
                    style={{ fontSize: 10, padding: '0 4px', lineHeight: '16px', margin: 0 }}
                  >
                    {device.is_active ? '激活' : '未激活'}
                  </Tag>
                </Space>
              </div>
            ))}
            {devices.length > 3 && (
              <span style={{ fontSize: 11, color: '#999' }}>
                +{devices.length - 3} 更多设备
              </span>
            )}
          </div>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 200,
      render: (_: any, record: Playlist) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleShowDetail(record)}
          >
            管理
          </Button>
          {!record.is_system && (
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => handleDeletePlaylist(record)}
            >
              删除
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Title level={4}>播放列表管理</Title>
      </div>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreatePlaylist}
          >
            新建播放列表
          </Button>
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={fetchPlaylists}
          >
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={playlists}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* 详情模态框 */}
      <Modal
        title={selectedPlaylist ? selectedPlaylist.name : '播放列表详情'}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {selectedPlaylist && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setAddItemModalVisible(true)}
                >
                  批量添加媒体
                </Button>
                <Button
                  icon={<PlayCircleOutlined />}
                  onClick={handlePlaylistPreview}
                  disabled={selectedPlaylist.items.length === 0}
                >
                  预览播放
                </Button>
              </Space>
            </div>

            {/* 拖拽排序列表 */}
            {selectedPlaylist.items.length > 0 ? (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={selectedPlaylist.items.map((item) => item.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div
                    style={{
                      border: '1px solid #f0f0f0',
                      borderRadius: 8,
                      overflow: 'hidden',
                    }}
                  >
                    {selectedPlaylist.items.map((item) => (
                      <SortablePlaylistItem
                        key={item.id}
                        item={item}
                        onRemove={handleRemoveItem}
                        mediaFiles={mediaFiles}
                        onUpdateDuration={handleUpdateItemDuration}
                        updatingItemId={updatingItemId}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            ) : (
              <div
                style={{
                  textAlign: 'center',
                  padding: 40,
                  color: '#999',
                  border: '1px dashed #d9d9d9',
                  borderRadius: 8,
                }}
              >
                暂无媒体项，点击"批量添加媒体"按钮添加
              </div>
            )}

            {/* 添加媒体模态框 */}
            <Modal
              title="批量添加媒体"
              open={addItemModalVisible}
              onCancel={() => {
                setAddItemModalVisible(false);
                setSelectedMediaIds([]);
                setBatchPreviewMedia(null);
                setMediaSearchText('');
              }}
              footer={null}
              width={900}
            >
              <Form
                layout="vertical"
                onFinish={handleBatchAddItems}
              >
                {/* 搜索框 */}
                <Form.Item style={{ marginBottom: 12 }}>
                  <Input.Search
                    placeholder="搜索媒体文件名..."
                    allowClear
                    value={mediaSearchText}
                    onChange={(e) => setMediaSearchText(e.target.value)}
                    style={{ marginBottom: 8 }}
                  />
                </Form.Item>

                {/* 媒体卡片网格选择器 */}
                <Form.Item
                  label={`选择媒体（已选: ${selectedMediaIds.length} 个）`}
                  style={{ marginBottom: 16 }}
                >
                  <div style={{ maxHeight: 350, overflow: 'auto', padding: 4 }}>
                    {filteredMediaFiles.length > 0 ? (
                      <Checkbox.Group
                        value={selectedMediaIds}
                        onChange={(values) => setSelectedMediaIds(values as number[])}
                        style={{ width: '100%' }}
                      >
                        <Row gutter={[12, 12]}>
                          {filteredMediaFiles.map((media) => (
                            <Col span={6} key={media.id}>
                              <Card
                                hoverable
                                size="small"
                                cover={renderMediaThumbnail(media)}
                                style={{
                                  border: selectedMediaIds.includes(media.id) ? '2px solid #1890ff' : '1px solid #d9d9d9',
                                  cursor: 'pointer',
                                  transition: 'all 0.2s',
                                }}
                                onClick={() => toggleMediaSelection(media.id)}
                              >
                                <Card.Meta
                                  title={
                                    <Checkbox
                                      value={media.id}
                                      style={{ fontSize: 12 }}
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <Tooltip title={media.file_name}>
                                        <span style={{
                                          display: 'inline-block',
                                          maxWidth: 100,
                                          overflow: 'hidden',
                                          textOverflow: 'ellipsis',
                                          whiteSpace: 'nowrap'
                                        }}>
                                          {media.file_name}
                                        </span>
                                      </Tooltip>
                                    </Checkbox>
                                  }
                                  description={
                                    <Tag color={media.file_type === 'image' ? 'green' : media.file_type === 'video' ? 'blue' : 'orange'} style={{ fontSize: 10 }}>
                                      {media.file_type.toUpperCase()}
                                    </Tag>
                                  }
                                />
                              </Card>
                            </Col>
                          ))}
                        </Row>
                      </Checkbox.Group>
                    ) : (
                      <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                        {mediaSearchText ? '未找到匹配的媒体' : '暂无可用的媒体文件'}
                      </div>
                    )}
                  </div>
                </Form.Item>

                {/* 已选媒体预览 */}
                {selectedMediaIds.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <Typography.Text strong>已选媒体预览</Typography.Text>
                    <Row gutter={[8, 8]} style={{ marginTop: 8, maxHeight: 200, overflow: 'auto' }}>
                      {selectedMediaIds.map((id) => {
                        const media = mediaFiles.find((m) => m.id === id);
                        if (!media) return null;
                        return (
                          <Col span={6} key={id}>
                            <Card
                              size="small"
                              hoverable
                              cover={renderMediaThumbnail(media)}
                              actions={[
                                <EyeOutlined key="preview" onClick={() => setBatchPreviewMedia(media)} />,
                                <CloseCircleOutlined key="remove" onClick={() => {
                                  setSelectedMediaIds(selectedMediaIds.filter((i) => i !== id));
                                }} />,
                              ]}
                            >
                              <Card.Meta
                                title={
                                  <Tooltip title={media.file_name}>
                                    <span style={{ fontSize: 11, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                      {media.file_name}
                                    </span>
                                  </Tooltip>
                                }
                                description={
                                  <Tag color={media.file_type === 'image' ? 'green' : media.file_type === 'video' ? 'blue' : 'orange'} style={{ fontSize: 10 }}>
                                    {media.file_type.toUpperCase()}
                                  </Tag>
                                }
                              />
                            </Card>
                          </Col>
                        );
                      })}
                    </Row>
                  </div>
                )}

                <Form.Item
                  label="显示时长(秒)"
                  name="display_duration"
                  initialValue={5}
                  rules={[{ required: true, message: '请输入显示时长' }]}
                >
                  <InputNumber min={1} max={3600} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item>
                  <Space>
                    <Button type="primary" htmlType="submit">
                      添加 ({selectedMediaIds.length} 个媒体)
                    </Button>
                    <Button onClick={() => {
                      setAddItemModalVisible(false);
                      setSelectedMediaIds([]);
                      setBatchPreviewMedia(null);
                      setMediaSearchText('');
                    }}>
                      取消
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </Modal>

            {/* 批量添加时的媒体预览模态框 */}
            <Modal
              title={batchPreviewMedia?.file_name || '媒体预览'}
              open={!!batchPreviewMedia}
              onCancel={() => setBatchPreviewMedia(null)}
              footer={null}
              width={700}
              centered
            >
              {batchPreviewMedia && (
                <div style={{ textAlign: 'center' }}>
                  {batchPreviewMedia.file_type === 'image' ? (
                    <Image
                      src={getMediaFileUrl(batchPreviewMedia.id)}
                      alt={batchPreviewMedia.file_name}
                      style={{ maxWidth: '100%', maxHeight: '60vh' }}
                    />
                  ) : (
                    <video
                      src={getMediaFileUrl(batchPreviewMedia.id)}
                      controls
                      autoPlay
                      style={{ maxWidth: '100%', maxHeight: '60vh' }}
                    />
                  )}
                  <div style={{ marginTop: 12 }}>
                    <Tag color="blue">{batchPreviewMedia.file_type}</Tag>
                    <Tag>{batchPreviewMedia.file_size ? `${(batchPreviewMedia.file_size / 1024).toFixed(1)} KB` : ''}</Tag>
                  </div>
                </div>
              )}
            </Modal>

            {/* 设备分配 - 系统默认播放列表显示特殊提示 */}
            {selectedPlaylist.is_system ? (
              <div style={{ marginTop: 24, padding: 24, textAlign: 'center', backgroundColor: '#fffbe6', borderRadius: 8 }}>
                <Tag color="gold" style={{ fontSize: 14, padding: '8px 16px', marginBottom: 12 }}>
                  <DesktopOutlined style={{ marginRight: 8 }} />
                  全部设备（默认播放列表）
                </Tag>
                <div style={{ color: '#666', fontSize: 13 }}>
                  系统默认播放列表会自动应用到所有设备，无需手动分配。
                </div>
              </div>
            ) : (
              <>
                {/* 设备分配 */}
                <div style={{ marginTop: 24 }}>
                  <Typography.Text strong>设备分配</Typography.Text>
                </div>

                {selectedPlaylist.devices && selectedPlaylist.devices.length > 0 ? (
                  <div style={{ marginTop: 16 }}>
                    <Table
                      rowKey="id"
                      columns={[
                        {
                          title: '设备名称',
                          dataIndex: 'device_name',
                          render: (name: string, record: any) => (
                            <Space size={4}>
                              <DesktopOutlined
                                style={{
                                  color: record.device_status === 'online' ? '#52c41a' : '#999'
                                }}
                              />
                              <span
                                style={{
                                  color: record.device_status === 'online' ? '#52c41a' : 'inherit'
                                }}
                              >
                                {name || `设备 #${record.device_id}`}
                              </span>
                            </Space>
                          )
                        },
                        {
                          title: '在线状态',
                          dataIndex: 'device_status',
                          width: 100,
                          render: (status: string) => (
                            <Tag color={status === 'online' ? 'success' : 'default'}>
                              {status === 'online' ? '在线' : '离线'}
                            </Tag>
                          )
                        },
                        {
                          title: '激活状态',
                          dataIndex: 'is_active',
                          width: 100,
                          render: (isActive: boolean) => (
                            <Tag color={isActive ? 'blue' : 'default'}>
                              {isActive ? '激活' : '未激活'}
                            </Tag>
                          )
                        },
                        {
                          title: '分配时间',
                          dataIndex: 'assigned_at',
                          width: 180,
                          render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-'
                        },
                        {
                          title: '操作',
                          key: 'action',
                          width: 100,
                          render: (_: any, record: any) => (
                            <Button
                              size="small"
                              danger
                              onClick={() => handleUnassignDevice(record.device_id)}
                            >
                              取消分配
                            </Button>
                          )
                        },
                      ]}
                      dataSource={selectedPlaylist.devices}
                      pagination={false}
                      size="small"
                    />
                  </div>
                ) : (
                  <div style={{ marginTop: 16, textAlign: 'center', color: '#999' }}>
                    <Typography.Text>暂无设备分配</Typography.Text>
                  </div>
                )}

                <div style={{ marginTop: 24 }}>
                  <Typography.Text strong>分配到新设备</Typography.Text>
                </div>

                <div style={{ marginTop: 16 }}>
                  <Select
                    style={{ width: '100%' }}
                    placeholder={availableDevices.length === 0 ? '暂无可用设备' : '选择设备'}
                    onChange={(value) => setSelectedDevice(value)}
                  >
                    {(availableDevices || []).map((device) => (
                      <Select.Option key={device.id} value={device.id}>
                        {device.device_name} ({device.status})
                      </Select.Option>
                    ))}
                  </Select>
                </div>
                <div style={{ marginTop: 16 }}>
                  <Button
                    type="primary"
                    onClick={handleAssignToDevice}
                    disabled={!selectedDevice}
                  >
                    分配
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </Modal>

      {/* 播放列表预览模态框 */}
      <Modal
        title={`播放列表预览 (${previewIndex + 1}/${selectedPlaylist?.items.length || 0})`}
        open={playlistPreviewVisible}
        onCancel={() => {
          setPlaylistPreviewVisible(false);
          setIsPlaying(false);
          setPreviewSpeed(1);
        }}
        footer={
          <Space>
            <Button
              onClick={() => setPreviewIndex(Math.max(0, previewIndex - 1))}
              disabled={previewIndex === 0}
            >
              上一个
            </Button>
            <Button
              type={isPlaying ? 'default' : 'primary'}
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? '暂停' : '播放'}
            </Button>
            <Button
              onClick={() => setPreviewIndex(Math.min((selectedPlaylist?.items.length || 1) - 1, previewIndex + 1))}
              disabled={!selectedPlaylist || previewIndex >= selectedPlaylist.items.length - 1}
            >
              下一个
            </Button>
            <span style={{ marginLeft: 16, marginRight: 8 }}>倍速:</span>
            {[1, 2, 4, 8].map((speed) => (
              <Button
                key={speed}
                size="small"
                type={previewSpeed === speed ? 'primary' : 'default'}
                onClick={() => setPreviewSpeed(speed)}
              >
                {speed}X
              </Button>
            ))}
          </Space>
        }
        width={1000}
        centered
      >
        {selectedPlaylist && selectedPlaylist.items[previewIndex] && (
          <div>
            {/* 固定大小的播放区域 */}
            <div
              style={{
                width: '100%',
                height: 450,
                backgroundColor: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 8,
                overflow: 'hidden',
              }}
            >
              {selectedPlaylist.items[previewIndex].file_type === 'image' && (
                <img
                  src={getMediaFileUrl(selectedPlaylist.items[previewIndex].media_id)}
                  alt={selectedPlaylist.items[previewIndex].file_name}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '100%',
                    width: 'auto',
                    height: 'auto',
                    objectFit: 'contain',
                  }}
                />
              )}
              {(selectedPlaylist.items[previewIndex].file_type === 'video' || selectedPlaylist.items[previewIndex].file_type === 'ppt') && (
                <video
                  key={previewIndex}
                  src={getMediaFileUrl(selectedPlaylist.items[previewIndex].media_id)}
                  controls
                  autoPlay
                  style={{
                    maxWidth: '100%',
                    maxHeight: '100%',
                    width: 'auto',
                    height: 'auto',
                    objectFit: 'contain',
                  }}
                />
              )}
            </div>
            <div style={{ marginTop: 12, textAlign: 'center' }}>
              <Tag color="blue">{selectedPlaylist.items[previewIndex].file_name}</Tag>
              <Tag>{selectedPlaylist.items[previewIndex].display_duration}秒</Tag>
              {previewSpeed > 1 && <Tag color="orange">{previewSpeed}X 倍速</Tag>}
            </div>
          </div>
        )}
      </Modal>

      {/* 设备分配详情模态框 */}
      <Modal
        title={`分配设备 - ${selectedPlaylistForDevices?.name || ''}`}
        open={deviceInfoModalVisible}
        onCancel={() => {
          setDeviceInfoModalVisible(false);
          setSelectedPlaylistForDevices(null);
        }}
        footer={null}
        width={600}
      >
        {selectedPlaylistForDevices && (
          <div>
            {/* 系统默认播放列表特殊提示 */}
            {selectedPlaylistForDevices.is_system ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Tag color="gold" style={{ fontSize: 14, padding: '8px 16px' }}>
                  <DesktopOutlined style={{ marginRight: 8 }} />
                  全部设备（默认播放列表）
                </Tag>
                <div style={{ marginTop: 16, color: '#666', fontSize: 13 }}>
                  系统默认播放列表会自动应用到所有设备，无需手动分配。
                </div>
              </div>
            ) : (
              <>
                {selectedPlaylistForDevices.devices && selectedPlaylistForDevices.devices.length > 0 ? (
                  <Table
                    columns={[
                      {
                        title: '设备名称',
                        dataIndex: 'device_name',
                        render: (name: string, record: DeviceAssignment) => (
                          <Space size={4}>
                            <DesktopOutlined
                              style={{
                                color: record.device_status === 'online' ? '#52c41a' : '#999'
                              }}
                            />
                            {name || `设备 #${record.device_id}`}
                          </Space>
                        ),
                      },
                      {
                        title: '状态',
                        dataIndex: 'is_active',
                        width: 100,
                        render: (isActive: boolean) => (
                          <Tag color={isActive ? 'success' : 'default'}>
                            {isActive ? '激活' : '未激活'}
                          </Tag>
                        ),
                      },
                      {
                        title: '分配时间',
                        dataIndex: 'assigned_at',
                        width: 180,
                        render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-',
                      },
                    ]}
                    dataSource={selectedPlaylistForDevices.devices}
                    rowKey="id"
                    pagination={false}
                    size="small"
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                    暂未分配到任何设备
                  </div>
                )}
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <Button type="primary" onClick={() => {
                    setDeviceInfoModalVisible(false);
                    setSelectedPlaylistForDevices(null);
                    handleShowDetail(selectedPlaylistForDevices);
                  }}>
                    管理设备分配
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default PlaylistListPage;
