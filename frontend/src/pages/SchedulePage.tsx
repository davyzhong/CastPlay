/**
 * 调度管理页面
 * 管理设备的播放列表调度规则
 */
import { useState, useEffect, useCallback, useMemo, memo } from 'react';
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
  Popconfirm,
  Tooltip,
  InputNumber,
  Checkbox,
  Empty,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  CalendarOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import type { Device, Playlist, PlaylistSchedule } from '../types';
import { DAY_NAMES } from '../types';
import {
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  daysToBitmask,
  bitmaskToDays,
  getDaysDisplay,
} from '../api/schedule';
import { getDeviceList } from '../api/device';
import { getPlaylistList } from '../api/playlist';

const { Title, Text } = Typography;

// Memoized day tag component
const DayTag = memo(function DayTag({ day, isActive }: { day: string; isActive: boolean }) {
  return (
    <Tag color={isActive ? 'blue' : 'default'} style={{ minWidth: 32, textAlign: 'center' }}>
      {day}
    </Tag>
  );
});

// 星期选择器选项
const DAY_OPTIONS = [
  { label: '周一', value: 0 },
  { label: '周二', value: 1 },
  { label: '周三', value: 2 },
  { label: '周四', value: 3 },
  { label: '周五', value: 4 },
  { label: '周六', value: 5 },
  { label: '周日', value: 6 },
];

// 快捷选项
const QUICK_DAY_PRESETS = [
  { label: '每天', value: [0, 1, 2, 3, 4, 5, 6] },
  { label: '工作日', value: [0, 1, 2, 3, 4] },
  { label: '周末', value: [5, 6] },
];

