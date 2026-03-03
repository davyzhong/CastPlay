import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  Table,
  Button,
  Space,
  message,
  Modal,
  Form,
  Input,
  Card,
  Row,
  Col,
  Tag,
  InputNumber,
  Image,
  Drawer,
  Checkbox,
  List,
  Empty,
  Progress,
  Select,
  Tabs,
  Upload,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  FileOutlined,
  SearchOutlined,
  PauseCircleOutlined,
  StepForwardOutlined,
  StepBackwardOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  InsertRowBelowOutlined,
  InboxOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { playlistApi, Playlist, PlaylistDetail } from '../api/playlist';
import { mediaApi, MediaFile } from '../api/media';
import { deviceApi, Device } from '../api/device';
import { getMediaUrl } from '../api/client';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import dayjs from 'dayjs';
import type { UploadFile } from 'antd';

const { Dragger } = Upload;

const PlaylistList: React.FC = () => {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [currentPlaylist, setCurrentPlaylist] = useState<PlaylistDetail | null>(null);
  const [mediaList, setMediaList] = useState<MediaFile[]>([]);
  const [deviceList, setDeviceList] = useState<Device[]>([]);
  const [addMediaModalVisible, setAddMediaModalVisible] = useState(false);
  const [assignDeviceModalVisible, setAssignDeviceModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [assignDeviceForm] = Form.useForm();

  // 多选媒体相关状态
  const [selectedMediaIds, setSelectedMediaIds] = useState<number[]>([]);
  const [mediaDurations, setMediaDurations] = useState<{[key: number]: number}>({});
  const [mediaSearchText, setMediaSearchText] = useState('');
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewMedia, setPreviewMedia] = useState<MediaFile | null>(null);

  // 播放列表预览相关状态
  const [playPreviewVisible, setPlayPreviewVisible] = useState(false);
  const [playPreviewIndex, setPlayPreviewIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewProgress, setPreviewProgress] = useState(0);
  const [previewSpeed, setPreviewSpeed] = useState<number>(1); // 轮播预览速度倍数
  const [singlePreviewSpeed, setSinglePreviewSpeed] = useState<number>(1); // 单个媒体预览速度
  const playTimerRef = useRef<NodeJS.Timeout | null>(null);
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const videoPreviewRef = useRef<HTMLVideoElement>(null); // 轮播预览视频ref
  const singleVideoRef = useRef<HTMLVideoElement>(null);   // 单个预览视频ref

  // 插入位置状态
  const [insertAfterIndex, setInsertAfterIndex] = useState<number | null>(null);

  // 上传相关状态
  const [addMediaTab, setAddMediaTab] = useState<string>('select');
  const [uploadFileList, setUploadFileList] = useState<UploadFile[]>([]);
  const [uploadFileType, setUploadFileType] = useState<'image' | 'video' | 'ppt'>('image');
  const [uploadDuration, setUploadDuration] = useState<number>(5);
  const [uploading, setUploading] = useState(false);

  const loadPlaylists = async () => {
    setLoading(true);
    try {
      const response = await playlistApi.list();
      setPlaylists(response.playlists || []);
    } catch (error) {
      message.error('加载播放列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadMediaList = async () => {
    try {
      const response = await mediaApi.list({ per_page: 100, status: 'ready' });
      setMediaList(response.media || []);
    } catch (error) {
      message.error('加载媒体列表失败');
    }
  };

  const loadDeviceList = async () => {
    try {
      const response = await deviceApi.list();
      setDeviceList(response.devices || []);
    } catch (error) {
      message.error('加载设备列表失败');
    }
  };

  const loadPlaylistDetail = async (id: number) => {
    try {
      const detail = await playlistApi.get(id);
      setCurrentPlaylist(detail);
      setDetailDrawerVisible(true);
    } catch (error) {
      message.error('加载播放列表详情失败');
    }
  };

  useEffect(() => {
    loadPlaylists();
    loadMediaList();
    loadDeviceList();
  }, []);

  const handleCreate = () => {
    form.resetFields();
    setCurrentPlaylist(null);
    setModalVisible(true);
  };

  const handleEdit = (playlist: Playlist) => {
    form.setFieldsValue(playlist);
    setCurrentPlaylist(playlist as any);
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (currentPlaylist) {
        await playlistApi.update(currentPlaylist.id, values);
        message.success('更新成功');
      } else {
        await playlistApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadPlaylists();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个播放列表吗？',
      onOk: async () => {
        try {
          await playlistApi.delete(id);
          message.success('删除成功');
          loadPlaylists();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleAddMedia = async () => {
    if (!currentPlaylist || selectedMediaIds.length === 0) {
      message.error('请选择至少一个媒体文件');
      return;
    }

    try {
      let successCount = 0;

      // 如果是插入模式，先添加媒体，然后重新排序
      for (const mediaId of selectedMediaIds) {
        const duration = mediaDurations[mediaId] || 5;
        await playlistApi.addMedia(currentPlaylist.id, {
          media_id: mediaId,
          display_duration: duration,
        });
        successCount++;
      }

      // 如果是插入到指定位置，需要重新排序
      if (insertAfterIndex !== null) {
        // 重新加载获取最新数据
        const detail = await playlistApi.get(currentPlaylist.id);
        const items = detail.items;

        // 新添加的项目会在末尾，需要移动到指定位置
        const newItems = items.slice(0, items.length - successCount);
        const addedItems = items.slice(items.length - successCount);

        // 插入到指定位置后面
        newItems.splice(insertAfterIndex + 1, 0, ...addedItems);

        // 重新排序
        const reorderedItems = newItems.map((item, i) => ({
          id: item.id,
          order: i + 1,
        }));

        await playlistApi.reorderItems(currentPlaylist.id, reorderedItems);
      }

      message.success(`成功添加 ${successCount} 个媒体文件`);
      setAddMediaModalVisible(false);
      setSelectedMediaIds([]);
      setMediaDurations({});
      setMediaSearchText('');
      setInsertAfterIndex(null);
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('添加失败');
    }
  };

  // 媒体选择切换
  const handleMediaSelect = (mediaId: number, checked: boolean) => {
    if (checked) {
      setSelectedMediaIds(prev => [...prev, mediaId]);
      if (!mediaDurations[mediaId]) {
        setMediaDurations(prev => ({ ...prev, [mediaId]: 5 }));
      }
    } else {
      setSelectedMediaIds(prev => prev.filter(id => id !== mediaId));
    }
  };

  // 设置媒体时长
  const handleDurationChange = (mediaId: number, duration: number) => {
    setMediaDurations(prev => ({ ...prev, [mediaId]: duration }));
  };

  // 预览媒体
  const handlePreviewMedia = (media: MediaFile) => {
    setPreviewMedia(media);
    setPreviewVisible(true);
  };

  // === 播放列表预览功能 ===
  const startPlayPreview = useCallback(() => {
    if (!currentPlaylist?.items?.length) return;
    setPlayPreviewVisible(true);
    setPlayPreviewIndex(0);
    setIsPlaying(true);
    setPreviewProgress(0);
  }, [currentPlaylist]);

  const stopPlayPreview = useCallback(() => {
    setIsPlaying(false);
    if (playTimerRef.current) {
      clearTimeout(playTimerRef.current);
      playTimerRef.current = null;
    }
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const closePlayPreview = useCallback(() => {
    stopPlayPreview();
    setPlayPreviewVisible(false);
    setPlayPreviewIndex(0);
    setPreviewProgress(0);
  }, [stopPlayPreview]);

  const playNext = useCallback(() => {
    if (!currentPlaylist?.items?.length) return;
    setPlayPreviewIndex(prev => (prev + 1) % currentPlaylist.items.length);
    setPreviewProgress(0);
  }, [currentPlaylist]);

  const playPrev = useCallback(() => {
    if (!currentPlaylist?.items?.length) return;
    setPlayPreviewIndex(prev =>
      prev === 0 ? currentPlaylist.items.length - 1 : prev - 1
    );
    setPreviewProgress(0);
  }, [currentPlaylist]);

  const togglePlay = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  // 播放计时器效果
  useEffect(() => {
    if (isPlaying && playPreviewVisible && currentPlaylist?.items?.length) {
      const interval = 1000 / previewSpeed; // 1X=1s, 2X=0.5s, 4X=0.25s, 8X=0.125s
      // 进度条更新
      progressTimerRef.current = setInterval(() => {
        setPreviewProgress(prev => {
          if (prev >= 100) return 100;
          return prev + (100 / (interval / 50));
        });
      }, 50);

      // 切换到下一个
      playTimerRef.current = setTimeout(() => {
        playNext();
      }, interval);
    }

    return () => {
      if (playTimerRef.current) clearTimeout(playTimerRef.current);
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    };
  }, [isPlaying, playPreviewVisible, playPreviewIndex, currentPlaylist, playNext, previewSpeed]);

  // 当前预览的媒体项
  const currentPreviewItem = currentPlaylist?.items?.[playPreviewIndex];

  // 过滤媒体列表
  const filteredMediaList = mediaList.filter(media =>
    media.file_name.toLowerCase().includes(mediaSearchText.toLowerCase())
  );

  // 获取媒体类型图标
  const getMediaIcon = (type: string) => {
    if (type === 'image') return <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />;
    if (type === 'video') return <VideoCameraOutlined style={{ fontSize: 24, color: '#52c41a' }} />;
    return <FileOutlined style={{ fontSize: 24, color: '#faad14' }} />;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleRemoveMedia = async (itemId: number) => {
    if (!currentPlaylist) return;

    try {
      await playlistApi.removeMedia(currentPlaylist.id, itemId);
      message.success('移除成功');
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('移除失败');
    }
  };

  // 上移媒体
  const handleMoveUp = async (index: number) => {
    if (!currentPlaylist || index === 0) return;

    const items = Array.from(currentPlaylist.items);
    [items[index - 1], items[index]] = [items[index], items[index - 1]];

    const reorderedItems = items.map((item, i) => ({
      id: item.id,
      order: i + 1,
    }));

    try {
      await playlistApi.reorderItems(currentPlaylist.id, reorderedItems);
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('移动失败');
    }
  };

  // 下移媒体
  const handleMoveDown = async (index: number) => {
    if (!currentPlaylist || index >= currentPlaylist.items.length - 1) return;

    const items = Array.from(currentPlaylist.items);
    [items[index], items[index + 1]] = [items[index + 1], items[index]];

    const reorderedItems = items.map((item, i) => ({
      id: item.id,
      order: i + 1,
    }));

    try {
      await playlistApi.reorderItems(currentPlaylist.id, reorderedItems);
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('移动失败');
    }
  };

  // 在指定位置后插入
  const handleInsertAfter = (index: number) => {
    setInsertAfterIndex(index);
    setAddMediaModalVisible(true);
  };

  // 上传并添加到播放列表
  const handleUploadAndAdd = async () => {
    if (!currentPlaylist || uploadFileList.length === 0) {
      message.error('请选择要上传的文件');
      return;
    }

    setUploading(true);
    let successCount = 0;
    const uploadedMediaIds: number[] = [];

    try {
      // 上传所有文件
      for (const file of uploadFileList) {
        const fileObj = file.originFileObj as File;
        try {
          const result = await mediaApi.upload(fileObj, uploadFileType);
          if (result.media?.id) {
            uploadedMediaIds.push(result.media.id);
            successCount++;
          }
        } catch (e) {
          console.error('上传失败:', file.name);
        }
      }

      if (uploadedMediaIds.length === 0) {
        message.error('上传失败');
        setUploading(false);
        return;
      }

      // 添加到播放列表
      for (const mediaId of uploadedMediaIds) {
        await playlistApi.addMedia(currentPlaylist.id, {
          media_id: mediaId,
          display_duration: uploadDuration,
        });
      }

      // 如果是插入到指定位置，需要重新排序
      if (insertAfterIndex !== null) {
        const detail = await playlistApi.get(currentPlaylist.id);
        const items = detail.items;

        const newItems = items.slice(0, items.length - successCount);
        const addedItems = items.slice(items.length - successCount);
        newItems.splice(insertAfterIndex + 1, 0, ...addedItems);

        const reorderedItems = newItems.map((item, i) => ({
          id: item.id,
          order: i + 1,
        }));

        await playlistApi.reorderItems(currentPlaylist.id, reorderedItems);
      }

      message.success(`成功上传并添加 ${successCount} 个文件`);

      // 重置状态
      setAddMediaModalVisible(false);
      setUploadFileList([]);
      setUploadDuration(5);
      setInsertAfterIndex(null);
      setAddMediaTab('select');

      // 刷新媒体列表和播放列表
      loadMediaList();
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('操作失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination || !currentPlaylist) return;

    const items = Array.from(currentPlaylist.items);
    const [removed] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, removed);

    // 更新顺序
    const reorderedItems = items.map((item, index) => ({
      id: item.id,
      order: index + 1,
    }));

    try {
      await playlistApi.reorderItems(currentPlaylist.id, reorderedItems);
      message.success('排序成功');
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('排序失败');
    }
  };

  const handleAssignDevice = async () => {
    if (!currentPlaylist) return;

    try {
      const values = await assignDeviceForm.validateFields();
      await playlistApi.assignToDevice(currentPlaylist.id, values.device_id);
      message.success('分配成功');
      setAssignDeviceModalVisible(false);
      assignDeviceForm.resetFields();
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('分配失败');
    }
  };

  const handleUnassignDevice = async (deviceId: number) => {
    if (!currentPlaylist) return;

    try {
      await playlistApi.unassignFromDevice(currentPlaylist.id, deviceId);
      message.success('取消分配成功');
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('取消分配失败');
    }
  };

  const handleToggleActive = async (deviceId: number, isActive: boolean) => {
    if (!currentPlaylist) return;

    try {
      await playlistApi.toggleActive(currentPlaylist.id, deviceId, !isActive);
      message.success(isActive ? '已停用' : '已激活');
      loadPlaylistDetail(currentPlaylist.id);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '媒体数',
      dataIndex: 'item_count',
      key: 'item_count',
      width: 100,
      render: (count: number) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_: any, record: Playlist) => (
        <Space>
          <Button
            type="link"
            icon={<PlayCircleOutlined />}
            onClick={() => loadPlaylistDetail(record.id)}
          >
            详情
          </Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
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
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建播放列表
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={playlists}
        loading={loading}
        rowKey="id"
      />

      {/* 创建/编辑对话框 */}
      <Modal
        title={currentPlaylist ? '编辑播放列表' : '创建播放列表'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="名称"
            name="name"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入播放列表名称" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title="播放列表详情"
        width={800}
        open={detailDrawerVisible}
        onClose={() => setDetailDrawerVisible(false)}
      >
        {currentPlaylist && (
          <div>
            <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
              <p><strong>名称：</strong>{currentPlaylist.name}</p>
              <p><strong>描述：</strong>{currentPlaylist.description || '无'}</p>
              {currentPlaylist.items?.length > 0 && (
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={startPlayPreview}
                  style={{ marginTop: 8 }}
                >
                  预览播放效果
                </Button>
              )}
            </Card>

            <Card
              title="媒体列表"
              size="small"
              style={{ marginBottom: 16 }}
              extra={
                <Button
                  size="small"
                  type="primary"
                  onClick={() => setAddMediaModalVisible(true)}
                >
                  添加媒体
                </Button>
              }
            >
              <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="playlist-items">
                  {(provided) => (
                    <div {...provided.droppableProps} ref={provided.innerRef}>
                      {currentPlaylist.items?.map((item, index) => (
                        <Draggable
                          key={item.id}
                          draggableId={String(item.id)}
                          index={index}
                        >
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              style={{
                                padding: 12,
                                marginBottom: 8,
                                border: '1px solid #d9d9d9',
                                borderRadius: 6,
                                background: '#fff',
                                ...provided.draggableProps.style,
                              }}
                            >
                              <Row gutter={12} align="middle">
                                <Col span={1}>
                                  <Tag color="blue">{item.display_order}</Tag>
                                </Col>
                                <Col span={3}>
                                  {item.media?.id ? (
                                    <Image
                                      src={getMediaUrl(item.media.id, 'thumbnail')}
                                      width={100}
                                      height={100}
                                      style={{ objectFit: 'cover', borderRadius: 4 }}
                                      preview={false}
                                      fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAI0lEQVR4nO3BMQEAAADCoPVPbQwfoAAAAAAAAAAAAAAAAIC3AR8AADjSAWsAAAAASUVORK5CYII="
                                    />
                                  ) : (
                                    <div style={{
                                      width: 100,
                                      height: 100,
                                      background: '#f5f5f5',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      borderRadius: 4,
                                    }}>
                                      {getMediaIcon(item.media?.file_type || item.media_type || '')}
                                    </div>
                                  )}
                                </Col>
                                <Col span={8}>
                                  <div style={{ fontWeight: 500, marginBottom: 4 }}>
                                    {item.media?.file_name || item.media_name}
                                  </div>
                                  <Space size="small">
                                    <Tag color={(item.media?.file_type || item.media_type) === 'image' ? 'blue' :
                                               (item.media?.file_type || item.media_type) === 'video' ? 'green' : 'orange'}>
                                      {(item.media?.file_type || item.media_type) === 'image' ? '图片' :
                                       (item.media?.file_type || item.media_type) === 'video' ? '视频' : 'PPT'}
                                    </Tag>
                                    {item.media?.file_size ? (
                                      <span style={{ color: '#888', fontSize: 12 }}>
                                        {formatFileSize(item.media.file_size)}
                                      </span>
                                    ) : null}
                                  </Space>
                                </Col>
                                <Col span={2}>
                                  <Tag color="purple" title={(item.media?.file_type || item.media_type) === 'ppt' ? '每页时长' : '播放时长'}>
                                    {item.display_duration}秒{(item.media?.file_type || item.media_type) === 'ppt' ? '/页' : ''}
                                  </Tag>
                                </Col>
                                <Col span={10} style={{ textAlign: 'right' }}>
                                  <Space size={4}>
                                    <Button
                                      size="small"
                                      type="text"
                                      icon={<ArrowUpOutlined />}
                                      disabled={index === 0}
                                      onClick={() => handleMoveUp(index)}
                                      title="上移"
                                    />
                                    <Button
                                      size="small"
                                      type="text"
                                      icon={<ArrowDownOutlined />}
                                      disabled={index === (currentPlaylist.items?.length || 0) - 1}
                                      onClick={() => handleMoveDown(index)}
                                      title="下移"
                                    />
                                    <Button
                                      size="small"
                                      type="text"
                                      icon={<InsertRowBelowOutlined />}
                                      onClick={() => handleInsertAfter(index)}
                                      title="在此后插入"
                                    />
                                    <Button
                                      size="small"
                                      type="link"
                                      icon={<EyeOutlined />}
                                      onClick={() => {
                                        const previewData = item.media ? item.media : {
                                          id: item.media_id,
                                          file_name: item.media_name || '',
                                          file_type: item.media_type || '',
                                          file_size: 0,
                                          thumbnail_path: null,
                                        };
                                        setPreviewMedia(previewData as MediaFile);
                                        setPreviewVisible(true);
                                      }}
                                    >
                                      预览
                                    </Button>
                                    <Button
                                      size="small"
                                      danger
                                      onClick={() => handleRemoveMedia(item.id)}
                                    >
                                      移除
                                    </Button>
                                  </Space>
                                </Col>
                              </Row>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </DragDropContext>
              {currentPlaylist.items?.length === 0 && (
                <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                  暂无媒体，请添加
                </div>
              )}
            </Card>

            <Card
              title="分配设备"
              size="small"
              extra={
                <Button
                  size="small"
                  type="primary"
                  onClick={() => setAssignDeviceModalVisible(true)}
                >
                  分配设备
                </Button>
              }
            >
              {currentPlaylist.devices?.map((device) => (
                <div
                  key={device.device_id}
                  style={{
                    padding: 8,
                    marginBottom: 8,
                    border: '1px solid #d9d9d9',
                    borderRadius: 4,
                  }}
                >
                  <Row align="middle">
                    <Col span={12}>
                      {device.device_name}
                      {device.is_active && <Tag color="green" style={{ marginLeft: 8 }}>激活中</Tag>}
                    </Col>
                    <Col span={12} style={{ textAlign: 'right' }}>
                      <Space>
                        <Button
                          size="small"
                          onClick={() => handleToggleActive(device.device_id, device.is_active)}
                        >
                          {device.is_active ? '停用' : '激活'}
                        </Button>
                        <Button
                          size="small"
                          danger
                          onClick={() => handleUnassignDevice(device.device_id)}
                        >
                          取消分配
                        </Button>
                      </Space>
                    </Col>
                  </Row>
                </div>
              ))}
              {currentPlaylist.devices?.length === 0 && (
                <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                  暂未分配设备
                </div>
              )}
            </Card>
          </div>
        )}
      </Drawer>

      {/* 添加媒体对话框 - 支持多选和上传 */}
      <Modal
        title={
          insertAfterIndex !== null
            ? `在第 ${insertAfterIndex + 1} 项后插入媒体`
            : '添加媒体'
        }
        open={addMediaModalVisible}
        onOk={addMediaTab === 'select' ? handleAddMedia : handleUploadAndAdd}
        onCancel={() => {
          setAddMediaModalVisible(false);
          setSelectedMediaIds([]);
          setMediaDurations({});
          setMediaSearchText('');
          setInsertAfterIndex(null);
          setUploadFileList([]);
          setAddMediaTab('select');
        }}
        okText={
          addMediaTab === 'select'
            ? (insertAfterIndex !== null ? `插入 ${selectedMediaIds.length} 个` : `添加 ${selectedMediaIds.length} 个`)
            : (uploading ? '上传中...' : `上传并添加 ${uploadFileList.length} 个`)
        }
        cancelText="取消"
        okButtonProps={{
          disabled: addMediaTab === 'select' ? selectedMediaIds.length === 0 : uploadFileList.length === 0,
          loading: uploading
        }}
        width={750}
      >
        <Tabs
          activeKey={addMediaTab}
          onChange={setAddMediaTab}
          items={[
            {
              key: 'select',
              label: '选择已有媒体',
              children: (
                <>
                  <div style={{ marginBottom: 16 }}>
                    <Input
                      placeholder="搜索媒体文件..."
                      prefix={<SearchOutlined />}
                      value={mediaSearchText}
                      onChange={e => setMediaSearchText(e.target.value)}
                      allowClear
                    />
                  </div>

                  <div style={{ maxHeight: 350, overflowY: 'auto' }}>
                    {filteredMediaList.length === 0 ? (
                      <Empty description="暂无媒体文件" />
                    ) : (
                      <List
                        dataSource={filteredMediaList}
                        renderItem={(media) => {
                          const isSelected = selectedMediaIds.includes(media.id);
                          return (
                            <List.Item
                              style={{
                                padding: '12px',
                                background: isSelected ? '#e6f7ff' : '#fff',
                                borderRadius: 4,
                                marginBottom: 8,
                                border: isSelected ? '1px solid #1890ff' : '1px solid #d9d9d9',
                              }}
                            >
                              <Row style={{ width: '100%' }} align="middle" gutter={12}>
                                <Col span={2}>
                                  <Checkbox
                                    checked={isSelected}
                                    onChange={e => handleMediaSelect(media.id, e.target.checked)}
                                  />
                                </Col>
                                <Col span={3}>
                                  <Image
                                      src={getMediaUrl(media.id, 'thumbnail')}
                                      width={90}
                                      height={90}
                                      style={{ objectFit: 'cover', borderRadius: 4 }}
                                      preview={false}
                                      fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAI0lEQVR4nO3BMQEAAADCoPVPbQwfoAAAAAAAAAAAAAAAAIC3AR8AADjSAWsAAAAASUVORK5CYII="
                                    />
                                </Col>
                                <Col span={9}>
                                  <div style={{ fontWeight: 500 }}>{media.file_name}</div>
                                  <div style={{ fontSize: 12, color: '#888' }}>
                                    <Tag>{media.file_type}</Tag>
                                    <span style={{ marginLeft: 8 }}>{formatFileSize(media.file_size)}</span>
                                  </div>
                                </Col>
                                <Col span={6}>
                                  {isSelected && (
                                    <Space size="small">
                                      <span style={{ fontSize: 12 }}>
                                        {media.file_type === 'ppt' ? '每页:' : '时长:'}
                                      </span>
                                      <InputNumber
                                        size="small"
                                        min={1}
                                        max={3600}
                                        value={mediaDurations[media.id] || 5}
                                        onChange={val => handleDurationChange(media.id, val || 5)}
                                        style={{ width: 70 }}
                                        addonAfter="秒"
                                      />
                                    </Space>
                                  )}
                                </Col>
                                <Col span={4} style={{ textAlign: 'right' }}>
                                  <Button
                                    type="link"
                                    size="small"
                                    icon={<EyeOutlined />}
                                    onClick={() => handlePreviewMedia(media)}
                                  >
                                    预览
                                  </Button>
                                </Col>
                              </Row>
                            </List.Item>
                          );
                        }}
                      />
                    )}
                  </div>

                  {selectedMediaIds.length > 0 && (
                    <div style={{ marginTop: 16, padding: '8px 12px', background: '#f5f5f5', borderRadius: 4 }}>
                      <strong>已选择 {selectedMediaIds.length} 个文件</strong>
                      <Button
                        type="link"
                        size="small"
                        onClick={() => {
                          setSelectedMediaIds([]);
                          setMediaDurations({});
                        }}
                      >
                        清空选择
                      </Button>
                    </div>
                  )}
                </>
              ),
            },
            {
              key: 'upload',
              label: '上传新文件',
              children: (
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Row gutter={16}>
                    <Col span={12}>
                      <div>
                        <label style={{ display: 'block', marginBottom: 8 }}>文件类型：</label>
                        <Select
                          style={{ width: '100%' }}
                          value={uploadFileType}
                          onChange={setUploadFileType}
                          disabled={uploading}
                          options={[
                            { label: '图片 (JPG, PNG, GIF)', value: 'image' },
                            { label: '视频 (MP4, AVI, MOV)', value: 'video' },
                            { label: 'PPT (PPTX, PPT)', value: 'ppt' },
                          ]}
                        />
                      </div>
                    </Col>
                    <Col span={12}>
                      <div>
                        <label style={{ display: 'block', marginBottom: 8 }}>
                          {uploadFileType === 'ppt' ? '每页播放时长：' : '播放时长：'}
                        </label>
                        <InputNumber
                          style={{ width: '100%' }}
                          min={1}
                          max={3600}
                          value={uploadDuration}
                          onChange={val => setUploadDuration(val || 5)}
                          addonAfter="秒"
                          disabled={uploading}
                        />
                        {uploadFileType === 'ppt' && (
                          <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
                            PPT每页内容的显示时间
                          </div>
                        )}
                      </div>
                    </Col>
                  </Row>

                  <Dragger
                    multiple
                    fileList={uploadFileList}
                    onChange={({ fileList }) => setUploadFileList(fileList)}
                    beforeUpload={() => false}
                    disabled={uploading}
                    accept={uploadFileType === 'image' ? '.jpg,.jpeg,.png,.gif,.bmp' :
                            uploadFileType === 'video' ? '.mp4,.avi,.mov,.mkv,.flv' : '.ppt,.pptx'}
                    showUploadList={false}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽文件到此区域</p>
                    <p className="ant-upload-hint">支持多文件同时上传，上传后自动添加到当前播放列表</p>
                  </Dragger>

                  {uploadFileList.length > 0 && (
                    <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                      <List
                        size="small"
                        dataSource={uploadFileList}
                        renderItem={(file) => (
                          <List.Item
                            style={{ padding: '8px 0' }}
                            actions={[
                              !uploading && (
                                <Button
                                  type="text"
                                  size="small"
                                  icon={<CloseCircleOutlined />}
                                  onClick={() => setUploadFileList(prev => prev.filter(f => f.uid !== file.uid))}
                                />
                              ),
                            ].filter(Boolean)}
                          >
                            <List.Item.Meta
                              avatar={getMediaIcon(uploadFileType)}
                              title={<span style={{ fontSize: 13 }}>{file.name}</span>}
                              description={
                                <span style={{ fontSize: 12, color: '#888' }}>
                                  {formatFileSize((file.originFileObj as File)?.size || 0)}
                                </span>
                              }
                            />
                          </List.Item>
                        )}
                      />
                      <div style={{ textAlign: 'right', marginTop: 8, color: '#888' }}>
                        共 {uploadFileList.length} 个文件
                      </div>
                    </div>
                  )}
                </Space>
              ),
            },
          ]}
        />
      </Modal>

      {/* 媒体预览弹窗 */}
      <Modal
        title={previewMedia?.file_name}
        open={previewVisible}
        footer={null}
        onCancel={() => {
          setPreviewVisible(false);
          setPreviewMedia(null);
          setSinglePreviewSpeed(1);
        }}
        width={800}
      >
        {previewMedia?.file_type === 'image' && (
          <img
            src={getMediaUrl(previewMedia.id, 'download')}
            alt={previewMedia.file_name}
            style={{ width: '100%' }}
          />
        )}
        {(previewMedia?.file_type === 'video' || previewMedia?.file_type === 'ppt') && (
          <div>
            <video
              ref={singleVideoRef}
              src={getMediaUrl(previewMedia.id, 'download')}
              controls
              autoPlay
              muted
              style={{ width: '100%' }}
              onLoadedData={() => { if (singleVideoRef.current) singleVideoRef.current.playbackRate = singlePreviewSpeed; }}
              onError={(e) => {
                if (previewMedia.file_type === 'ppt') {
                  e.currentTarget.style.display = 'none';
                  const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                  if (fallback) fallback.style.display = 'block';
                }
              }}
            />
            {previewMedia.file_type === 'ppt' && (
              <div style={{ display: 'none', textAlign: 'center', padding: 40 }}>
                <FileOutlined style={{ fontSize: 64, color: '#faad14' }} />
                <p style={{ marginTop: 16, color: '#888' }}>PPT 文件暂未转换，无法预览</p>
                <p style={{ fontSize: 12, color: '#999' }}>请稍后刷新或检查 Celery 转换服务是否运行</p>
              </div>
            )}
            {/* 速度控制 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12 }}>
              <span style={{ color: '#888', fontSize: 13 }}>播放速度:</span>
              {([1, 1.5, 2, 4] as const).map(s => (
                <Button
                  key={s}
                  size="small"
                  type={singlePreviewSpeed === s ? 'primary' : 'default'}
                  onClick={() => {
                    setSinglePreviewSpeed(s);
                    if (singleVideoRef.current) singleVideoRef.current.playbackRate = s;
                  }}
                >
                  {s}X
                </Button>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* 分配设备对话框 */}
      <Modal
        title="分配设备"
        open={assignDeviceModalVisible}
        onOk={handleAssignDevice}
        onCancel={() => {
          setAssignDeviceModalVisible(false);
          assignDeviceForm.resetFields();
        }}
        okText="分配"
        cancelText="取消"
      >
        <Form form={assignDeviceForm} layout="vertical">
          <Form.Item
            label="选择设备"
            name="device_id"
            rules={[{ required: true, message: '请选择设备' }]}
          >
            <Select
              placeholder="请选择设备"
              options={deviceList.map((device) => ({
                label: `${device.device_name} (${device.device_id})`,
                value: device.id,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 播放列表预览模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <PlayCircleOutlined />
            <span>播放预览 - {currentPlaylist?.name}</span>
          </div>
        }
        open={playPreviewVisible}
        footer={null}
        onCancel={closePlayPreview}
        width={900}
        centered
        styles={{ body: { padding: 0 } }}
      >
        {currentPreviewItem && (
          <div style={{ background: '#000' }}>
            {/* 播放区域 */}
            <div
              style={{
                width: '100%',
                height: 500,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#000',
                position: 'relative',
              }}
            >
              {(currentPreviewItem.media?.file_type || currentPreviewItem.media_type) === 'image' && (
                <img
                  src={getMediaUrl(currentPreviewItem.media_id, 'download')}
                  alt={currentPreviewItem.media?.file_name || currentPreviewItem.media_name}
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                />
              )}
              {(currentPreviewItem.media?.file_type || currentPreviewItem.media_type) === 'video' && (
                <video
                  ref={videoPreviewRef}
                  key={currentPreviewItem.id}
                  src={getMediaUrl(currentPreviewItem.media_id, 'download')}
                  autoPlay
                  muted
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  onLoadedData={() => { if (videoPreviewRef.current) videoPreviewRef.current.playbackRate = previewSpeed; }}
                />
              )}
              {(currentPreviewItem.media?.file_type || currentPreviewItem.media_type) === 'ppt' && (
                <video
                  ref={videoPreviewRef}
                  key={`ppt-${currentPreviewItem.id}`}
                  src={getMediaUrl(currentPreviewItem.media_id, 'download')}
                  autoPlay
                  muted
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  onLoadedData={() => { if (videoPreviewRef.current) videoPreviewRef.current.playbackRate = previewSpeed; }}
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              )}

              {/* 序号指示 */}
              <div
                style={{
                  position: 'absolute',
                  top: 16,
                  right: 16,
                  background: 'rgba(0,0,0,0.6)',
                  color: '#fff',
                  padding: '4px 12px',
                  borderRadius: 4,
                  fontSize: 14,
                }}
              >
                {playPreviewIndex + 1} / {currentPlaylist?.items?.length}
              </div>
            </div>

            {/* 进度条 */}
            <Progress
              percent={previewProgress}
              showInfo={false}
              strokeColor="#1890ff"
              trailColor="#333"
              style={{ margin: 0 }}
              size="small"
            />

            {/* 控制条 */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                background: '#1a1a1a',
                gap: 16,
                flexWrap: 'wrap',
              }}
            >
              <Button
                type="text"
                icon={<StepBackwardOutlined style={{ fontSize: 24, color: '#fff' }} />}
                onClick={playPrev}
              />
              <Button
                type="primary"
                shape="circle"
                size="large"
                icon={isPlaying ?
                  <PauseCircleOutlined style={{ fontSize: 28 }} /> :
                  <PlayCircleOutlined style={{ fontSize: 28 }} />
                }
                onClick={togglePlay}
                style={{ width: 56, height: 56 }}
              />
              <Button
                type="text"
                icon={<StepForwardOutlined style={{ fontSize: 24, color: '#fff' }} />}
                onClick={playNext}
              />
              {/* 速度按鈕 */}
              <div style={{ display: 'flex', gap: 6, marginLeft: 8 }}>
                {([1, 2, 4, 8] as const).map(s => (
                  <Button
                    key={s}
                    size="small"
                    type={previewSpeed === s ? 'primary' : 'default'}
                    onClick={() => {
                      setPreviewSpeed(s);
                      if (videoPreviewRef.current) videoPreviewRef.current.playbackRate = s;
                    }}
                    style={{
                      minWidth: 40,
                      background: previewSpeed === s ? '#1890ff' : '#333',
                      borderColor: previewSpeed === s ? '#1890ff' : '#555',
                      color: '#fff',
                    }}
                  >
                    {s}X
                  </Button>
                ))}
              </div>
            </div>

            {/* 当前媒体信息 */}
            <div
              style={{
                padding: '12px 16px',
                background: '#222',
                color: '#fff',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <strong>{currentPreviewItem.media?.file_name || currentPreviewItem.media_name}</strong>
                <Tag color="blue" style={{ marginLeft: 8 }}>
                  {currentPreviewItem.media?.file_type || currentPreviewItem.media_type}
                </Tag>
                {previewSpeed > 1 && <Tag color="orange" style={{ marginLeft: 4 }}>{previewSpeed}X 快进</Tag>}
              </div>
              <div style={{ color: '#888' }}>
                切换间隔: {(1000 / previewSpeed / 1000).toFixed(2)}s
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default PlaylistList;
