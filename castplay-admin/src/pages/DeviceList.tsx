import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Tag, message, Modal, Form, Input, TimePicker, Checkbox, Select } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useDeviceStore, Device } from '../stores/deviceStore';
import { deviceApi } from '@/api/device';
import dayjs from 'dayjs';

/**
 * 设备列表页面
 * 使用 Zustand store 统一管理设备状态
 */
const DeviceList: React.FC = () => {
  // Zustand store 状态
  const {
    devices,
    loading,
    fetchDevices,
    deleteDevice,
    createDevice,
    error,
    clearError,
  } = useDeviceStore();

  // 局部 UI 状态
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [currentDevice, setCurrentDevice] = useState<Device | null>(null);
  const [form] = Form.useForm();
  const [createForm] = Form.useForm();

  const loadDevices = async () => {
    await fetchDevices();
  };

  useEffect(() => {
    loadDevices();
  }, []);

  // 监听错误状态
  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error]);

  const handleSetSchedule = (device: Device) => {
    setCurrentDevice(device);
    setScheduleModalVisible(true);

    // Load existing schedule
    deviceApi.getSchedule(device.id).then((schedule) => {
      form.setFieldsValue({
        power_on_time: schedule.power_on_time ? dayjs(schedule.power_on_time, 'HH:mm') : null,
        power_off_time: schedule.power_off_time ? dayjs(schedule.power_off_time, 'HH:mm') : null,
        weekdays: schedule.weekdays || [1, 2, 3, 4, 5, 6, 7],
        is_enabled: schedule.is_enabled,
      });
    }).catch(() => {
      form.resetFields();
    });
  };

  const handleScheduleSubmit = async () => {
    if (!currentDevice) return;

    try {
      const values = await form.validateFields();
      await deviceApi.setSchedule(currentDevice.id, {
        power_on_time: values.power_on_time?.format('HH:mm'),
        power_off_time: values.power_off_time?.format('HH:mm'),
        weekdays: values.weekdays,
        is_enabled: values.is_enabled,
      });
      message.success('定时配置设置成功');
      setScheduleModalVisible(false);
    } catch (error) {
      message.error('设置失败');
    }
  };

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个设备吗？',
      onOk: async () => {
        try {
          await deleteDevice(id);
          message.success('删除成功');
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      await createDevice({
        device_name: values.device_name || undefined,
        timezone: values.timezone,
      });
      message.success('设备创建成功');
      setCreateModalVisible(false);
      createForm.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.error || '创建失败');
    }
  };

  const columns = [
    {
      title: '设备ID',
      dataIndex: 'device_id',
      key: 'device_id',
    },
    {
      title: '设备名称',
      dataIndex: 'device_name',
      key: 'device_name',
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
        <Tag color={status === 'online' ? 'green' : 'red'}>
          {status === 'online' ? '在线' : '离线'}
        </Tag>
      ),
    },
    {
      title: '最后在线',
      dataIndex: 'last_online',
      key: 'last_online',
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Device) => (
        <Space>
          <Button type="link" onClick={() => handleSetSchedule(record)}>
            定时配置
          </Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            新建设备
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadDevices}>
            刷新
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={devices}
        loading={loading}
        rowKey="id"
      />

      <Modal
        title="设置定时配置"
        open={scheduleModalVisible}
        onOk={handleScheduleSubmit}
        onCancel={() => setScheduleModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="开机时间" name="power_on_time">
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="关机时间" name="power_off_time">
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="工作日" name="weekdays">
            <Checkbox.Group
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
          <Form.Item label="启用" name="is_enabled" valuePropName="checked">
            <Checkbox>启用定时配置</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新建设备"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        okText="创建"
        cancelText="取消"
      >
        <Form form={createForm} layout="vertical">
          <Form.Item
            label="设备ID"
            name="device_id"
            extra="留空则自动生成"
          >
            <Input placeholder="留空自动生成" />
          </Form.Item>
          <Form.Item
            label="设备名称"
            name="device_name"
            extra="留空则使用默认名称"
          >
            <Input placeholder="留空使用默认名称" />
          </Form.Item>
          <Form.Item
            label="时区"
            name="timezone"
            initialValue="Asia/Shanghai"
          >
            <Select
              options={[
                { label: '中国标准时间 (UTC+8)', value: 'Asia/Shanghai' },
                { label: '美国太平洋时间 (UTC-8)', value: 'America/Los_Angeles' },
                { label: '美国东部时间 (UTC-5)', value: 'America/New_York' },
                { label: '伦敦时间 (UTC+0)', value: 'Europe/London' },
                { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default DeviceList;
