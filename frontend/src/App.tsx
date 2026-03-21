import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Layout, theme, Menu } from 'antd';
import { AppstoreOutlined, DatabaseOutlined, FolderOutlined, PlayCircleOutlined, DesktopOutlined, ScheduleOutlined } from '@ant-design/icons';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DeviceList from './pages/DeviceList';
import MediaList from './pages/MediaList';
import PlaylistList from './pages/PlaylistList';
import SchedulePage from './pages/SchedulePage';
import WebPlayerSimulator from './pages/WebPlayerSimulator';
import { useState, useEffect } from 'react';
import { getToken } from './api/auth';

const { Content, Sider } = Layout;

const MainLayout: React.FC = () => {
  const {
    token: { colorBgContainer },
  } = theme.useToken();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedKey, setSelectedKey] = useState('dashboard');

  const menuItems = [
    {
      key: 'dashboard',
      icon: <AppstoreOutlined />,
      label: '仪表盘',
      path: '/',
    },
    {
      key: 'devices',
      icon: <DatabaseOutlined />,
      label: '设备管理',
      path: '/devices',
    },
    {
      key: 'media',
      icon: <FolderOutlined />,
      label: '媒体库',
      path: '/media',
    },
    {
      key: 'playlists',
      icon: <PlayCircleOutlined />,
      label: '播放列表',
      path: '/playlists',
    },
    {
      key: 'schedules',
      icon: <ScheduleOutlined />,
      label: '调度管理',
      path: '/schedules',
    },
    {
      key: 'webplayer',
      icon: <DesktopOutlined />,
      label: 'Web播放端模拟器',
      path: '/webplayer',
    },
  ];

  useEffect(() => {
    const path = location.pathname;
    if (path === '/') {
      setSelectedKey('dashboard');
    } else {
      setSelectedKey(path.substring(1));
    }
  }, [location.pathname]);

  const handleMenuClick = ({ key }: { key: string }) => {
    const menuItem = menuItems.find(item => item.key === key);
    if (menuItem) {
      navigate(menuItem.path);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="dark">
        <div style={{
          padding: '16px',
          color: '#fff',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          CastPlay
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={handleMenuClick}
          items={menuItems.map((item) => ({
            key: item.key,
            icon: item.icon,
            label: item.label,
          }))}
        />
      </Sider>
      <Layout style={{ padding: '0 24px 24px 24px', overflow: 'auto' }}>
        <Content style={{
          background: colorBgContainer,
          padding: 24,
          borderRadius: '8px',
          minHeight: 'calc(100vh - 64px)'
        }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<DeviceList />} />
            <Route path="/media" element={<MediaList />} />
            <Route path="/playlists" element={<PlaylistList />} />
            <Route path="/schedules" element={<SchedulePage />} />
            <Route path="/webplayer" element={<WebPlayerSimulator />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

/**
 * 受保护的路由组件
 * 检查用户是否已登录，未登录则重定向到登录页
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getToken();

  if (!token) {
    // 未登录，重定向到登录页
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default App;
