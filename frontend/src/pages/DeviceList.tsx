/**
 * 设备管理页面
 * 优化版本：合并列信息，简化界面
 */
import { useState, useEffect, useRef, useMemo } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  TimePicker,
  Select,
  Card,
  Switch,
  Typography,
  App,
  List,
  Popconfirm,
  Tooltip,
  Descriptions,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  ReloadOutlined,
  ClockCircleOutlined,
  UnorderedListOutlined,
  DesktopOutlined,
  StopOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { Device, DeviceSchedule, DevicePlaylist, Playlist } from '../types';
import { getDeviceList, setDeviceSchedule, getDeviceSchedule, getDevicePlaylists, toggleDeviceDisabled } from '../api/device';
import { getPlaylistList, assignPlaylistToDevice, unassignPlaylistFromDevice, togglePlaylistActivation } from '../api/playlist';
import { useStore } from '../store';

const { Title, Text } = Typography;

const DeviceListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [playlistModalVisible, setPlaylistModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [_schedule, setSchedule] = useState<DeviceSchedule | null>(null);
  const [devicePlaylists, setDevicePlaylists] = useState<DevicePlaylist[]>([]);
  const [allPlaylists, setAllPlaylists] = useState<Playlist[]>([]);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null);
  const [playlistLoading, setPlaylistLoading] = useState(false);
  const { setDevices: setStoreDevices } = useStore();
  const [form] = Form.useForm();

  // 新增：设备附加信息状态
  const [deviceSchedules, setDeviceSchedules] = useState<Record<number, DeviceSchedule>>({});
  const [devicePlaylistsMap, setDevicePlaylistsMap] = useState<Record<number, DevicePlaylist[]>>({});
  const [infoLoading, setInfoLoading] = useState(false);

  // P0-6 修复：使用 ref 保存 AbortController 以便取消请求
  const abortControllerRef = useRef<AbortController | null>(null);
  const extraInfoAbortControllerRef = useRef<AbortController | null>(null);

  const fetchDevices = async () => {
    // P0-6 修复：取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const response = await getDeviceList({ limit: 100 });
      if (response.items) {
        setDevices(response.items);
        setStoreDevices(response.items);
      }
    } catch (error: unknown) {
      // P0-6 修复：忽略取消请求导致的错误
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Fetch devices error:', error);
      const errorMessage = error instanceof Error ? error.message : '获取设备列表失败';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();

    // P0-6 修复：组件卸载时取消进行中的请求
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (extraInfoAbortControllerRef.current) {
        extraInfoAbortControllerRef.current.abort();
      }
    };
  }, []);

  // 批量获取设备附加信息（定时配置和播放列表）
  const fetchDeviceExtraInfo = async (deviceList: Device[]) => {
    if (deviceList.length === 0) return;

    // P0-6 修复：取消之前的请求
    if (extraInfoAbortControllerRef.current) {
      extraInfoAbortControllerRef.current.abort();
    }
    extraInfoAbortControllerRef.current = new AbortController();
    const currentController = extraInfoAbortControllerRef.current;

    setInfoLoading(true);
    const schedules: Record<number, DeviceSchedule> = {};
    const playlistsMap: Record<number, DevicePlaylist[]> = {};

    try {
      await Promise.all(
        deviceList.map(async (device) => {
          // P0-6 修复：检查是否已取消
          if (currentController.signal.aborted) return;

          // 获取定时配置
          try {
            const scheduleData = await getDeviceSchedule(device.id);
            schedules[device.id] = scheduleData;
          } catch {
            // 404 表示未配置，忽略
          }

          // 获取播放列表
          try {
            const response = await getDevicePlaylists(device.id);
            playlistsMap[device.id] = response.playlists || [];
          } catch {
            // 忽略错误
          }
        })
      );

      // P0-6 修复：检查是否已取消后再更新状态
      if (!currentController.signal.aborted) {
        setDeviceSchedules(schedules);
        setDevicePlaylistsMap(playlistsMap);
      }
    } catch (error) {
      // 忽略取消请求导致的错误
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Fetch extra info error:', error);
    } finally {
      if (!currentController.signal.aborted) {
        setInfoLoading(false);
      }
    }
  };

  // P0-7 修复：使用 useMemo 缓存设备 ID 列表，避免每次渲染创建新字符串
  const deviceIdsKey = useMemo(
    () => devices.map(d => d.id).sort().join(','),
    [devices]
  );

  // 设备列表加载后获取附加信息
  useEffect(() => {
    if (devices.length > 0) {
      fetchDeviceExtraInfo(devices);
    }
    // P0-7 修复：使用缓存的 key 作为依赖
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceIdsKey]);

  const handleScheduleModal = async (device: Device) => {
    setSelectedDevice(device);

    try {
      const scheduleData = await getDeviceSchedule(device.id);
      setSchedule(scheduleData);
      form.setFieldsValue({
        power_on_time: scheduleData.power_on_time,
        power_off_time: scheduleData.power_off_time,
        is_enabled: scheduleData.is_enabled,
        weekdays: scheduleData.weekdays,
      });
    } catch (error: unknown) {
      const err = error as { status?: number };
      if (err.status === 404) {
        setSchedule(null);
        form.setFieldsValue({
          power_on_time: null,
          power_off_time: null,
          is_enabled: false,
          weekdays: [1, 2, 3, 4, 5],
        });
      } else {
        console.error('Fetch schedule error:', error);
        message.error('获取定时配置失败');
      }
    }

    setScheduleModalVisible(true);
  };

  const handleSetSchedule = async (values: any) => {
    if (!selectedDevice) return;

    try {
      const formatTime = (time: any) => {
        if (!time) return null;
        if (time && typeof time.format === 'function') {
          return time.format('HH:mm');
        }
        return time;
      };

      await setDeviceSchedule(selectedDevice.id, {
        power_on_time: formatTime(values.power_on_time),
        power_off_time: formatTime(values.power_off_time),
        is_enabled: values.is_enabled || false,
        weekdays: values.weekdays || [1, 2, 3, 4, 5],
      });

      message.success('定时配置已更新');
      setScheduleModalVisible(false);
      // 刷新该设备的定时配置信息
      fetchDeviceExtraInfo([selectedDevice]);
    } catch (error: unknown) {
      console.error('Set schedule error:', error);
      const err = error as { message?: string };
      message.error(err.message || '设置定时配置失败');
    }
  };

  const handleToggleDisabled = async (device: Device) => {
    const newDisabledState = !device.is_disabled;
    const action = newDisabledState ? '禁用' : '启用';

    modal.confirm({
      title: `确认${action}设备`,
      content: newDisabledState
        ? `禁用后，设备 "${device.device_name}" 只能播放默认内容，不会接收播放列表更新。确定要禁用吗？`
        : `确定要启用设备 "${device.device_name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: newDisabledState ? 'danger' : 'primary',
      onOk: async () => {
        try {
          await toggleDeviceDisabled(device.id, newDisabledState);
          message.success(`设备已${action}`);
          // 刷新设备列表
          fetchDevices();
        } catch (error: unknown) {
          console.error('Toggle disabled error:', error);
          message.error(`${action}设备失败`);
        }
      },
    });
  };

  const handleShowDetail = (device: Device) => {
    setSelectedDevice(device);
    setDetailModalVisible(true);
  };

  // 播放列表管理相关函数
  const fetchAllPlaylists = async () => {
    try {
      const response = await getPlaylistList({ limit: 100 });
      setAllPlaylists(response.items || []);
    } catch (error: unknown) {
      console.error('Fetch playlists error:', error);
    }
  };

  const handlePlaylistModal = async (device: Device) => {
    setSelectedDevice(device);
    setPlaylistLoading(true);
    setPlaylistModalVisible(true);

    try {
      const response = await getDevicePlaylists(device.id);
      setDevicePlaylists(response.playlists || []);
      await fetchAllPlaylists();
    } catch (error: unknown) {
      console.error('Fetch device playlists error:', error);
      message.error('获取设备播放列表失败');
    } finally {
      setPlaylistLoading(false);
    }
  };

  const handleAssignPlaylist = async () => {
    if (!selectedDevice || !selectedPlaylistId) return;

    setPlaylistLoading(true);
    try {
      await assignPlaylistToDevice(selectedPlaylistId, selectedDevice.id);
      message.success('播放列表分配成功');
      setSelectedPlaylistId(null);
      const response = await getDevicePlaylists(selectedDevice.id);
      setDevicePlaylists(response.playlists || []);
      // 同时更新列表页显示
      setDevicePlaylistsMap(prev => ({
        ...prev,
        [selectedDevice.id]: response.playlists || []
      }));
    } catch (error: unknown) {
      console.error('Assign playlist error:', error);
      const err = error as { response?: { data?: { detail?: string } } };
      message.error(err.response?.data?.detail || '分配播放列表失败');
    } finally {
      setPlaylistLoading(false);
    }
  };

  const handleUnassignPlaylist = async (playlistId: number) => {
    if (!selectedDevice) return;

    try {
      await unassignPlaylistFromDevice(playlistId, selectedDevice.id);
      message.success('已取消播放列表分配');
      const response = await getDevicePlaylists(selectedDevice.id);
      setDevicePlaylists(response.playlists || []);
      // 同时更新列表页显示
      setDevicePlaylistsMap(prev => ({
        ...prev,
        [selectedDevice.id]: response.playlists || []
      }));
    } catch (error: unknown) {
      console.error('Unassign playlist error:', error);
      message.error('取消分配失败');
    }
  };

  const handleTogglePlaylistActive = async (playlistId: number, isActive: boolean) => {
    if (!selectedDevice) return;

    try {
      await togglePlaylistActivation(playlistId, selectedDevice.id, isActive);
      message.success(isActive ? '播放列表已激活' : '播放列表已停用');
      const response = await getDevicePlaylists(selectedDevice.id);
      setDevicePlaylists(response.playlists || []);
      // 同时更新列表页显示
      setDevicePlaylistsMap(prev => ({
        ...prev,
        [selectedDevice.id]: response.playlists || []
      }));
    } catch (error: unknown) {
      console.error('Toggle playlist active error:', error);
      message.error('操作失败');
    }
  };

  // 格式化最后在线时间
  const formatLastOnline = (time: string | undefined) => {
    if (!time) return '-';
    const date = new Date(time);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins} 分钟前`;
    if (diffHours < 24) return `${diffHours} 小时前`;
    if (diffDays < 7) return `${diffDays} 天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const columns: ColumnsType<Device> = [
    {
      title: '设备信息',
      key: 'device_info',
      width: 300,
      render: (_: any, record: Device) => (
        <Space direction="vertical" size={0}>
          <Space>
            <DesktopOutlined style={{ color: record.is_disabled ? '#999' : '#1890ff' }} />
            <Text strong style={{ color: record.is_disabled ? '#999' : undefined }}>
              {record.device_name}
            </Text>
            {record.is_disabled && (
              <Tag color="warning" icon={<StopOutlined />}>已禁用</Tag>
            )}
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            ID: {record.device_id.slice(0, 8)}...
          </Text>
          {(record.ip_address || record.mac_address) && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.ip_address && `IP: ${record.ip_address}`}
              {record.ip_address && record.mac_address && ' | '}
              {record.mac_address && `MAC: ${record.mac_address}`}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '注册码',
      dataIndex: 'registration_code',
      key: 'registration_code',
      width: 140,
      render: (code: string) => code ? (
        <Text copyable={{ text: code }} style={{ color: '#1890ff' }}>{code}</Text>
      ) : '-',
    },
    {
      title: '状态',
      key: 'status_info',
      width: 140,
      render: (_: any, record: Device) => {
        if (record.is_disabled) {
          return (
            <Tooltip title="设备已被禁用，只能播放默认内容">
              <Tag color="warning" icon={<StopOutlined />}>已禁用</Tag>
            </Tooltip>
          );
        }
        return (
          <Tooltip title={`最后在线: ${formatLastOnline(record.last_online)}`}>
            <Tag color={record.status === 'online' ? 'success' : 'default'}>
              {record.status === 'online' ? '在线' : '离线'}
            </Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '定时配置',
      key: 'schedule_info',
      width: 160,
      render: (_: any, record: Device) => {
        if (infoLoading) {
          return <LoadingOutlined spin style={{ color: '#1890ff' }} />;
        }

        const scheduleInfo = deviceSchedules[record.id];

        if (!scheduleInfo || !scheduleInfo.is_enabled) {
          return (
            <Tooltip title="点击配置定时开关机">
              <Button
                type="link"
                size="small"
                onClick={() => handleScheduleModal(record)}
              >
                未配置
              </Button>
            </Tooltip>
          );
        }

        const weekdayNames = ['日', '一', '二', '三', '四', '五', '六'];
        const weekdays = scheduleInfo.weekdays || [];
        const weekdaysText = weekdays.length === 7
          ? '每天'
          : weekdays.length > 0
            ? `周${weekdays.map(d => weekdayNames[d]).join('、')}`
            : '未设置工作日';

        return (
          <Tooltip title="点击修改配置">
            <div
              style={{ cursor: 'pointer', fontSize: 12 }}
              onClick={() => handleScheduleModal(record)}
            >
              <div style={{ color: '#1890ff', fontWeight: 500 }}>
                <ClockCircleOutlined style={{ marginRight: 4 }} />
                {scheduleInfo.power_on_time} - {scheduleInfo.power_off_time}
              </div>
              <div style={{ color: '#52c41a', marginTop: 2 }}>
                ✓ {weekdaysText}
              </div>
            </div>
          </Tooltip>
        );
      },
    },
    {
      title: '播放列表',
      key: 'playlist_info',
      width: 200,
      render: (_: any, record: Device) => {
        if (infoLoading) {
          return <LoadingOutlined spin style={{ color: '#1890ff' }} />;
        }

        const playlists = devicePlaylistsMap[record.id] || [];

        if (playlists.length === 0) {
          return (
            <Tooltip title="未分配播放列表，使用系统默认播放列表。点击分配自定义播放列表。">
              <div
                style={{ cursor: record.is_disabled ? 'default' : 'pointer' }}
                onClick={() => !record.is_disabled && handlePlaylistModal(record)}
              >
                <Space size={4}>
                  <UnorderedListOutlined style={{ color: '#faad14', fontSize: 12 }} />
                  <Text style={{ fontSize: 12, color: '#faad14', fontWeight: 500 }}>默认播放列表</Text>
                </Space>
                <div style={{ fontSize: 11, color: '#999', paddingLeft: 18 }}>
                  系统默认
                </div>
              </div>
            </Tooltip>
          );
        }

        return (
          <div
            style={{ cursor: record.is_disabled ? 'default' : 'pointer' }}
            onClick={() => !record.is_disabled && handlePlaylistModal(record)}
          >
            {playlists.map((pl) => (
              <div key={pl.assignment_id} style={{ marginBottom: 4 }}>
                <Space size={4}>
                  <UnorderedListOutlined style={{ color: '#1890ff', fontSize: 12 }} />
                  <Text style={{ fontSize: 12, fontWeight: 500 }}>{pl.playlist_name}</Text>
                </Space>
                <div style={{ fontSize: 11, color: '#666', paddingLeft: 18 }}>
                  {pl.item_count}个媒体
                  <Tag
                    color={pl.is_active ? 'success' : 'default'}
                    style={{ fontSize: 10, padding: '0 4px', marginLeft: 4, lineHeight: '16px' }}
                  >
                    {pl.is_active ? '激活' : '未激活'}
                  </Tag>
                </div>
              </div>
            ))}
          </div>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: Device) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<InfoCircleOutlined />}
              onClick={() => handleShowDetail(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_disabled ? '启用设备' : '禁用设备'}>
            <Button
              type="text"
              size="small"
              danger={!record.is_disabled}
              icon={record.is_disabled ? <CheckCircleOutlined /> : <StopOutlined />}
              onClick={() => handleToggleDisabled(record)}
            >
              {record.is_disabled ? '启用' : '禁用'}
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 清理无效设备
  const handleCleanupDevices = async () => {
    modal.confirm({
      title: '确认清理无效设备',
      content: '将删除以下设备：\n• 名称包含 test/测试 的设备\n• Web-XXXXXX 格式的测试设备\n• 超过 7 天未上线且无播放列表的设备\n\n此操作不可恢复。',
      okText: '确认清理',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const response = await fetch('/api/devices/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });
          const data = await response.json();
          message.success(data.message || `已清理 ${data.deleted_count} 个无效设备`);
          fetchDevices();
        } catch (error: unknown) {
          console.error('Cleanup error:', error);
          message.error('清理失败');
        }
      },
    });
  };

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>设备管理</Title>
        <Space>
          <Button
            icon={<DeleteOutlined />}
            danger
            onClick={handleCleanupDevices}
          >
            清理无效设备
          </Button>
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={fetchDevices}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={devices}
          rowKey="id"
          loading={loading}
          pagination={false}
          locale={{ emptyText: '暂无设备' }}
        />
      </Card>

      {/* 设备详情模态框 */}
      <Modal
        title="设备详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedDevice && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="设备名称" span={2}>
              {selectedDevice.device_name}
            </Descriptions.Item>
            <Descriptions.Item label="设备 ID" span={2}>
              <Text copyable>{selectedDevice.device_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="注册码">
              {selectedDevice.registration_code ? (
                <Text copyable={{ text: selectedDevice.registration_code }}>
                  {selectedDevice.registration_code}
                </Text>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="时区">
              {selectedDevice.timezone}
            </Descriptions.Item>
            <Descriptions.Item label="MAC 地址">
              {selectedDevice.mac_address || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="IP 地址">
              {selectedDevice.ip_address || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {selectedDevice.is_disabled ? (
                <Tag color="warning">已禁用</Tag>
              ) : (
                <Tag color={selectedDevice.status === 'online' ? 'success' : 'default'}>
                  {selectedDevice.status === 'online' ? '在线' : '离线'}
                </Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="最后在线">
              {selectedDevice.last_online
                ? new Date(selectedDevice.last_online).toLocaleString('zh-CN')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={2}>
              {new Date(selectedDevice.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 定时配置模态框 */}
      <Modal
        title={selectedDevice ? `配置定时: ${selectedDevice.device_name}` : '配置定时'}
        open={scheduleModalVisible}
        onCancel={() => setScheduleModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSetSchedule}
          initialValues={{
            is_enabled: false,
            weekdays: [1, 2, 3, 4, 5],
          }}
        >
          <Form.Item label="启用定时配置" name="is_enabled" valuePropName="checked">
            <Switch checkedChildren="启用" />
          </Form.Item>

          <Form.Item
            label="开机时间"
            name="power_on_time"
            rules={[{ required: true, message: '请选择开机时间' }]}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="关机时间"
            name="power_off_time"
            rules={[{ required: true, message: '请选择关机时间' }]}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="工作日"
            name="weekdays"
            rules={[{ required: true, message: '请选择工作日' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择工作日"
              style={{ width: '100%' }}
              options={[
                { label: '周一', value: 1 },
                { label: '周二', value: 2 },
                { label: '周三', value: 3 },
                { label: '周四', value: 4 },
                { label: '周五', value: 5 },
                { label: '周六', value: 6 },
                { label: '周日', value: 7 },
              ]}
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 播放列表管理模态框 */}
      <Modal
        title={selectedDevice ? `播放列表管理: ${selectedDevice.device_name}` : '播放列表管理'}
        open={playlistModalVisible}
        onCancel={() => {
          setPlaylistModalVisible(false);
          setDevicePlaylists([]);
          setSelectedPlaylistId(null);
        }}
        footer={null}
        width={600}
      >
        <div>
          {/* 分配新播放列表 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space.Compact style={{ width: '100%' }}>
              <Select
                style={{ width: 'calc(100% - 80px)' }}
                placeholder="选择播放列表"
                value={selectedPlaylistId}
                onChange={setSelectedPlaylistId}
                options={allPlaylists
                  .filter((p) => !devicePlaylists.some((dp) => dp.playlist_id === p.id))
                  .map((p) => ({
                    label: `${p.name} (${p.item_count} 项)`,
                    value: p.id,
                  }))}
              />
              <Button
                type="primary"
                onClick={handleAssignPlaylist}
                disabled={!selectedPlaylistId}
                loading={playlistLoading}
              >
                分配
              </Button>
            </Space.Compact>
          </Card>

          {/* 已分配的播放列表 */}
          <Typography.Text strong>已分配的播放列表</Typography.Text>
          <List
            loading={playlistLoading}
            style={{ marginTop: 8 }}
            dataSource={devicePlaylists}
            locale={{ emptyText: '暂无分配的播放列表' }}
            renderItem={(item) => (
              <List.Item
                key={item.assignment_id || item.playlist_id}
                actions={[
                  <Switch
                    key="active"
                    size="small"
                    checked={item.is_active}
                    checkedChildren="激活"
                    unCheckedChildren="停用"
                    onChange={(checked) => handleTogglePlaylistActive(item.playlist_id, checked)}
                  />,
                  <Popconfirm
                    key="remove"
                    title="确定要取消分配吗？"
                    onConfirm={() => handleUnassignPlaylist(item.playlist_id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button size="small" danger>
                      移除
                    </Button>
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      {item.playlist_name}
                      <Tag color="blue">{item.item_count} 项</Tag>
                    </Space>
                  }
                  description={`分配时间: ${item.assigned_at ? new Date(item.assigned_at).toLocaleString('zh-CN') : '-'}`}
                />
              </List.Item>
            )}
          />
        </div>
      </Modal>
    </div>
  );
};

export default DeviceListPage;
