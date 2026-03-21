/**
 * 加载状态 UI 组件
 * 提供全屏和局部加载状态显示
 */
import React from 'react';
import { Spin, Typography, Progress, Space } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

interface LoadingOverlayProps {
  /** 是否显示 */
  visible: boolean;
  /** 加载提示文本 */
  tip?: string;
  /** 进度百分比 (0-100)，如果提供则显示进度条 */
  progress?: number;
  /** 是否显示为全屏模式 */
  fullscreen?: boolean;
  /** 子组件（在加载时显示为半透明） */
  children?: React.ReactNode;
  /** 自定义背景色 */
  background?: string;
  /** 自定义 z-index */
  zIndex?: number;
}

/**
 * 加载状态覆盖层组件
 */
export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  tip = '加载中...',
  progress,
  fullscreen = false,
  children,
  background = 'rgba(0, 0, 0, 0.7)',
  zIndex = 1000,
}) => {
  if (!visible) {
    return <>{children}</>;
  }

  const overlayStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background,
    zIndex,
    transition: 'opacity 0.3s ease',
  };

  if (fullscreen) {
    return (
      <div
        style={{
          ...overlayStyle,
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
        }}
      >
        <LoadingContent tip={tip} progress={progress} />
      </div>
    );
  }

  // 如果有子组件，显示为覆盖层
  if (children) {
    return (
      <div style={{ position: 'relative', width: '100%', height: '100%' }}>
        {children}
        <div
          style={{
            ...overlayStyle,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
          }}
        >
          <LoadingContent tip={tip} progress={progress} />
        </div>
      </div>
    );
  }

  // 没有子组件，显示为块级元素
  return (
    <div
      style={{
        ...overlayStyle,
        padding: 40,
        borderRadius: 8,
      }}
    >
      <LoadingContent tip={tip} progress={progress} />
    </div>
  );
};

/**
 * 加载内容组件
 */
const LoadingContent: React.FC<{
  tip: string;
  progress?: number;
}> = ({ tip, progress }) => {
  const hasProgress = progress !== undefined && progress >= 0;

  return (
    <Space direction="vertical" size="large" align="center">
      {/* 加载动画 */}
      <Spin
        indicator={<LoadingOutlined style={{ fontSize: 48, color: '#fff' }} />}
      />

      {/* 提示文本 */}
      <Text style={{ color: '#fff', fontSize: 16 }}>
        {tip}
      </Text>

      {/* 进度条 */}
      {hasProgress && (
        <div style={{ width: 200 }}>
          <Progress
            percent={Math.min(100, Math.max(0, progress))}
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            trailColor="rgba(255, 255, 255, 0.2)"
          />
        </div>
      )}
    </Space>
  );
};

/**
 * 全屏加载组件（简写）
 */
export const FullscreenLoading: React.FC<{
  visible: boolean;
  tip?: string;
  progress?: number;
}> = ({ visible, tip, progress }) => (
  <LoadingOverlay
    visible={visible}
    tip={tip}
    progress={progress}
    fullscreen
  />
);

/**
 * 启动加载界面
 * 用于应用启动时显示品牌和加载状态
 */
export const StartupLoading: React.FC<{
  visible: boolean;
  message?: string;
  progress?: number;
  brandName?: string;
}> = ({
  visible,
  message = '正在初始化...',
  progress,
  brandName = 'CastPlay'
}) => {
  if (!visible) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        zIndex: 9999,
      }}
    >
      {/* 品牌名称 */}
      <Title
        level={1}
        style={{
          color: '#fff',
          marginBottom: 40,
          fontWeight: 300,
          letterSpacing: 4,
        }}
      >
        {brandName}
      </Title>

      {/* 加载动画 */}
      <Spin
        indicator={<LoadingOutlined style={{ fontSize: 48, color: '#1890ff' }} />}
      />

      {/* 消息 */}
      <Text
        style={{
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: 14,
          marginTop: 24,
        }}
      >
        {message}
      </Text>

      {/* 进度条 */}
      {progress !== undefined && (
        <div style={{ width: 240, marginTop: 24 }}>
          <Progress
            percent={Math.min(100, Math.max(0, progress))}
            status="active"
            strokeColor={{
              '0%': '#1890ff',
              '100%': '#52c41a',
            }}
            trailColor="rgba(255, 255, 255, 0.1)"
          />
        </div>
      )}
    </div>
  );
};

/**
 * 内联加载组件
 * 用于组件内部的加载状态
 */
export const InlineLoading: React.FC<{
  loading: boolean;
  tip?: string;
  children: React.ReactNode;
  delay?: number;
}> = ({ loading, tip = '加载中...', children, delay = 200 }) => {
  const [showLoading, setShowLoading] = React.useState(false);

  React.useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (loading) {
      timer = setTimeout(() => setShowLoading(true), delay);
    } else {
      setShowLoading(false);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [loading, delay]);

  if (!loading) {
    return <>{children}</>;
  }

  if (!showLoading) {
    return <>{children}</>;
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
      }}
    >
      <Space>
        <Spin size="small" />
        <Text type="secondary">{tip}</Text>
      </Space>
    </div>
  );
};

export default LoadingOverlay;
