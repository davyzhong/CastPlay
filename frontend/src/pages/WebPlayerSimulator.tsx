/**
 * Web 播放端模拟器
 * 自动化模拟 Android 播放端功能
 *
 * 自动流程：
 * 1. 页面加载时自动生成设备ID（基于MAC地址）并注册
 * 2. 自动连接 WebSocket
 * 3. 自动加载播放列表并开始播放
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Tag,
  Typography,
  List,
  Tooltip,
  Statistic,
  Badge,
  Descriptions,
  App,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  CheckCircleOutlined,
  VideoCameraOutlined,
  PictureOutlined,
  StepBackwardOutlined,
  StepForwardOutlined,
  SyncOutlined,
  WifiOutlined,
  DisconnectOutlined,
  BugOutlined,
  ClockCircleOutlined,
  CodeOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import {
  registerDevice,
  reportPlayerStatus,
  getMediaDownloadUrl,
  playerInit,
  getAllPlaylists,
  getPlaylistDetail,
} from '../api/player';
import type { PlayerPlaylist, PlaylistItem, PlayerInitResponse } from '../api/player';

const { Title, Text } = Typography;

// 生成随机 MAC 地址（用于显示）
const generateRandomMAC = (): string => {
  const prefix = '02:00:00';
  const suffix = Array.from({ length: 3 }, () =>
    Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
  ).join(':');
  return `${prefix}:${suffix}`.toUpperCase();
};

// 使用独立的 localStorage key（与 PlayerCore 区分，作为模拟器设备）
const DEVICE_STORAGE_KEY = 'simulator_device_id';

// 使用固定的设备 ID（用于持久化测试配置）
const FIXED_SIMULATOR_DEVICE_ID = 'web-player-sim-01';

// 获取设备 UUID（使用固定 ID，确保配置持久化）
const getOrCreateDeviceUUID = (): string => {
  // 始终使用固定的设备 ID
  localStorage.setItem(DEVICE_STORAGE_KEY, FIXED_SIMULATOR_DEVICE_ID);
  return FIXED_SIMULATOR_DEVICE_ID;
};

// 清除设备 UUID（实际上不会清除，因为使用固定 ID）
const clearDeviceUUID = (): void => {
  localStorage.removeItem(DEVICE_STORAGE_KEY);
  localStorage.removeItem('webplayer_device_uuid'); // 清理旧 key
  localStorage.removeItem('webplayer_mac_address'); // 清理旧数据
};

// 播放速度选项
const SPEED_OPTIONS = [
  { label: '1X', value: 1 },
  { label: '2X', value: 2 },
  { label: '4X', value: 4 },
  { label: '8X', value: 8 },
];

// WebSocket 消息类型
interface WSMessage {
  event: string;
  device_id: number | string;
  action: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

// 日志条目
interface LogEntry {
  id: number;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
}

const WebPlayerSimulator: React.FC = () => {
  const { modal } = App.useApp();

  // ============================================================================
  // 状态管理
  // ============================================================================

  // 初始化状态
  const [initState, setInitState] = useState<'loading' | 'registering' | 'connecting' | 'ready' | 'error'>('loading');
  const [initError, setInitError] = useState<string | null>(null);

  // 设备信息
  const [deviceUUID, setDeviceUUID] = useState('');
  const [macAddress, setMacAddress] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [registrationCode, setRegistrationCode] = useState('');
  const [deviceInfo, setDeviceInfo] = useState<PlayerInitResponse['device'] | null>(null);

  // 播放列表
  const [playlists, setPlaylists] = useState<PlayerPlaylist[]>([]);
  const [currentPlaylist, setCurrentPlaylist] = useState<PlayerPlaylist | null>(null);
  const [playlistItems, setPlaylistItems] = useState<PlaylistItem[]>([]);

  // 定时配置
  const [scheduleConfig, setScheduleConfig] = useState<PlayerInitResponse['schedule']>(null);

  // 播放器状态
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loopPlay, setLoopPlay] = useState(true);
  const [playlistRotationEnabled, setPlaylistRotationEnabled] = useState(false);
  const [currentPlaylistIndex, setCurrentPlaylistIndex] = useState(0);
  const [allPlaylistsLoading, setAllPlaylistsLoading] = useState(false);

  // WebSocket
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // 日志
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logLevel, setLogLevel] = useState<'all' | 'info' | 'warn' | 'error' | 'debug'>('all');
  const logIdRef = useRef(0);
  const logRef = useRef<HTMLDivElement>(null);

  // 定时器引用
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ============================================================================
  // 日志系统
  // ============================================================================

  const addLog = useCallback((level: LogEntry['level'], msg: string) => {
    const entry: LogEntry = {
      id: ++logIdRef.current,
      timestamp: new Date().toLocaleTimeString(),
      level,
      message: msg,
    };
    setLogs((prev) => [...prev.slice(-100), entry]);
  }, []);

  // 自动滚动日志
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error': return '#ff4d4f';
      case 'warn': return '#faad14';
      case 'debug': return '#8c8c8c';
      default: return '#d4d4d4';
    }
  };

  // ============================================================================
  // 自动初始化流程
  // ============================================================================

  useEffect(() => {
    initializePlayer();
  }, []);

  const initializePlayer = async () => {
    try {
      // 1. 获取或创建设备 UUID（存储在 localStorage 中，确保同一浏览器始终使用相同的设备 ID）
      setInitState('loading');
      const uuid = getOrCreateDeviceUUID();
      setDeviceUUID(uuid);
      setDeviceId(uuid);
      addLog('info', `设备 UUID: ${uuid}`);

      // 生成用于显示的 MAC 地址（仅用于友好显示）
      const displayMAC = generateRandomMAC();
      setMacAddress(displayMAC);

      // 2. 注册设备
      setInitState('registering');
      addLog('info', '正在注册设备...');
      try {
        const registerResponse = await registerDevice(uuid, 'web_browser');
        if (registerResponse.registration_code) {
          setRegistrationCode(registerResponse.registration_code);
          addLog('info', `设备注册成功，注册码: ${registerResponse.registration_code}`);
        } else {
          addLog('info', '设备注册成功');
        }
      } catch (err: unknown) {
        const error = err as { response?: { data?: { detail?: string } } };
        // 设备可能已注册，继续初始化
        addLog('debug', `注册响应: ${error.response?.data?.detail || '继续初始化'}`);
      }

      // 3. 初始化播放端
      addLog('info', '正在初始化播放端...');
      const initResponse: PlayerInitResponse = await playerInit(uuid);

      setDeviceInfo(initResponse.device);
      setScheduleConfig(initResponse.schedule);
      // 如果服务端返回了注册码，更新本地状态
      if (initResponse.device.registration_code) {
        setRegistrationCode(initResponse.device.registration_code);
      }
      addLog('info', `设备名称: ${initResponse.device.device_name}`);

      // 4. 加载播放列表
      if (initResponse.playlists && initResponse.playlists.length > 0) {
        setPlaylists(initResponse.playlists);
        // 自动选择第一个播放列表
        const firstPlaylist = initResponse.playlists[0];
        setCurrentPlaylistIndex(0);
        setCurrentPlaylist(firstPlaylist);
        setPlaylistItems(firstPlaylist.items);
        addLog('info', `加载播放列表: ${firstPlaylist.name}, 共 ${firstPlaylist.items.length} 项`);
      } else {
        addLog('warn', '没有分配播放列表');
      }

      // 5. 连接 WebSocket
      setInitState('connecting');
      connectWebSocket(uuid);

      // 6. 启动心跳
      startHeartbeat(uuid);

      // 7. 自动开始播放
      setInitState('ready');
      if (initResponse.playlists && initResponse.playlists.length > 0 && initResponse.playlists[0].items.length > 0) {
        setIsPlaying(true);
        addLog('info', '自动开始播放');
      }

    } catch (error: unknown) {
      const err = error as { message?: string };
      setInitState('error');
      setInitError(err.message || '初始化失败');
      addLog('error', `初始化失败: ${err.message || '未知错误'}`);
    }
  };

  // ============================================================================
  // WebSocket 连接
  // ============================================================================

  const connectWebSocket = (devId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const url = `${wsProtocol}//${wsHost}/ws/${devId}`;

    addLog('info', `连接 WebSocket: ${url}`);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setWsConnected(true);
        addLog('info', 'WebSocket 连接成功');
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          handleWSMessage(msg);
        } catch {
          addLog('warn', '无法解析 WebSocket 消息');
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        addLog('warn', 'WebSocket 连接关闭，5秒后重连...');
        setTimeout(() => connectWebSocket(devId), 5000);
      };

      ws.onerror = () => {
        addLog('error', 'WebSocket 连接错误');
        setWsConnected(false);
      };

      wsRef.current = ws;
    } catch {
      addLog('error', 'WebSocket 连接失败');
    }
  };

  const handleWSMessage = (msg: WSMessage) => {
    addLog('debug', `收到消息: ${msg.event}`);

    switch (msg.event) {
      case 'playlist_update':
        addLog('info', '收到播放列表更新通知');
        // 重新初始化
        if (deviceId) {
          playerInit(deviceId).then((response) => {
            setPlaylists(response.playlists);
            if (response.playlists.length > 0) {
              // 尝试保持当前播放列表的选择
              const currentId = currentPlaylist?.id;
              const foundIndex = response.playlists.findIndex((p: PlayerPlaylist) => p.id === currentId);
              const playlistIndex = foundIndex >= 0 ? foundIndex : 0;
              setCurrentPlaylistIndex(playlistIndex);
              setCurrentPlaylist(response.playlists[playlistIndex]);
              setPlaylistItems(response.playlists[playlistIndex].items);
            }
          });
        }
        break;

      case 'schedule_update':
        addLog('info', '收到定时配置更新通知');
        if (deviceId) {
          playerInit(deviceId).then((response) => {
            setScheduleConfig(response.schedule);
          });
        }
        break;

      case 'force_sync':
        addLog('info', '收到强制同步命令');
        if (deviceId) {
          playerInit(deviceId);
        }
        break;

      case 'reboot':
        addLog('warn', '收到重启命令（模拟）');
        modal.info({
          title: '重启命令',
          content: '收到服务端重启命令',
        });
        break;

      default:
        addLog('debug', `未知消息: ${msg.event}`);
    }
  };

  // ============================================================================
  // 心跳
  // ============================================================================

  const startHeartbeat = (devId: string) => {
    heartbeatRef.current = setInterval(async () => {
      try {
        await reportPlayerStatus(devId, isPlaying ? 'playing' : 'idle');
        addLog('debug', '心跳上报成功');
      } catch {
        addLog('warn', '心跳上报失败');
      }
    }, 30000);
  };

  // ============================================================================
  // 播放控制
  // ============================================================================

  const handlePlay = () => {
    if (playlistItems.length === 0) return;
    setIsPlaying(true);
    addLog('info', '开始播放');
  };

  const handlePause = () => {
    setIsPlaying(false);
    addLog('info', '暂停播放');
  };

  const handleStop = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
    addLog('info', '停止播放');
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    } else if (loopPlay && playlistItems.length > 0) {
      setCurrentIndex(playlistItems.length - 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < playlistItems.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else if (loopPlay) {
      // 当前播放列表播完
      if (playlistRotationEnabled && playlists.length > 1) {
        // 启用列表轮播，切换到下一个播放列表
        const nextPlaylistIndex = (currentPlaylistIndex + 1) % playlists.length;
        const nextPlaylist = playlists[nextPlaylistIndex];
        setCurrentPlaylistIndex(nextPlaylistIndex);
        setCurrentPlaylist(nextPlaylist);
        setPlaylistItems(nextPlaylist.items);
        setCurrentIndex(0);
        addLog('info', `切换到下一个播放列表: ${nextPlaylist.name}`);
      } else {
        // 不启用列表轮播，循环当前列表
        setCurrentIndex(0);
      }
    } else {
      setIsPlaying(false);
      addLog('info', '播放完毕');
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    addLog('info', `播放速度: ${speed}X`);
  };

  // 自动播放下一项（视频和PPT由 onEnded 处理，图片使用定时器）
  useEffect(() => {
    if (!isPlaying || playlistItems.length === 0) return;

    const currentItem = playlistItems[currentIndex];
    if (!currentItem) return;

    // 视频和PPT由播放器的 onEnded 事件处理
    if (currentItem.file_type === 'video' || currentItem.file_type === 'ppt') {
      return;
    }

    // 图片使用定时器
    const duration = (currentItem.display_duration * 1000) / playbackSpeed;

    playbackTimerRef.current = setTimeout(() => {
      handleNext();
    }, duration);

    return () => {
      if (playbackTimerRef.current) {
        clearTimeout(playbackTimerRef.current);
      }
    };
  }, [isPlaying, currentIndex, playlistItems, playbackSpeed, loopPlay]);

  // ============================================================================
  // 切换播放列表
  // ============================================================================

  const handleSelectPlaylist = (playlistId: number) => {
    const playlistIndex = playlists.findIndex((p) => p.id === playlistId);
    const playlist = playlists[playlistIndex];
    if (playlist) {
      setCurrentPlaylistIndex(playlistIndex);
      setCurrentPlaylist(playlist);
      setPlaylistItems(playlist.items);
      setCurrentIndex(0);
      setIsPlaying(true);
      addLog('info', `切换播放列表: ${playlist.name}`);
    }
  };

  // 加载系统中所有播放列表（测试模式）
  const handleLoadAllPlaylists = async () => {
    setAllPlaylistsLoading(true);
    try {
      const response = await getAllPlaylists();
      const allPlaylists = response.items || [];

      // 转换为 PlayerPlaylist 格式并加载详情
      const playerPlaylists: PlayerPlaylist[] = [];
      for (const p of allPlaylists) {
        try {
          const detail = await getPlaylistDetail(p.id);
          playerPlaylists.push({
            id: detail.id,
            name: detail.name,
            version: detail.updated_at,
            is_system: detail.is_system,
            items: (detail.items || []).map((item: any) => ({
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
          });
        } catch (err) {
          addLog('warn', `加载播放列表 ${p.name} 失败`);
        }
      }

      setPlaylists(playerPlaylists);
      if (playerPlaylists.length > 0) {
        const firstPlaylist = playerPlaylists[0];
        setCurrentPlaylistIndex(0);
        setCurrentPlaylist(firstPlaylist);
        setPlaylistItems(firstPlaylist.items);
        addLog('info', `已加载 ${playerPlaylists.length} 个播放列表（测试模式）`);
      }
    } catch (err: unknown) {
      const error = err as { message?: string };
      addLog('error', `加载播放列表失败: ${error.message || '未知错误'}`);
    } finally {
      setAllPlaylistsLoading(false);
    }
  };

  // 重置设备（清除本地存储的设备 UUID，下次加载时会生成新设备）
  const handleResetDevice = () => {
    modal.confirm({
      title: '重置设备',
      content: '确定要重置设备吗？这将清除当前设备信息并生成新的设备 ID。该操作不可撤销。',
      okText: '确定重置',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        clearDeviceUUID();
        addLog('info', '设备已重置，正在重新初始化...');
        setInitState('loading');
        setPlaylists([]);
        setCurrentPlaylist(null);
        setPlaylistItems([]);
        setRegistrationCode('');
        setTimeout(() => {
          initializePlayer();
        }, 500);
      },
    });
  };

  // ============================================================================
  // 清理
  // ============================================================================

  useEffect(() => {
    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // ============================================================================
  // 渲染
  // ============================================================================

  const currentItem = playlistItems[currentIndex];

  const getFileTypeInfo = (type: string) => {
    switch (type) {
      case 'image': return { icon: <PictureOutlined />, color: '#52c41a', bgColor: '#f6ffed' };
      case 'video': return { icon: <VideoCameraOutlined />, color: '#1890ff', bgColor: '#e6f7ff' };
      case 'ppt': return { icon: <VideoCameraOutlined />, color: '#fa8c16', bgColor: '#fff7e6' };
      default: return { icon: <PlayCircleOutlined />, color: '#666', bgColor: '#f5f5f5' };
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (logLevel === 'all') return true;
    return log.level === logLevel;
  });

  // 加载状态渲染
  if (initState === 'loading' || initState === 'registering' || initState === 'connecting') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
        <LoadingOutlined style={{ fontSize: 48, marginBottom: 24 }} />
        <Title level={4}>
          {initState === 'loading' && '正在初始化...'}
          {initState === 'registering' && '正在注册设备...'}
          {initState === 'connecting' && '正在连接服务器...'}
        </Title>
        <Text type="secondary">设备 ID: {deviceId || '生成中...'}</Text>
      </div>
    );
  }

  // 错误状态渲染
  if (initState === 'error') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
        <Title level={4} type="danger">初始化失败</Title>
        <Text type="secondary">{initError}</Text>
        <Button type="primary" style={{ marginTop: 16 }} onClick={initializePlayer}>
          重试
        </Button>
      </div>
    );
  }

  return (
    <div style={{ padding: '0 0 24px 0' }}>
      {/* 顶部状态栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          <PlayCircleOutlined style={{ marginRight: 8 }} />
          Web 播放端模拟器
        </Title>
        <Space>
          <Tag color={wsConnected ? 'success' : 'default'}>
            {wsConnected ? <WifiOutlined /> : <DisconnectOutlined />}
            {' '}{wsConnected ? '已连接' : '未连接'}
          </Tag>
          {deviceInfo && (
            <Tooltip title={`MAC: ${macAddress} | ID: ${deviceId}`}>
              <Tag color="success" icon={<CheckCircleOutlined />}>
                {deviceInfo.device_name}
              </Tag>
            </Tooltip>
          )}
          <Tooltip title="重置设备（生成新的设备 ID）">
            <Button size="small" danger onClick={handleResetDevice}>
              重置
            </Button>
          </Tooltip>
        </Space>
      </div>

      <Row gutter={16}>
        {/* 左侧：播放列表和设备信息 */}
        <Col span={6}>
          {/* 播放列表 */}
          <Card
            title={
              <Space>
                <span>播放列表</span>
                <Button
                  type="link"
                  size="small"
                  onClick={handleLoadAllPlaylists}
                  loading={allPlaylistsLoading}
                  style={{ padding: 0 }}
                >
                  加载所有
                </Button>
              </Space>
            }
            size="small"
            style={{ marginBottom: 16 }}
          >
            {playlists.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 16 }}>
                <Text type="secondary">可加载系统中所有播放列表进行测试</Text>
                <Button
                  type="primary"
                  block
                  onClick={handleLoadAllPlaylists}
                  loading={allPlaylistsLoading}
                  style={{ marginTop: 8 }}
                >
                  加载所有播放列表
                </Button>
              </div>
            ) : playlists.length > 0 ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                {playlists.map((p) => (
                  <Button
                    key={p.id}
                    block
                    type={currentPlaylist?.id === p.id ? 'primary' : 'default'}
                    onClick={() => handleSelectPlaylist(p.id)}
                  >
                    {p.name} ({p.items.length} 项)
                  </Button>
                ))}

                {playlistItems.length > 0 && (
                  <div style={{ maxHeight: 250, overflow: 'auto', border: '1px solid #f0f0f0', borderRadius: 4, marginTop: 8 }}>
                    <List
                      size="small"
                      dataSource={playlistItems}
                      renderItem={(item, index) => {
                        const typeInfo = getFileTypeInfo(item.file_type);
                        return (
                          <List.Item
                            style={{
                              backgroundColor: index === currentIndex ? '#e6f7ff' : undefined,
                              padding: '4px 8px',
                              cursor: 'pointer',
                            }}
                            onClick={() => {
                              setCurrentIndex(index);
                              addLog('debug', `跳转到第 ${index + 1} 项`);
                            }}
                          >
                            <Space size="small">
                              <Tag color="purple">{index + 1}</Tag>
                              <Text ellipsis style={{ fontSize: 11, maxWidth: 120 }}>
                                {item.file_name}
                              </Text>
                              <Tag color={typeInfo.color} style={{ fontSize: 10 }}>
                                {item.display_duration}s
                              </Tag>
                            </Space>
                          </List.Item>
                        );
                      }}
                    />
                  </div>
                )}
              </Space>
            ) : (
              <Text type="secondary">没有分配播放列表</Text>
            )}
          </Card>

          {/* 设备信息 */}
          {deviceInfo && (
            <Card title="设备信息" size="small" style={{ marginBottom: 16 }}>
              {/* 注册码突出显示 */}
              {registrationCode && (
                <div style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: 8,
                  padding: '12px 16px',
                  marginBottom: 12,
                  textAlign: 'center',
                }}>
                  <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12, marginBottom: 4 }}>
                    设备注册码
                  </div>
                  <Text
                    copyable
                    style={{
                      color: '#fff',
                      fontSize: 18,
                      fontFamily: 'monospace',
                      fontWeight: 'bold',
                      letterSpacing: 2,
                    }}
                  >
                    {registrationCode}
                  </Text>
                  <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 10, marginTop: 4 }}>
                    在设备管理页面使用此注册码识别设备
                  </div>
                </div>
              )}
              <Descriptions size="small" column={1}>
                <Descriptions.Item label="名称">{deviceInfo.device_name}</Descriptions.Item>
                <Descriptions.Item label="UUID">
                  <Text copyable style={{ fontSize: 10 }}>{deviceUUID}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="时区">{deviceInfo.timezone}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {/* 定时配置 */}
          {scheduleConfig && scheduleConfig.is_enabled && (
            <Card
              title={<Space><ClockCircleOutlined /><span>定时配置</span></Space>}
              size="small"
            >
              <Descriptions size="small" column={1}>
                <Descriptions.Item label="开机">{scheduleConfig.power_on_time}</Descriptions.Item>
                <Descriptions.Item label="关机">{scheduleConfig.power_off_time}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </Col>

        {/* 中间：播放预览和控制 */}
        <Col span={12}>
          {/* 播放预览 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <div
              style={{
                width: '100%',
                height: 380,
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
                ) : (
                  <video
                    key={currentItem.id}
                    src={getMediaDownloadUrl(currentItem.media_id)}
                    style={{ maxWidth: '100%', maxHeight: '100%' }}
                    controls
                    autoPlay={isPlaying}
                    onEnded={handleNext}
                  />
                )
              ) : (
                <div style={{ textAlign: 'center', color: '#666' }}>
                  <PlayCircleOutlined style={{ fontSize: 48, marginBottom: 8 }} />
                  <p>无播放内容</p>
                </div>
              )}

              {isPlaying && currentItem && (
                <div
                  style={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    backgroundColor: 'rgba(0,0,0,0.7)',
                    padding: '2px 8px',
                    borderRadius: 4,
                    color: '#fff',
                    fontSize: 12,
                  }}
                >
                  <Space>
                    <SyncOutlined spin />
                    <span>{playbackSpeed}X | {currentIndex + 1}/{playlistItems.length}</span>
                  </Space>
                </div>
              )}
            </div>
          </Card>

          {/* 播放控制 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16} align="middle">
              <Col span={10}>
                <Space>
                  <Tooltip title="上一项">
                    <Button icon={<StepBackwardOutlined />} onClick={handlePrev} size="small" />
                  </Tooltip>
                  {!isPlaying ? (
                    <Button type="primary" icon={<PlayCircleOutlined />} onClick={handlePlay} size="small">
                      播放
                    </Button>
                  ) : (
                    <Button icon={<PauseCircleOutlined />} onClick={handlePause} size="small">
                      暂停
                    </Button>
                  )}
                  <Tooltip title="停止">
                    <Button danger icon={<StopOutlined />} onClick={handleStop} size="small" />
                  </Tooltip>
                  <Tooltip title="下一项">
                    <Button icon={<StepForwardOutlined />} onClick={handleNext} size="small" />
                  </Tooltip>
                </Space>
              </Col>
              <Col span={4} style={{ textAlign: 'center' }}>
                <Space direction="vertical" size="small">
                  <Tag
                    color={loopPlay ? 'success' : 'default'}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setLoopPlay(!loopPlay)}
                  >
                    {loopPlay ? '循环: 开' : '循环: 关'}
                  </Tag>
                  {playlists.length > 1 && (
                    <Tag
                      color={playlistRotationEnabled ? 'processing' : 'default'}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setPlaylistRotationEnabled(!playlistRotationEnabled)}
                    >
                      {playlistRotationEnabled ? '列表轮播: 开' : '列表轮播: 关'}
                    </Tag>
                  )}
                </Space>
              </Col>
              <Col span={10}>
                <Space>
                  <Text>速度:</Text>
                  {SPEED_OPTIONS.map((opt) => (
                    <Button
                      key={opt.value}
                      size="small"
                      type={playbackSpeed === opt.value ? 'primary' : 'default'}
                      onClick={() => handleSpeedChange(opt.value)}
                    >
                      {opt.label}
                    </Button>
                  ))}
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 播放信息 */}
          <Row gutter={16}>
            <Col span={8}>
              <Card size="small">
                {currentItem ? (
                  <>
                    <Statistic title="当前播放" value={`${currentIndex + 1} / ${playlistItems.length}`} valueStyle={{ fontSize: 20 }} />
                    <Text ellipsis style={{ fontSize: 11 }}>{currentItem.file_name}</Text>
                  </>
                ) : (
                  <Text type="secondary">暂无播放内容</Text>
                )}
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic title="播放列表" value={currentPlaylist?.name || '-'} valueStyle={{ fontSize: 14 }} />
                <Text type="secondary" style={{ fontSize: 11 }}>{playlistItems.length} 个媒体项</Text>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic title="设备状态" value={isPlaying ? '播放中' : '空闲'} valueStyle={{ fontSize: 14 }} />
              </Card>
            </Col>
          </Row>

          {/* 日志 */}
          <Card
            title={<Space><CodeOutlined /><span>操作日志</span></Space>}
            size="small"
            style={{ marginTop: 16 }}
            extra={
              <Space>
                <select
                  value={logLevel}
                  onChange={(e) => setLogLevel(e.target.value as typeof logLevel)}
                  style={{ fontSize: 11 }}
                >
                  <option value="all">全部</option>
                  <option value="info">信息</option>
                  <option value="warn">警告</option>
                  <option value="error">错误</option>
                </select>
                <Button size="small" onClick={() => setLogs([])}>清空</Button>
              </Space>
            }
          >
            <div
              ref={logRef}
              style={{
                height: 120,
                overflow: 'auto',
                backgroundColor: '#1e1e1e',
                color: '#d4d4d4',
                padding: 8,
                borderRadius: 4,
                fontFamily: 'Consolas, Monaco, monospace',
                fontSize: 10,
                lineHeight: 1.5,
              }}
            >
              {filteredLogs.length === 0 ? (
                <Text style={{ color: '#666' }}>暂无日志</Text>
              ) : (
                filteredLogs.map((log) => (
                  <div key={log.id} style={{ color: getLogColor(log.level) }}>
                    [{log.timestamp}] [{log.level.toUpperCase()}] {log.message}
                  </div>
                ))
              )}
            </div>
          </Card>
        </Col>

        {/* 右侧：调试面板 */}
        <Col span={6}>
          <Card title={<Space><BugOutlined /><span>调试设置</span></Space>} size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Button size="small" block onClick={() => deviceId && playerInit(deviceId)}>
                重新初始化
              </Button>
              <Button size="small" block onClick={() => setIsPlaying(!isPlaying)}>
                {isPlaying ? '模拟暂停' : '模拟播放'}
              </Button>
              <Button
                size="small"
                block
                onClick={() => {
                  modal.info({
                    title: '模拟重启',
                    content: '设备将模拟重启过程...',
                  });
                  addLog('warn', '设备模拟重启');
                }}
              >
                模拟重启
              </Button>
            </Space>
          </Card>

          <Card title="API 端点" size="small" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10 }}>
              <p><Text code>POST /api/player/init</Text></p>
              <p><Text code>POST /api/player/status</Text></p>
              <p><Text code>GET /api/player/media/:id/download</Text></p>
              <p><Text code>WS /ws/:device_id</Text></p>
            </div>
          </Card>

          {/* 网络状态指示器 */}
          <Card title="状态监控" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>WebSocket</Text>
                <Badge status={wsConnected ? 'success' : 'default'} text={wsConnected ? '已连接' : '未连接'} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>播放状态</Text>
                <Tag color={isPlaying ? 'green' : 'default'}>{isPlaying ? '播放中' : '空闲'}</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>播放列表</Text>
                <Text>{playlists.length} 个</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>媒体项</Text>
                <Text>{playlistItems.length} 个</Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default WebPlayerSimulator;
