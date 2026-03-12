/**
 * 仪表盘页面
 * 展示系统概览数据
 */
import { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Progress,
  Typography,
  Space,
  List,
  Avatar,
  Empty,
  Spin,
  Image,
} from 'antd';
import {
  DatabaseOutlined,
  FolderOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  FilePptOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getDeviceList } from '../api/device';
import { getMediaList, getThumbnail } from '../api/media';
import { getPlaylistList } from '../api/playlist';
import type { Device, MediaFile, Playlist } from '../types';

const { Title, Text } = Typography;

interface DashboardStats {
  devices: {
    total: number;
    online: number;
    offline: number;
  };
  media: {
    total: number;
    images: number;
    videos: number;
    ppts: number;
    totalSize: number;
  };
  playlists: {
    total: number;
    activeAssignments: number;
  };
}

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    devices: { total: 0, online: 0, offline: 0 },
    media: { total: 0, images: 0, videos: 0, ppts: 0, totalSize: 0 },
    playlists: { total: 0, activeAssignments: 0 },
  });
  const [recentDevices, setRecentDevices] = useState<Device[]>([]);
  const [recentMedia, setRecentMedia] = useState<MediaFile[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 并行获取所有数据
      const [devicesRes, mediaRes, playlistsRes] = await Promise.all([
        getDeviceList({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
        getMediaList({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
        getPlaylistList({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
      ]);

      const devices = devicesRes.items || [];
      const media = mediaRes.items || [];
      const playlists = playlistsRes.items || [];

      // 计算设备统计
      const onlineDevices = devices.filter((d: Device) => d.status === 'online').length;
      const offlineDevices = devices.filter((d: Device) => d.status === 'offline').length;

      // 计算媒体统计
      const images = media.filter((m: MediaFile) => m.file_type === 'image').length;
      const videos = media.filter((m: MediaFile) => m.file_type === 'video').length;
      const ppts = media.filter((m: MediaFile) => m.file_type === 'ppt').length;
      const totalSize = media.reduce((sum: number, m: MediaFile) => sum + (m.file_size || 0), 0);

      // 计算播放列表统计
      let activeAssignments = 0;
      playlists.forEach((p: Playlist & { devices?: { is_active: boolean }[] }) => {
        if (p.devices) {
          activeAssignments += p.devices.filter((d: { is_active: boolean }) => d.is_active).length;
        }
      });

      setStats({
        devices: { total: devices.length, online: onlineDevices, offline: offlineDevices },
        media: { total: media.length, images, videos, ppts, totalSize },
        playlists: { total: playlists.length, activeAssignments },
      });

      // 最近设备（按创建时间排序）
      setRecentDevices(
        devices
          .sort((a: Device, b: Device) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 5)
      );

      // 最近媒体
      setRecentMedia(
        media
          .sort((a: MediaFile, b: MediaFile) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 5)
      );
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (time: string): string => {
    if (!time) return '-';
    const date = new Date(time.replace(' ', 'T'));
    return isNaN(date.getTime()) ? '-' : date.toLocaleString('zh-CN');
  };

  const getTimeAgo = (time: string): string => {
    if (!time) return '-';
    const date = new Date(time.replace(' ', 'T'));
    if (isNaN(date.getTime())) return '-';
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins} 分钟前`;
    if (diffHours < 24) return `${diffHours} 小时前`;
    if (diffDays < 30) return `${diffDays} 天前`;
    return formatTime(time);
  };

  // 设备表格列
  const deviceColumns: ColumnsType<Device> = [
    {
      title: '设备名称',
      dataIndex: 'device_name',
      key: 'device_name',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'online' ? 'success' : 'default'} icon={status === 'online' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {status === 'online' ? '在线' : '离线'}
        </Tag>
      ),
    },
    {
      title: '最后在线',
      dataIndex: 'last_online',
      key: 'last_online',
      width: 120,
      render: (time: string) => getTimeAgo(time),
    },
  ];

  // 媒体列表项渲染
  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <FileImageOutlined style={{ color: '#52c41a' }} />;
      case 'video':
        return <VideoCameraOutlined style={{ color: '#1890ff' }} />;
      case 'ppt':
        return <FilePptOutlined style={{ color: '#fa8c16' }} />;
      default:
        return <FolderOutlined />;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载中...">
          <div style={{ padding: 50 }} />
        </Spin>
      </div>
    );
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>系统概览</Title>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="设备总数"
              value={stats.devices.total}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <Progress
                percent={stats.devices.total > 0 ? (stats.devices.online / stats.devices.total) * 100 : 0}
                size="small"
                format={() => `${stats.devices.online} 在线 / ${stats.devices.offline} 离线`}
                strokeColor={{ '0%': '#52c41a', '100%': '#1890ff' }}
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="媒体文件"
              value={stats.media.total}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ marginTop: 8 }}>
              <Space size="small">
                <Tag icon={<FileImageOutlined />} color="green">{stats.media.images} 图片</Tag>
                <Tag icon={<VideoCameraOutlined />} color="blue">{stats.media.videos} 视频</Tag>
                <Tag icon={<FilePptOutlined />} color="orange">{stats.media.ppts} PPT</Tag>
              </Space>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="播放列表"
              value={stats.playlists.total}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                {stats.playlists.activeAssignments} 个激活的设备分配
              </Text>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="存储空间"
              value={formatFileSize(stats.media.totalSize)}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                {stats.media.total} 个文件占用
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 详细信息 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* 设备状态 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                <span>设备状态</span>
              </Space>
            }
            extra={<Tag color="blue">{stats.devices.total} 台设备</Tag>}
          >
            {recentDevices.length > 0 ? (
              <Table
                columns={deviceColumns}
                dataSource={recentDevices}
                rowKey="id"
                pagination={false}
                size="small"
              />
            ) : (
              <Empty description="暂无设备" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>

        {/* 最近媒体 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <FolderOutlined />
                <span>最近上传</span>
              </Space>
            }
            extra={<Tag color="green">{stats.media.total} 个文件</Tag>}
          >
            {recentMedia.length > 0 ? (
              <List
                itemLayout="horizontal"
                dataSource={recentMedia}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        // 图片类型：显示缩略图，支持点击预览原图
                        item.file_type === 'image' ? (
                          <Image
                            src={getThumbnail(item.id)}
                            alt={item.file_name}
                            width={48}
                            height={48}
                            style={{ borderRadius: 4, objectFit: 'cover', cursor: 'pointer' }}
                            fallback="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'%3E%3Crect fill='%23f0f0f0' width='48' height='48'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='10'%3E加载中%3C/text%3E%3C/svg%3E"
                            preview={{
                              src: `/api/media/${item.id}/download`,
                            }}
                          />
                        ) : item.file_type === 'ppt' ? (
                          // PPT 类型：显示缩略图，点击预览缩略图大图
                          <Image
                            src={getThumbnail(item.id)}
                            alt={item.file_name}
                            width={48}
                            height={48}
                            style={{ borderRadius: 4, objectFit: 'cover', cursor: 'pointer' }}
                            fallback="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'%3E%3Crect fill='%23f0f0f0' width='48' height='48'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='10'%3E加载中%3C/text%3E%3C/svg%3E"
                            preview={{
                              src: getThumbnail(item.id),
                            }}
                          />
                        ) : (
                          // 视频类型：显示图标（后端未生成缩略图）
                          <Avatar
                            shape="square"
                            size={48}
                            style={{ backgroundColor: item.file_type === 'video' ? '#1890ff' : '#fa8c16' }}
                            icon={getMediaIcon(item.file_type)}
                          />
                        )
                      }
                      title={
                        <Text ellipsis style={{ maxWidth: 200 }} title={item.file_name}>
                          {item.file_name}
                        </Text>
                      }
                      description={
                        <Space split={<Text type="secondary">|</Text>}>
                          <Tag color={item.file_type === 'image' ? 'success' : item.file_type === 'video' ? 'processing' : 'warning'}>
                            {item.file_type.toUpperCase()}
                          </Tag>
                          <Text type="secondary">{formatFileSize(item.file_size || 0)}</Text>
                        </Space>
                      }
                    />
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        <ClockCircleOutlined style={{ marginRight: 4 }} />
                        {getTimeAgo(item.created_at)}
                      </Text>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无媒体文件" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 快捷操作 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="系统信息">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="设备在线率"
                  value={stats.devices.total > 0 ? ((stats.devices.online / stats.devices.total) * 100).toFixed(1) : 0}
                  suffix="%"
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="平均文件大小"
                  value={stats.media.total > 0 ? formatFileSize(stats.media.totalSize / stats.media.total) : '0 B'}
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="图片占比"
                  value={stats.media.total > 0 ? ((stats.media.images / stats.media.total) * 100).toFixed(1) : 0}
                  suffix="%"
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="平均播放列表分配"
                  value={stats.playlists.total > 0 ? (stats.playlists.activeAssignments / stats.playlists.total).toFixed(1) : 0}
                  suffix=" 台/列表"
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;
