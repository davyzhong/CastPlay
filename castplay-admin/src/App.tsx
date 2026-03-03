import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './layouts/MainLayout';
import DeviceList from './pages/DeviceList';
import MediaList from './pages/MediaList';
import PlaylistList from './pages/PlaylistList';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import websocketService from './services/websocket';
import { TokenManager } from './api/client';

// 受保护路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();

  if (!TokenManager.isAuthenticated()) {
    // 未登录，重定向到登录页，保存当前路径
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  useEffect(() => {
    // 仅在已登录时初始化 WebSocket 连接
    if (TokenManager.isAuthenticated()) {
      websocketService.connect();
    }

    // 组件卸载时断开连接
    return () => {
      websocketService.disconnect();
    };
  }, []);

  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          {/* 登录页 - 公开访问 */}
          <Route path="/login" element={<Login />} />

          {/* 受保护的路由 */}
          <Route path="/" element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }>
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