const SchedulePage: React.FC = () => {
  const { message } = App.useApp();
  const [devices, setDevices] = useState<Device[]>([]);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [schedules, setSchedules] = useState<PlaylistSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<PlaylistSchedule | null>(null);
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
  const [form] = Form.useForm();

  // 获取设备列表
  const fetchDevices = async () => {
    try {
      const response = await getDeviceList({ limit: 100 });
      if (response.items) {
        setDevices(response.items);
        // 默认选中第一个设备
        if (response.items.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(response.items[0].id);
        }
      }
    } catch (error) {
      console.error('Fetch devices error:', error);
    }
  };

  // 获取播放列表
  const fetchPlaylists = async () => {
    try {
      const response = await getPlaylistList();
      setPlaylists(response.items || []);
    } catch (error) {
      console.error('Fetch playlists error:', error);
    }
  };

  // 获取调度列表
  const fetchSchedules = useCallback(async () => {
    if (!selectedDeviceId) return;

    setLoading(true);
    try {
      const response = await getSchedules(selectedDeviceId);
      setSchedules(response.schedules || []);
    } catch (error) {
      console.error('Fetch schedules error:', error);
      message.error('获取调度列表失败');
    } finally {
      setLoading(false);
    }
  }, [selectedDeviceId, message]);

  useEffect(() => {
    fetchDevices();
    fetchPlaylists();
  }, []);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  // 打开创建/编辑模态框
  const openModal = (schedule?: PlaylistSchedule) => {
    if (schedule) {
      setEditingSchedule(schedule);
      const selectedDays = bitmaskToDays(schedule.days_of_week);
      form.setFieldsValue({
        device_id: schedule.device_id,
        playlist_id: schedule.playlist_id,
        time_range: [
          schedule.start_time ? (() => {
            const [h, m, s] = schedule.start_time.split(':').map(Number);
            return new Date(2000, 0, 1, h, m, s);
          })() : null,
          schedule.end_time ? (() => {
            const [h, m, s] = schedule.end_time.split(':').map(Number);
            return new Date(2000, 0, 1, h, m, s);
          })() : null,
        ],
        days_of_week: selectedDays,
        enabled: schedule.enabled,
        priority: schedule.priority,
      });
    } else {
      setEditingSchedule(null);
      form.resetFields();
      form.setFieldsValue({
        device_id: selectedDeviceId,
        days_of_week: [0, 1, 2, 3, 4, 5, 6], // 默认每天
        enabled: true,
        priority: 0,
      });
    }
    setModalVisible(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingSchedule(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const [startTime, endTime] = values.time_range || [];

      const formatTime = (date: Date) => {
        const h = date.getHours().toString().padStart(2, '0');
        const m = date.getMinutes().toString().padStart(2, '0');
        const s = date.getSeconds().toString().padStart(2, '0');
        return `${h}:${m}:${s}`;
      };

      const params = {
        device_id: values.device_id,
        playlist_id: values.playlist_id,
        start_time: formatTime(startTime),
        end_time: formatTime(endTime),
        days_of_week: daysToBitmask(values.days_of_week),
        enabled: values.enabled,
        priority: values.priority || 0,
      };

      if (editingSchedule) {
        await updateSchedule(editingSchedule.id, params);
        message.success('调度更新成功');
      } else {
        await createSchedule(params);
        message.success('调度创建成功');
      }

      closeModal();
      fetchSchedules();
    } catch (error: unknown) {
      console.error('Submit error:', error);
      const errorMessage = error instanceof Error ? error.message : '操作失败';
      message.error(errorMessage);
    }
  };

  // 删除调度
  const handleDelete = async (scheduleId: number) => {
    try {
      await deleteSchedule(scheduleId);
      message.success('调度删除成功');
      fetchSchedules();
    } catch (error) {
      console.error('Delete error:', error);
      message.error('删除失败');
    }
  };

  // 切换启用状态
  const handleToggleEnabled = async (schedule: PlaylistSchedule) => {
    try {
      await updateSchedule(schedule.id, { enabled: !schedule.enabled });
      message.success(schedule.enabled ? '已禁用调度' : '已启用调度');
      fetchSchedules();
    } catch (error) {
      console.error('Toggle error:', error);
      message.error('操作失败');
    }
  };

  // 渲染星期显示（使用 memoized 组件）
  const renderDays = useCallback((daysOfWeek: number) => {
    const days = getDaysDisplay(daysOfWeek);
    return (
      <Space size={2} wrap>
        {DAY_NAMES.map((day) => (
          <DayTag key={day} day={day} isActive={days.includes(day)} />
        ))}
      </Space>
    );
  }, []);

  // 表格列定义（memoized）
  const columns = useMemo<ColumnsType<PlaylistSchedule>>(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '播放列表',
      dataIndex: 'playlist_name',
      key: 'playlist_name',
      render: (name: string) => name || '-',
    },
    {
      title: '时间范围',
      key: 'time_range',
      render: (_, record) => (
        <Space>
          <ClockCircleOutlined />
          <Text>
            {record.start_time.slice(0, 5)} - {record.end_time.slice(0, 5)}
          </Text>
        </Space>
      ),
    },
    {
      title: '星期',
      dataIndex: 'days_of_week',
      key: 'days_of_week',
      render: (days: number) => renderDays(days),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: number) => (
        <Tag color={priority > 0 ? 'orange' : 'default'}>{priority}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record) => (
        <Space>
          <Switch
            size="small"
            checked={enabled}
            onChange={() => handleToggleEnabled(record)}
          />
          {enabled ? (
            <Tag color="success">启用</Tag>
          ) : (
            <Tag color="default">禁用</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '冲突',
      dataIndex: 'conflicts',
      key: 'conflicts',
      render: (conflicts: { schedule_id: number; playlist_name: string; overlap: string }[]) => {
        if (!conflicts || conflicts.length === 0) {
          return <Tag color="success">无冲突</Tag>;
        }
        return (
          <Tooltip
            title={
              <div>
                {conflicts.map((c, i) => (
                  <div key={i}>
                    与「{c.playlist_name}」冲突: {c.overlap}
                  </div>
                ))}
              </div>
            }
          >
            <Tag color="warning" icon={<WarningOutlined />}>
              {conflicts.length} 个冲突
            </Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openModal(record)}
          />
          <Popconfirm
            title="确定删除此调度？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ], [renderDays, handleToggleEnabled, openModal, handleDelete]);

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              <CalendarOutlined /> 播放列表调度
            </Title>
            <Select
              style={{ width: 200 }}
              placeholder="选择设备"
              value={selectedDeviceId}
              onChange={(value) => setSelectedDeviceId(value)}
              options={devices.map((d) => ({
                label: d.device_name,
                value: d.id,
              }))}
            />
          </Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openModal()}
            disabled={!selectedDeviceId}
          >
            新建调度
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={schedules}
          rowKey="id"
          loading={loading}
          pagination={false}
          locale={{
            emptyText: (
              <Empty
                description="暂无调度规则"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingSchedule ? '编辑调度' : '新建调度'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={closeModal}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="device_id"
            label="设备"
            rules={[{ required: true, message: '请选择设备' }]}
          >
            <Select
              placeholder="选择设备"
              options={devices.map((d) => ({
                label: d.device_name,
                value: d.id,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="playlist_id"
            label="播放列表"
            rules={[{ required: true, message: '请选择播放列表' }]}
          >
            <Select
              placeholder="选择播放列表"
              options={playlists.map((p) => ({
                label: p.name,
                value: p.id,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="time_range"
            label="时间范围"
            rules={[{ required: true, message: '请选择时间范围' }]}
          >
            <TimePicker.RangePicker
              style={{ width: '100%' }}
              format="HH:mm"
              placeholder={['开始时间', '结束时间']}
            />
          </Form.Item>

          <Form.Item label="快捷选择">
            <Space>
              {QUICK_DAY_PRESETS.map((preset) => (
                <Button
                  key={preset.label}
                  size="small"
                  onClick={() => {
                    form.setFieldValue('days_of_week', preset.value);
                  }}
                >
                  {preset.label}
                </Button>
              ))}
            </Space>
          </Form.Item>

          <Form.Item
            name="days_of_week"
            label="生效星期"
            rules={[{ required: true, message: '请选择至少一天' }]}
          >
            <Checkbox.Group options={DAY_OPTIONS} />
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
            tooltip="数值越大优先级越高，冲突时高优先级生效"
          >
            <InputNumber min={0} max={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SchedulePage;
