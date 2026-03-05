import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout, ConfigProvider, theme } from 'antd';
import { AppstoreOutlined, DatabaseOutlined, FolderOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useStore } from './store';
import getToken from './api/auth';

const { Content, Sider } = Layout;

const MainLayout: React.FC = () => {
  const {
    token: { colorBgContainer },
  } = theme.useToken();
  const user = useStore((state) => state.user);
  const logout = useStore((state) => state.logout);

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
  ];

  if (!user || !getToken()) {
    return <Navigate to="/login" replace />;
  }

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
        <Layout.Menu
          theme="dark"
          mode="inline"
          selectedKeys={[window.location.pathname.split('/')[1]]}
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
            <Route path="/" element={
              <div>
                <h1>仪表盘</h1>
                <p>欢迎使用 CastPlay 数字标牌管理系统</p>
              </div>
            } />
            <Route path="/devices" element={<import('./pages/DeviceList').default />} />
            <Route path="/media" element={<import('./pages/MediaList').default />} />
            <Route path="/playlists" element={<import('./pages/PlaylistList').default />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<import('./pages/Login').default />} />
      <Route path="/*" element={<MainLayout />} />
    </Routes>
  );
};

export default App;
