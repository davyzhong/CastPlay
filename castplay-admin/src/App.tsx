import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './layouts/MainLayout';
import DeviceList from './pages/DeviceList';
import MediaList from './pages/MediaList';
import PlaylistList from './pages/PlaylistList';
import Dashboard from './pages/Dashboard';
import websocketService from './services/websocket';

const App: React.FC = () => {
  useEffect(() => {
    // 初始化 WebSocket 连接
    websocketService.connect();

    // 组件卸载时断开连接
    return () => {
      websocketService.disconnect();
    };
  }, []);

  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="devices" element={<DeviceList />} />
            <Route path="media" element={<MediaList />} />
            <Route path="playlists" element={<PlaylistList />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
