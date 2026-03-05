/**
 * 播放列表页面
 */
import { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Card,
  Typography,
  Popconfirm,
  Tag,
  Dropdown,
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  MenuOutlined,
  ReloadOutlined,
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
  addItemToPlaylist,
  removeItemFromPlaylist,
  reorderPlaylistItems,
  assignPlaylistToDevice,
  unassignPlaylistFromDevice,
  togglePlaylistActivation,
} from '../api/playlist';
import { getMediaList } from '../api/media';
import { useStore } from '../store';

const { Title } = Typography;

const PlaylistListPage: React.FC = () => {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [addItemModalVisible, setAddItemModalVisible] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState<PlaylistDetail | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [availableDevices, setAvailableDevices] = useState<Device[]>([]);
  const setNotification = useStore((state) => state.setNotification);

  const fetchPlaylists = async () => {
    setLoading(true);
    try {
      const response = await getPlaylistList({ limit: 100 });
      setPlaylists(response.items);
    } catch (error: any) {
      console.error('Fetch playlists error:', error);
      message.error('获取播放列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchMediaFiles = async () => {
    try {
      const response = await getMediaList({ limit: 500 });
      setMediaFiles(response.items);
    } catch (error: any) {
      console.error('Fetch media files error:', error);
      message.error('获取媒体列表失败');
    }
  };

  const fetchDevices = async () => {
    try {
      // 这里需要导入设备 API
      // const response = await getDeviceList({ limit: 100 });
      // setAvailableDevices(response.items);
    } catch (error: any) {
      console.error('Fetch devices error:', error);
    }
  };

  useEffect(() => {
    fetchPlaylists();
    fetchMediaFiles();
    fetchDevices();
  }, []);

  const handleCreatePlaylist = async () => {
    try {
      const response = await createPlaylist({
        name: `播放列表 ${new Date().getTime()}`,
      });
      message.success('播放列表创建成功');
      await fetchPlaylists();
    } catch (error: any) {
      console.error('Create playlist error:', error);
      message.error('创建播放列表失败');
    }
  };

  const handleDeletePlaylist = async (playlist: Playlist) => {
    Modal.confirm({
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

  const handleAddItem = async (values: { media_id: number; display_duration: number }) => {
    if (!selectedPlaylist) return;

    try {
      await addItemToPlaylist(selectedPlaylist.id, {
        media_id: values.media_id,
        display_duration: values.display_duration,
      });
      message.success('媒体添加成功');
      await handleShowDetail(selectedPlaylist);
    } catch (error: any) {
      console.error('Add item error:', error);
      message.error('添加媒体失败');
    }
    };

  const handleRemoveItem = async (itemId: number) => {
    if (!selectedPlaylist) return;

    Modal.confirm({
      title: '确认删除',
      content: '确定要移除这个媒体项吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await removeItemFromPlaylist(selectedPlaylist.id, itemId);
          message.success('媒体项已移除');
          await handleShowDetail(selectedPlaylist);
        } catch (error: any) {
          console.error('Remove item error:', error);
          message.error('移除媒体项失败');
        }
      },
    });
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

  const handleUnassignDevice = async (assignmentId: number) => {
    if (!selectedPlaylist) return;

    Modal.confirm({
      title: '确认取消分配',
      content: '确定要取消该设备的播放列表分配吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await unassignPlaylistFromDevice(selectedPlaylist.id, assignmentId);
          message.success('已取消设备分配');
          await handleShowDetail(selectedPlaylist);
        } catch (error: any) {
          console.error('Unassign playlist error:', error);
          message.error('取消分配失败');
        }
      },
    });
  };

  const itemColumns: ColumnsType<PlaylistItem> = [
    {
      title: '顺序',
      dataIndex: 'display_order',
      width: 80,
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      width: 100,
    },
    {
      title: '时长(秒)',
      dataIndex: 'display_duration',
      width: 100,
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 100,
      render: (_: any, record: PlaylistItem) => (
        <Button
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => handleRemoveItem(record.id)}
        >
          删除
        </Button>
      ),
    },
  ];

  const columns: ColumnsType<Playlist> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '名称',
      dataIndex: 'name',
    },
    {
      title: '媒体数量',
      dataIndex: 'items',
      width: 120,
      render: (_: any, record: Playlist) => (
        <Tag color="blue">{record.items?.length || 0}</Tag>
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
        width={800}
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
                  添加媒体
                </Button>
              </Space>
            </div>

            <Table
              columns={itemColumns}
              dataSource={selectedPlaylist.items}
              rowKey="id"
              pagination={false}
              size="small"
            />

            {/* 添加媒体模态框 */}
            <Modal
              title="添加媒体"
              open={addItemModalVisible}
              onCancel={() => setAddItemModalVisible(false)}
              footer={null}
              width={500}
            >
              <Form
                layout="vertical"
                onFinish={handleAddItem}
              >
                <Form.Item
                  label="选择媒体"
                  name="media_id"
                  rules={[{ required: true, message: '请选择媒体' }]}
                >
                  <Select
                    options={mediaFiles.map((m) => ({
                      label: m.file_name,
                      value: m.id,
                    }))}
                    showSearch
                    placeholder="请选择媒体文件"
                  />
                </Form.Item>
                <Form.Item
                  label="显示时长(秒)"
                  name="display_duration"
                  initialValue={5}
                  rules={[{ required: true, message: '请输入显示时长' }]}
                >
                  <InputNumber min={1} max={3600} />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit">
                    添加
                  </Button>
                </Form.Item>
              </Form>
            </Modal>

            {/* 设备分配 */}
            <div style={{ marginTop: 24 }}>
              <Typography.Text strong>设备分配</Typography.Text>
            </div>

            {selectedPlaylist.devices && selectedPlaylist.devices.length > 0 ? (
              <div style={{ marginTop: 16 }}>
                <Table
                  columns={[
                    { title: '设备名', dataIndex: ['device', 'name'] },
                    { title: '状态', dataIndex: ['assignment', 'is_active'], render: (isActive: boolean) => (
                      <Tag color={isActive ? 'success' : 'default'}>
                        {isActive ? '激活' : '未激活'}
                      </Tag>
                    )},
                    { title: '操作', dataIndex: ['assignment', 'id'], render: (id: number) => (
                      <Button
                        size="small"
                        danger
                        onClick={() => handleUnassignDevice(id)}
                      >
                        取消分配
                      </Button>
                    )},
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
                placeholder="选择设备"
                onChange={(value) => setSelectedDevice(value)}
              >
                {availableDevices.map((device) => (
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
    </div>
  );
};

export default PlaylistListPage;
