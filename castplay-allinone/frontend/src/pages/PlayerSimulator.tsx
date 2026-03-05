/**
 * 播放端模拟测试页面
 * 用于模拟 Android 播放端的功能测试
 * 整合设备注册、播放列表选择、预览播放、速度控制等功能
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Typography,
  Divider,
  message,
  List,
  Avatar,
  Radio,
  Tooltip,
  Statistic,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  CopyOutlined,
  CheckCircleOutlined,
  VideoCameraOutlined,
  PictureOutlined,
  ReloadOutlined,
  StepBackwardOutlined,
  StepForwardOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import {
  registerDevice,
  reportPlayerStatus,
  getDeviceList,
  getMediaDownloadUrl,
  getAllPlaylists,
  getPlaylistDetail,
} from '../api/player';
import type { PlayerPlaylist, PlaylistItem, DeviceInfo } from '../api/player';

const { Title, Text } = Typography;

// 生成 UUID
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

// 播放速度选项
const SPEED_OPTIONS = [
  { label: '1X', value: 1 },
  { label: '2X', value: 2 },
  { label: '4X', value: 4 },
  { label: '8X', value: 8 },
];

const PlayerSimulator: React.FC = () => {
  // 设备相关状态
  const [deviceId, setDeviceId] = useState('');
  const [deviceName, setDeviceName] = useState('测试播放器');
  const [isRegistered, setIsRegistered] = useState(false);
  const [existingDevices, setExistingDevices] = useState<DeviceInfo[]>([]);

  // 播放列表相关状态
  const [playlists, setPlaylists] = useState<PlayerPlaylist[]>([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState<PlayerPlaylist | null>(null);
  const [playlistItems, setPlaylistItems] = useState<PlaylistItem[]>([]);
  const [loadingPlaylists, setLoadingPlaylists] = useState(false);

  // 播放器状态
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loopPlay, setLoopPlay] = useState(true);

  // 日志
  const [logs, setLogs] = useState<string[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  // 心跳定时器
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 添加日志
  const addLog = useCallback((msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const logMsg = `[${timestamp}] ${msg}`;
    setLogs((prev) => [...prev.slice(-50), logMsg]);
  }, []);

  // 自动滚动日志
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  // 加载已有设备
  useEffect(() => {
    loadExistingDevices();
  }, []);

  const loadExistingDevices = async () => {
    try {
      const response = await getDeviceList();
      setExistingDevices(response.items || []);
    } catch {
      // 忽略错误
    }
  };

  // 生成新设备 ID
  const handleGenerateDeviceId = () => {
    const newId = generateUUID();
    setDeviceId(newId);
    addLog(`生成新设备 ID: ${newId}`);
  };

  // 复制设备 ID
  const handleCopyDeviceId = () => {
    if (deviceId) {
      navigator.clipboard.writeText(deviceId);
      message.success('设备 ID 已复制');
    }
  };

  // 设备注册
  const handleRegister = async () => {
    if (!deviceId) {
      message.error('请输入或生成设备 ID');
      return;
    }
    if (!deviceName) {
      message.error('请输入设备名称');
      return;
    }

    try {
      addLog(`正在注册设备: ${deviceId}`);
      const result = await registerDevice(deviceId, deviceName);
      addLog(`设备注册成功: ${result.device_name}`);
      setIsRegistered(true);
      message.success('设备注册成功');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      addLog(`注册失败: ${err.response?.data?.detail || '未知错误'}`);
      message.error('设备注册失败');
    }
  };

  // 加载所有播放列表
  const handleLoadPlaylists = async () => {
    setLoadingPlaylists(true);
    try {
      addLog('正在加载播放列表...');
      const response = await getAllPlaylists();

      // 获取每个播放列表的详情
      const playlistsWithItems: PlayerPlaylist[] = await Promise.all(
        response.items.map(async (p: { id: number; name: string; updated_at: string }) => {
          try {
            const detail = await getPlaylistDetail(p.id);
            return {
              id: p.id,
              name: p.name,
              version: p.updated_at,
              items: detail.items.map((item: {
                id: number;
                media_id: number;
                file_name: string;
                file_type: string;
                display_order: number;
                display_duration: number;
              }) => ({
                id: item.id,
                media_id: item.media_id,
                file_name: item.file_name,
                file_type: item.file_type,
                file_url: `/api/player/media/${item.media_id}/download`,
                display_order: item.display_order,
                display_duration: item.display_duration,
                file_size: 0,
                md5_hash: '',
              })),
            };
          } catch {
            return {
              id: p.id,
              name: p.name,
              version: p.updated_at,
              items: [],
            };
          }
        })
      );

      setPlaylists(playlistsWithItems);
      addLog(`加载成功，共 ${playlistsWithItems.length} 个播放列表`);
      message.success(`加载了 ${playlistsWithItems.length} 个播放列表`);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      addLog(`加载失败: ${err.response?.data?.detail || '未知错误'}`);
      message.error('加载播放列表失败');
    } finally {
      setLoadingPlaylists(false);
    }
  };

  // 选择播放列表
  const handleSelectPlaylist = (playlistId: number) => {
    const playlist = playlists.find((p) => p.id === playlistId);
    if (playlist) {
      setSelectedPlaylist(playlist);
      setPlaylistItems(playlist.items);
      setCurrentIndex(0);
      setIsPlaying(false);
      addLog(`选择播放列表: ${playlist.name}, 共 ${playlist.items.length} 个媒体项`);
    }
  };

  // 选择已有设备
  const handleSelectExistingDevice = (value: string) => {
    setDeviceId(value);
    const device = existingDevices.find((d) => d.device_id === value);
    if (device) {
      setDeviceName(device.device_name);
    }
  };

  // 开始播放
  const handlePlay = () => {
    if (playlistItems.length === 0) {
      message.warning('请先选择播放列表');
      return;
    }
    setIsPlaying(true);
    addLog(`开始播放: 第 ${currentIndex + 1} 项`);
  };

  // 暂停播放
  const handlePause = () => {
    setIsPlaying(false);
    addLog('暂停播放');
  };

  // 停止播放
  const handleStop = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
    addLog('停止播放');
  };

  // 上一项
  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      addLog(`切换到上一项: 第 ${currentIndex} 项`);
    } else if (loopPlay && playlistItems.length > 0) {
      setCurrentIndex(playlistItems.length - 1);
      addLog(`循环到最后一项: 第 ${playlistItems.length} 项`);
    }
  };

  // 下一项
  const handleNext = () => {
    if (currentIndex < playlistItems.length - 1) {
      setCurrentIndex(currentIndex + 1);
      addLog(`切换到下一项: 第 ${currentIndex + 2} 项`);
    } else if (loopPlay) {
      setCurrentIndex(0);
      addLog('循环播放: 回到第一项');
    } else {
      setIsPlaying(false);
      addLog('播放完毕');
    }
  };

  // 速度变化
  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    addLog(`设置播放速度: ${speed}X`);
  };

  // 自动播放下一项
  useEffect(() => {
    if (!isPlaying) return;

    const currentItem = playlistItems[currentIndex];
    if (!currentItem) return;

    // 根据速度计算实际显示时间
    const duration = (currentItem.display_duration * 1000) / playbackSpeed;

    const timer = setTimeout(() => {
      handleNext();
    }, duration);

    return () => clearTimeout(timer);
  }, [isPlaying, currentIndex, playlistItems, playbackSpeed, loopPlay]);

  // 启动心跳
  useEffect(() => {
    if (isRegistered && deviceId) {
      heartbeatRef.current = setInterval(async () => {
        try {
          await reportPlayerStatus(deviceId, isPlaying ? 'playing' : 'idle');
        } catch {
          addLog('心跳上报失败');
        }
      }, 30000);
    }

    return () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
    };
  }, [isRegistered, deviceId, isPlaying, addLog]);

  // 清理
  useEffect(() => {
    return () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
    };
  }, []);

  // 当前播放项
  const currentItem = playlistItems[currentIndex];

  // 获取文件类型图标和颜色
  const getFileTypeInfo = (type: string) => {
    switch (type) {
      case 'image':
        return { icon: <PictureOutlined />, color: '#52c41a', bgColor: '#f6ffed' };
      case 'video':
        return { icon: <VideoCameraOutlined />, color: '#1890ff', bgColor: '#e6f7ff' };
      case 'ppt':
        // PPT 已转换为视频，使用视频图标
        return { icon: <VideoCameraOutlined />, color: '#fa8c16', bgColor: '#fff7e6' };
      default:
        return { icon: <PlayCircleOutlined />, color: '#666', bgColor: '#f5f5f5' };
    }
  };

  return (
    <div style={{ padding: '0 0 24px 0' }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        <PlayCircleOutlined style={{ marginRight: 8 }} />
        播放端模拟器
      </Title>

      <Row gutter={24}>
        {/* 左侧：设备注册 + 播放列表选择 */}
        <Col span={8}>
          {/* 设备注册卡片 */}
          <Card
            title={
              <Space>
                <span>设备注册</span>
                {isRegistered && (
                  <Tag color="success" icon={<CheckCircleOutlined />}>
                    已注册
                  </Tag>
                )}
              </Space>
            }
            size="small"
            style={{ marginBottom: 16 }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>设备 ID</Text>
                <Input.Group compact style={{ marginTop: 8 }}>
                  <Input
                    style={{ width: 'calc(100% - 120px)' }}
                    value={deviceId}
                    onChange={(e) => setDeviceId(e.target.value)}
                    placeholder="输入或生成设备 ID"
                  />
                  <Button onClick={handleGenerateDeviceId}>生成</Button>
                  <Button icon={<CopyOutlined />} onClick={handleCopyDeviceId} />
                </Input.Group>
              </div>

              <div>
                <Text strong>设备名称</Text>
                <Input
                  style={{ marginTop: 8 }}
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  placeholder="输入设备名称"
                />
              </div>

              <Button type="primary" block onClick={handleRegister}>
                注册设备
              </Button>

              <Divider style={{ margin: '12px 0' }} />

              <Select
                style={{ width: '100%' }}
                placeholder="选择已有设备"
                onChange={handleSelectExistingDevice}
                options={existingDevices.map((d) => ({
                  label: `${d.device_name} (${d.device_id.slice(0, 8)}...)`,
                  value: d.device_id,
                }))}
              />
            </Space>
          </Card>

          {/* 播放列表选择卡片 */}
          <Card
            title={
              <Space>
                <span>播放列表</span>
                {selectedPlaylist && (
                  <Tag color="blue">{selectedPlaylist.name}</Tag>
                )}
              </Space>
            }
            size="small"
            extra={
              <Button
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                onClick={handleLoadPlaylists}
                loading={loadingPlaylists}
              >
                刷新
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                style={{ width: '100%' }}
                placeholder={playlists.length === 0 ? '点击刷新加载播放列表' : '选择播放列表'}
                onChange={handleSelectPlaylist}
                value={selectedPlaylist?.id}
                options={playlists.map((p) => ({
                  label: `${p.name} (${p.items.length} 项)`,
                  value: p.id,
                }))}
              />

              {playlistItems.length > 0 && (
                <div
                  style={{
                    maxHeight: 300,
                    overflow: 'auto',
                    border: '1px solid #f0f0f0',
                    borderRadius: 4,
                  }}
                >
                  <List
                    size="small"
                    dataSource={playlistItems}
                    renderItem={(item, index) => {
                      const typeInfo = getFileTypeInfo(item.file_type);
                      return (
                        <List.Item
                          style={{
                            backgroundColor: index === currentIndex ? '#e6f7ff' : undefined,
                            padding: '8px 12px',
                            cursor: 'pointer',
                          }}
                          onClick={() => {
                            setCurrentIndex(index);
                            addLog(`跳转到第 ${index + 1} 项: ${item.file_name}`);
                          }}
                        >
                          <List.Item.Meta
                            avatar={
                              <Avatar
                                icon={typeInfo.icon}
                                style={{ backgroundColor: typeInfo.bgColor, color: typeInfo.color }}
                                size="small"
                              />
                            }
                            title={
                              <Space>
                                <Tag color="purple" style={{ margin: 0 }}>
                                  {index + 1}
                                </Tag>
                                <Text
                                  style={{ fontSize: 12 }}
                                  ellipsis={{ tooltip: item.file_name }}
                                >
                                  {item.file_name}
                                </Text>
                              </Space>
                            }
                            description={
                              <Space size="small">
                                <Tag color={typeInfo.color} style={{ margin: 0, fontSize: 10 }}>
                                  {item.file_type}
                                </Tag>
                                <Text type="secondary" style={{ fontSize: 10 }}>
                                  {item.display_duration}s
                                </Text>
                              </Space>
                            }
                          />
                        </List.Item>
                      );
                    }}
                  />
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* 右侧：播放预览 + 控制 */}
        <Col span={16}>
          {/* 播放预览区域 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <div
              style={{
                width: '100%',
                height: 400,
                backgroundColor: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 8,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              {currentItem ? (
                currentItem.file_type === 'image' ? (
                  <img
                    src={getMediaDownloadUrl(currentItem.media_id)}
                    alt={currentItem.file_name}
                    style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                  />
                ) : (currentItem.file_type === 'video' || currentItem.file_type === 'ppt') ? (
                  <video
                    key={currentItem.id}
                    src={getMediaDownloadUrl(currentItem.media_id)}
                    style={{ maxWidth: '100%', maxHeight: '100%' }}
                    controls
                    autoPlay={isPlaying}
                  />
                ) : (
                  <div style={{ textAlign: 'center', color: '#fff' }}>
                    <PlayCircleOutlined style={{ fontSize: 64, marginBottom: 16 }} />
                    <p>请选择播放列表并开始播放</p>
                  </div>
                )
              ) : (
                <div style={{ textAlign: 'center', color: '#666' }}>
                  <PlayCircleOutlined style={{ fontSize: 64, marginBottom: 16 }} />
                  <p>请选择播放列表并开始播放</p>
                </div>
              )}

              {/* 播放状态指示器 */}
              {isPlaying && currentItem && (
                <div
                  style={{
                    position: 'absolute',
                    top: 16,
                    right: 16,
                    backgroundColor: 'rgba(0,0,0,0.6)',
                    padding: '4px 12px',
                    borderRadius: 4,
                    color: '#fff',
                  }}
                >
                  <Space>
                    <SyncOutlined spin />
                    <span>播放中 {playbackSpeed}X</span>
                  </Space>
                </div>
              )}
            </div>
          </Card>

          {/* 播放信息和控制 */}
          <Row gutter={16}>
            {/* 当前播放信息 */}
            <Col span={8}>
              <Card size="small">
                {currentItem ? (
                  <div>
                    <Statistic
                      title="当前播放"
                      value={`${currentIndex + 1} / ${playlistItems.length}`}
                    />
                    <Divider style={{ margin: '12px 0' }} />
                    <Text ellipsis={{ tooltip: currentItem.file_name }}>
                      {currentItem.file_name}
                    </Text>
                    <br />
                    <Space style={{ marginTop: 8 }}>
                      <Tag color={getFileTypeInfo(currentItem.file_type).color}>
                        {currentItem.file_type}
                      </Tag>
                      <Text type="secondary">{currentItem.display_duration}s</Text>
                    </Space>
                  </div>
                ) : (
                  <Text type="secondary">暂无播放内容</Text>
                )}
              </Card>
            </Col>

            {/* 播放控制 */}
            <Col span={8}>
              <Card title="播放控制" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {/* 播放按钮组 */}
                  <Space style={{ width: '100%', justifyContent: 'center' }}>
                    <Tooltip title="上一项">
                      <Button
                        icon={<StepBackwardOutlined />}
                        onClick={handlePrev}
                        disabled={playlistItems.length === 0}
                      />
                    </Tooltip>
                    {!isPlaying ? (
                      <Tooltip title="播放">
                        <Button
                          type="primary"
                          icon={<PlayCircleOutlined />}
                          onClick={handlePlay}
                          disabled={playlistItems.length === 0}
                          size="large"
                        />
                      </Tooltip>
                    ) : (
                      <Tooltip title="暂停">
                        <Button
                          type="primary"
                          icon={<PauseCircleOutlined />}
                          onClick={handlePause}
                          size="large"
                        />
                      </Tooltip>
                    )}
                    <Tooltip title="停止">
                      <Button
                        danger
                        icon={<StopOutlined />}
                        onClick={handleStop}
                        disabled={!isPlaying && currentIndex === 0}
                      />
                    </Tooltip>
                    <Tooltip title="下一项">
                      <Button
                        icon={<StepForwardOutlined />}
                        onClick={handleNext}
                        disabled={playlistItems.length === 0}
                      />
                    </Tooltip>
                  </Space>

                  {/* 循环播放 */}
                  <div style={{ textAlign: 'center' }}>
                    <Tag
                      color={loopPlay ? 'success' : 'default'}
                      style={{ cursor: 'pointer' }}
                      onClick={() => {
                        setLoopPlay(!loopPlay);
                        addLog(loopPlay ? '关闭循环播放' : '开启循环播放');
                      }}
                    >
                      {loopPlay ? '循环: 开' : '循环: 关'}
                    </Tag>
                  </div>
                </Space>
              </Card>
            </Col>

            {/* 播放速度 */}
            <Col span={8}>
              <Card title="播放速度" size="small">
                <Radio.Group
                  value={playbackSpeed}
                  onChange={(e) => handleSpeedChange(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {SPEED_OPTIONS.map((opt) => (
                      <Radio.Button
                        key={opt.value}
                        value={opt.value}
                        style={{ width: '100%', textAlign: 'center' }}
                      >
                        {opt.label}
                      </Radio.Button>
                    ))}
                  </Space>
                </Radio.Group>
              </Card>
            </Col>
          </Row>

          {/* 日志区域 */}
          <Card
            title="操作日志"
            size="small"
            style={{ marginTop: 16 }}
            extra={
              <Button size="small" onClick={() => setLogs([])}>
                清空
              </Button>
            }
          >
            <div
              ref={logRef}
              style={{
                height: 120,
                overflow: 'auto',
                backgroundColor: '#1e1e1e',
                color: '#d4d4d4',
                padding: 12,
                borderRadius: 4,
                fontFamily: 'Consolas, Monaco, monospace',
                fontSize: 11,
                lineHeight: 1.6,
              }}
            >
              {logs.length === 0 ? (
                <Text style={{ color: '#666' }}>暂无日志</Text>
              ) : (
                logs.map((log, index) => <div key={index}>{log}</div>)
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default PlayerSimulator;
