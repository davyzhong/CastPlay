import React, { useEffect, useState } from 'react';
import { Table, Tag, message, Card, Statistic, Row, Col, Select, Button, Space, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useDeviceStore, Device } from '../stores/deviceStore';

const { Title } = Typography;
const { Option } = Select;

/**
 * 设备监控页面（简化版 - 只读）
 * 只显示和监控设备状态，不能增删改
 */
const DeviceList: React.FC = () => {
  // Zustand store 状态
  const {
    devices,
    loading,
    fetchDevices,
    error,
    clearError,
  } = useDeviceStore();

  // 筛选状态
  const [filter, setFilter] = useState<'all' | 'online' | 'offline'>('all');

  const loadDevices = async () => {
    await fetchDevices();
  };

  useEffect(() => {
    loadDevices();
    // 定时刷新（60 秒）
    const interval = setInterval(loadDevices, 60000);
    return () => clearInterval(interval);
  }, []);

  // 监听错误状态
  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error]);

  // 计算统计数据
  const totalDevices = devices.length;
  const onlineDevices = devices.filter(d => d.status === 'online').length;
  const offlineDevices = totalDevices - onlineDevices;

  // 根据筛选条件过滤设备
  const filteredDevices = devices.filter(device => {
    if (filter === 'online') return device.status === 'online';
    if (filter === 'offline') return device.status === 'offline';
    return true;
  });

  const columns = [
    {
      title: '设备 ID',
      dataIndex: 'device_id',
      key: 'device_id',
    },
    {
      title: '设备名称',
      dataIndex: 'device_name',
      key: 'device_name',
    },
    {
      title: '类型',
      dataIndex: 'device_type',
      key: 'device_type',
      render: (type: string) => type === 'android_tv' ? 'Android TV' : 'Web 浏览器',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'online' ? 'green' : 'red'}>
          {status === 'online' ? '🟢 在线' : '🔴 离线'}
        </Tag>
      ),
    },
    {
      title: '最后在线',
      dataIndex: 'last_online',
      key: 'last_online',
      render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-',
    },
    {
      title: '当前播放列表',
      dataIndex: ['current_playlist', 'name'],
      key: 'current_playlist',
      render: (name: string) => name || '-',
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>设备监控</Title>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="总设备数"
              value={totalDevices}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="在线设备"
              value={onlineDevices}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="离线设备"
              value={offlineDevices}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选工具 */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>筛选：</span>
          <Select
            value={filter}
            onChange={(value) => setFilter(value)}
            style={{ width: 120 }}
          >
            <Option value="all">全部</Option>
            <Option value="online">在线</Option>
            <Option value="offline">离线</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={loadDevices}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 设备列表表格 */}
      <Table
        columns={columns}
        dataSource={filteredDevices}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 20 }}
      />
    </>
  );
};

export default DeviceList;
