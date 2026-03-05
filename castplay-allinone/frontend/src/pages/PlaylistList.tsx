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
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  HolderOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  VideoCameraOutlined,
  PictureOutlined,
  CloseCircleOutlined,
  DesktopOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type {
  Playlist,
  PlaylistDetail,
  Device,
  PlaylistItem,
  MediaFile,
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
} from '../api/playlist';
import { getMediaList, getMediaFileUrl } from '../api/media';
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
  onPreview: (item: PlaylistItem) => void;
}

const SortablePlaylistItem: React.FC<SortableRowProps> = ({ item, onRemove, onPreview }) => {
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
      case 'image': return 'blue';
      case 'video': return 'green';
      case 'ppt': return 'orange';
      default: return 'default';
    }
  };

  return (
    <div ref={setNodeRef} style={style}>
      <div {...attributes} {...listeners} style={{ cursor: 'grab', marginRight: 12 }}>
        <HolderOutlined />
      </div>
      <div style={{ width: 60, textAlign: 'center' }}>
        <Tag color="purple">{item.display_order + 1}</Tag>
      </div>
      <div style={{ flex: 1, marginLeft: 12 }}>
        <div style={{ fontWeight: 500 }}>{item.file_name}</div>
        <Space style={{ marginTop: 4 }}>
          <Tag color={getFileTypeColor(item.file_type)}>{item.file_type}</Tag>
          <span style={{ color: '#666' }}>时长: {item.display_duration}秒</span>
        </Space>
      </div>
      <Space>
        {item.file_type === 'image' && (
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => onPreview(item)}
          >
            预览
          </Button>
        )}
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
      </Space>
    </div>
  );
};

const PlaylistListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [addItemModalVisible, setAddItemModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [playlistPreviewVisible, setPlaylistPreviewVisible] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState<PlaylistDetail | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [availableDevices, setAvailableDevices] = useState<Device[]>([]);
  const [selectedMediaIds, setSelectedMediaIds] = useState<number[]>([]);
  const [previewItem, setPreviewItem] = useState<PlaylistItem | null>(null);
  const [previewIndex, setPreviewIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewSpeed, setPreviewSpeed] = useState(1);
  const [batchPreviewMedia, setBatchPreviewMedia] = useState<MediaFile | null>(null);
  const [deviceInfoModalVisible, setDeviceInfoModalVisible] = useState(false);
  const [selectedPlaylistForDevices, setSelectedPlaylistForDevices] = useState<Playlist | null>(null);

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

  const handleShowDetail = async (playlist: Playlist) => {
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

  // 预览单个媒体
  const handlePreviewItem = (item: PlaylistItem) => {
    setPreviewItem(item);
    setPreviewModalVisible(true);
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
      render: (name: string, record: Playlist) => (
        <Space>
          {name}
          {record.is_system && <Tag color="gold">系统默认</Tag>}
        </Space>
      ),
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
      dataIndex: 'device_count',
      width: 120,
      render: (count: number, record: Playlist) => (
        <Tooltip title="点击查看设备详情">
          <Tag
            color={count > 0 ? 'green' : 'default'}
            style={{ cursor: 'pointer' }}
            onClick={() => {
              setSelectedPlaylistForDevices(record);
              setDeviceInfoModalVisible(true);
            }}
          >
            <DesktopOutlined /> {count || 0} 台设备
          </Tag>
        </Tooltip>
      ),
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
          <Button
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDeletePlaylist(record)}
          >
            删除
          </Button>
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
                        onPreview={handlePreviewItem}
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
              }}
              footer={null}
              width={800}
            >
              <Form
                layout="vertical"
                onFinish={handleBatchAddItems}
              >
                <Form.Item
                  label={`选择媒体（已选: ${selectedMediaIds.length} 个）`}
                  name="media_ids"
                  rules={[{ required: true, message: '请选择至少一个媒体' }]}
                >
                  <Select
                    mode="multiple"
                    placeholder="请选择媒体文件（支持多选）"
                    value={selectedMediaIds}
                    onChange={setSelectedMediaIds}
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={mediaFiles.map((m) => ({
                      label: `${m.file_name} (${m.file_type})`,
                      value: m.id,
                    }))}
                  />
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
                              cover={
                                media.file_type === 'image' ? (
                                  <div style={{ height: 80, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                                    <img
                                      src={getMediaFileUrl(id)}
                                      alt={media.file_name}
                                      style={{ maxWidth: '100%', maxHeight: 80, objectFit: 'contain' }}
                                    />
                                  </div>
                                ) : (
                                  <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                                    {media.file_type === 'video' ? (
                                      <VideoCameraOutlined style={{ fontSize: 32, color: '#1890ff' }} />
                                    ) : (
                                      <PictureOutlined style={{ fontSize: 32, color: '#fa8c16' }} />
                                    )}
                                  </div>
                                )
                              }
                              actions={[
                                <EyeOutlined key="preview" onClick={() => setBatchPreviewMedia(media)} />,
                                <CloseCircleOutlined key="remove" onClick={() => {
                                  setSelectedMediaIds(selectedMediaIds.filter((i) => i !== id));
                                }} />,
                              ]}
                            >
                              <Card.Meta
                                title={<span style={{ fontSize: 11 }}>{media.file_name}</span>}
                                description={<Tag color="blue" style={{ fontSize: 10 }}>{media.file_type}</Tag>}
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
                      title: '设备 ID',
                      dataIndex: 'device_id',
                      render: (deviceId: number) => `设备 #${deviceId}`
                    },
                    {
                      title: '状态',
                      dataIndex: 'is_active',
                      render: (isActive: boolean) => (
                        <Tag color={isActive ? 'success' : 'default'}>
                          {isActive ? '激活' : '未激活'}
                        </Tag>
                      )
                    },
                    {
                      title: '分配时间',
                      dataIndex: 'assigned_at',
                      render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-'
                    },
                    {
                      title: '操作',
                      key: 'action',
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
          </div>
        )}
      </Modal>

      {/* 单个媒体预览模态框 */}
      <Modal
        title={previewItem?.file_name || '媒体预览'}
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false);
          setPreviewItem(null);
        }}
        footer={null}
        width={800}
        centered
      >
        {previewItem && (
          <div style={{ textAlign: 'center' }}>
            {previewItem.file_type === 'image' && (
              <Image
                src={getMediaFileUrl(previewItem.media_id)}
                alt={previewItem.file_name}
                style={{ maxWidth: '100%', maxHeight: '70vh' }}
              />
            )}
            {(previewItem.file_type === 'video' || previewItem.file_type === 'ppt') && (
              <video
                src={getMediaFileUrl(previewItem.media_id)}
                controls
                autoPlay
                style={{ maxWidth: '100%', maxHeight: '70vh' }}
              />
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
            {selectedPlaylistForDevices.devices && selectedPlaylistForDevices.devices.length > 0 ? (
              <Table
                columns={[
                  {
                    title: '设备 ID',
                    dataIndex: 'device_id',
                    width: 100,
                    render: (deviceId: number) => `设备 #${deviceId}`,
                  },
                  {
                    title: '状态',
                    dataIndex: 'is_active',
                    render: (isActive: boolean) => (
                      <Tag color={isActive ? 'success' : 'default'}>
                        {isActive ? '激活' : '未激活'}
                      </Tag>
                    ),
                  },
                  {
                    title: '分配时间',
                    dataIndex: 'assigned_at',
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
              <Button onClick={() => {
                setDeviceInfoModalVisible(false);
                setSelectedPlaylistForDevices(null);
                handleShowDetail(selectedPlaylistForDevices);
              }}>
                前往管理页面分配设备
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default PlaylistListPage;
