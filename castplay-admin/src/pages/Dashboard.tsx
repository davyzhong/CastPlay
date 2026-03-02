import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Progress } from 'antd';
import {
  MobileOutlined,
  FileImageOutlined,
  PlaySquareOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { deviceApi, Device } from '../api/device';
import { mediaApi, MediaFile } from '../api/media';
import { playlistApi } from '../api/playlist';
import dayjs from 'dayjs';

interface Statistics {
  totalDevices: number;
  onlineDevices: number;
  totalMedia: number;
  readyMedia: number;
  processingMedia: number;
  totalPlaylists: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Statistics>({
    totalDevices: 0,
    onlineDevices: 0,
    totalMedia: 0,
    readyMedia: 0,
    processingMedia: 0,
    totalPlaylists: 0,
  });
  const [recentDevices, setRecentDevices] = useState<Device[]>([]);
  const [recentMedia, setRecentMedia] = useState<MediaFile[]>([]);
  const [loading, setLoading] = useState(false);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      // 加载设备统计
      const deviceRes = await deviceApi.list({ per_page: 100 });
      const devices = deviceRes.devices || [];
      const onlineCount = devices.filter((d: Device) => d.status === 'online').length;

      // 加载媒体统计
      const mediaRes = await mediaApi.list({ per_page: 100 });
      const media = mediaRes.media || [];
      const readyCount = media.filter((m: MediaFile) => m.status === 'ready').length;
      const processingCount = media.filter((m: MediaFile) => m.status === 'processing').length;

      // 加载播放列表统计
      const playlistRes = await playlistApi.list({ per_page: 100 });
      const playlists = playlistRes.playlists || [];

      setStats({
        totalDevices: devices.length,
        onlineDevices: onlineCount,
        totalMedia: media.length,
        readyMedia: readyCount,
        processingMedia: processingCount,
        totalPlaylists: playlists.length,
      });

      // 设置最近设备
      setRecentDevices(devices.slice(0, 5));

      // 设置最近媒体
      const sortedMedia = media.sort(
        (a: MediaFile, b: MediaFile) =>
          new Date(b.upload_time).getTime() - new Date(a.upload_time).getTime()
      );
      setRecentMedia(sortedMedia.slice(0, 5));
    } catch (error) {
      console.error('加载统计数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatistics();
    // 每30秒刷新一次
    const interval = setInterval(loadStatistics, 30000);
    return () => clearInterval(interval);
  }, []);

  const deviceColumns = [
    {
      title: '设备名称',
      dataIndex: 'device_name',
      key: 'device_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'online' ? 'green' : 'red'}>
          {status === 'online' ? '在线' : '离线'}
        </Tag>
      ),
    },
    {
      title: '最后在线',
      dataIndex: 'last_online',
      key: 'last_online',
      render: (time: string) => (time ? dayjs(time).format('MM-DD HH:mm') : '-'),
    },
  ];

  const mediaColumns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => (
        <Tag color={type === 'image' ? 'blue' : type === 'video' ? 'green' : 'orange'}>
          {type === 'image' ? '图片' : type === 'video' ? '视频' : 'PPT'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          ready: 'green',
          processing: 'blue',
          failed: 'red',
        };
        const textMap: Record<string, string> = {
          ready: '就绪',
          processing: '处理中',
          failed: '失败',
        };
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>;
      },
    },
  ];

  const onlineRate = stats.totalDevices > 0
    ? Math.round((stats.onlineDevices / stats.totalDevices) * 100)
    : 0;

  const readyRate = stats.totalMedia > 0
    ? Math.round((stats.readyMedia / stats.totalMedia) * 100)
    : 0;

  return (
    <div>
      <h2>仪表盘</h2>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="设备总数"
              value={stats.totalDevices}
              prefix={<MobileOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ marginTop: 12 }}>
              <span style={{ fontSize: 12, color: '#999' }}>在线: </span>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#52c41a' }}>
                {stats.onlineDevices}
              </span>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="媒体文件"
              value={stats.totalMedia}
              prefix={<FileImageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 12 }}>
              <span style={{ fontSize: 12, color: '#999' }}>就绪: </span>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#52c41a' }}>
                {stats.readyMedia}
              </span>
              <span style={{ fontSize: 12, color: '#999', marginLeft: 12 }}>处理中: </span>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#1890ff' }}>
                {stats.processingMedia}
              </span>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="播放列表"
              value={stats.totalPlaylists}
              prefix={<PlaySquareOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, color: '#666' }}>设备在线率</span>
            </div>
            <Progress
              type="circle"
              percent={onlineRate}
              width={80}
              strokeColor={onlineRate > 80 ? '#52c41a' : onlineRate > 50 ? '#1890ff' : '#ff4d4f'}
            />
          </Card>
        </Col>
      </Row>

      {/* 媒体就绪率 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="媒体处理情况" size="small">
            <Row gutter={16}>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  <div style={{ marginTop: 8, fontSize: 16, fontWeight: 'bold' }}>
                    {stats.readyMedia}
                  </div>
                  <div style={{ color: '#999', fontSize: 12 }}>就绪</div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <ClockCircleOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                  <div style={{ marginTop: 8, fontSize: 16, fontWeight: 'bold' }}>
                    {stats.processingMedia}
                  </div>
                  <div style={{ color: '#999', fontSize: 12 }}>处理中</div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 14, color: '#666', marginBottom: 8 }}>就绪率</div>
                  <Progress
                    percent={readyRate}
                    status={readyRate === 100 ? 'success' : 'active'}
                  />
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 最近设备和媒体 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="最近设备" size="small" loading={loading}>
            <Table
              columns={deviceColumns}
              dataSource={recentDevices}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="最近上传" size="small" loading={loading}>
            <Table
              columns={mediaColumns}
              dataSource={recentMedia}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
