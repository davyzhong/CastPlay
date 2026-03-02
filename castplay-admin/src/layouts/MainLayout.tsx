import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  MobileOutlined,
  FileImageOutlined,
  PlaySquareOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const MainLayout: React.FC = () => {
  const location = useLocation();

  // 根据当前路径获取菜单选中项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path.startsWith('/devices')) return 'devices';
    if (path.startsWith('/media')) return 'media';
    if (path.startsWith('/playlists')) return 'playlists';
    return 'dashboard';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="dark">
        <div style={{ height: 32, margin: 16, color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
          CastPlay
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[getSelectedKey()]}>
          <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
            <Link to="/dashboard">仪表盘</Link>
          </Menu.Item>
          <Menu.Item key="devices" icon={<MobileOutlined />}>
            <Link to="/devices">设备管理</Link>
          </Menu.Item>
          <Menu.Item key="media" icon={<FileImageOutlined />}>
            <Link to="/media">媒体库</Link>
          </Menu.Item>
          <Menu.Item key="playlists" icon={<PlaySquareOutlined />}>
            <Link to="/playlists">播放列表</Link>
          </Menu.Item>
        </Menu>
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}>
          <h2>CastPlay 管理后台</h2>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
