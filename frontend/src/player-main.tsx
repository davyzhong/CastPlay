/**
 * 播放端独立入口
 * 用于真实设备播放
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import PlayerPage from './pages/PlayerPage';

// 简单的全局错误处理
window.onerror = (message, source, lineno, colno, error) => {
  console.error('Global error:', { message, source, lineno, colno, error });
  return false;
};

window.onunhandledrejection = (event) => {
  console.error('Unhandled rejection:', event.reason);
};

// 注意：已移除右键和快捷键限制，方便调试
// 生产环境可以通过配置项控制

// 渲染播放端
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PlayerPage />
  </React.StrictMode>
);
