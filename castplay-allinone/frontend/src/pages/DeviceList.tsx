/**
 * 设备管理页面
 */
import { useState, useEffect } from 'react';
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
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { PlusOutlined, ReloadOutlined, ClockCircleOutlined } from '@ant-design/icons';
import type { Device, DeviceSchedule } from '../types';
import { getDeviceList, deleteDevice, setDeviceSchedule, getDeviceSchedule } from '../api/device';
import { useStore } from '../store';

const { Title } = Typography;

const DeviceListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [schedule, setSchedule] = useState<DeviceSchedule | null>(null);
  const { setDevices: setStoreDevices } = useStore();
  const [form] = Form.useForm();

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const response = await getDeviceList({ limit: 100 });
      if (response.items) {
        setDevices(response.items);
        setStoreDevices(response.items);
      }
    } catch (error: unknown) {
      console.error('Fetch devices error:', error);
      const errorMessage = error instanceof Error ? error.message : '获取设备列表失败';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    }, []);

  const handleScheduleModal = async (device: Device) => {
    setSelectedDevice(device);

    // 获取现有定时配置
    try {
      const scheduleData = await getDeviceSchedule(device.id);
      setSchedule(scheduleData);
      form.setFieldsValue({
        power_on_time: scheduleData.power_on_time,
        power_off_time: scheduleData.power_off_time,
        is_enabled: scheduleData.is_enabled,
        weekdays: scheduleData.weekdays,
      });
    } catch (error: any) {
      console.error('Fetch schedule error:', error);
    }

    setScheduleModalVisible(true);
  };

  const handleSetSchedule = async (values: any) => {
    if (!selectedDevice) return;

    try {
      await setDeviceSchedule(selectedDevice.id, {
        power_on_time: values.power_on_time,
        power_off_time: values.power_off_time,
        is_enabled: values.is_enabled,
        weekdays: values.weekdays,
      });

      message.success('定时配置已更新');
      setScheduleModalVisible(false);
    } catch (error: any) {
      console.error('Set schedule error:', error);
      message.error('设置定时配置失败');
    }
  };

  const handleDelete = async (device: Device) => {
    modal.confirm({
      title: '确认删除',
      content: `确定要删除设备 "${device.device_name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteDevice(device.id);
          message.success('设备已删除');
          // 更新本地状态
          setDevices(devices.filter((d) => d.id !== device.id));
        } catch (error: any) {
          console.error('Delete device error:', error);
          message.error('删除设备失败');
        }
      },
    });
  };

  const columns: ColumnsType<Device> = [
    {
      title: '设备 ID',
      dataIndex: 'device_id',
      key: 'device_id',
      width: 150,
      ellipsis: true,
    },
    {
      title: '设备名称',
      dataIndex: 'device_name',
      key: 'device_name',
    },
    {
      title: 'MAC 地址',
      dataIndex: 'mac_address',
      key: 'mac_address',
      render: (mac: string) => mac || '-',
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip: string) => ip || '-',
    },
    {
      title: '注册码',
      dataIndex: 'registration_code',
      key: 'registration_code',
      render: (code: string) => code ? (
        <Tag color="blue">{code}</Tag>
      ) : '-',
    },
    {
      title: '播放速度',
      dataIndex: 'playback_speed',
      key: 'playback_speed',
      render: (speed: number) => `${speed || 1}X`,
    },
    {
      title: '时区',
      dataIndex: 'timezone',
      key: 'timezone',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'online' ? 'success' : 'default'}>
          {status === 'online' ? '在线' : '离线'}
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
      title: '定时配置',
      key: 'schedule',
      render: (_: any, record: Device) => (
        <Button
          type="link"
          icon={<ClockCircleOutlined />}
          onClick={() => handleScheduleModal(record)}
        >
          配置
        </Button>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Device) => (
        <Space size="middle">
          <Button
            type="link"
            danger
            onClick={() => handleDelete(record)}
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
        <Title level={4}>设备管理</Title>
      </div>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => message.info('设备注册由播放端完成')}
          >
            注册设备
          </Button>
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={fetchDevices}
          >
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={devices}
          rowKey="id"
          loading={loading}
          pagination={false}
          locale={{
            emptyText: '暂无设备',
          }}
        />
      </Card>

      {/* 定时配置模态框 */}
      <Modal
        title={selectedDevice ? `配置定时: ${selectedDevice.device_name}` : '配置定时'}
        open={scheduleModalVisible}
        onCancel={() => setScheduleModalVisible(false)}
        footer={null}
        width={500}
      >
        {schedule && (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSetSchedule}
            initialValues={{
              power_on_time: schedule.power_on_time,
              power_off_time: schedule.power_off_time,
              is_enabled: schedule.is_enabled,
              weekdays: schedule.weekdays,
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
        )}
      </Modal>
    </div>
  );
};

export default DeviceListPage;
