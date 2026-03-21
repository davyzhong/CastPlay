/**
 * 设置按钮组件
 * 悬浮在播放器右上角的齿轮图标，用于重新打开服务器配置
 */
import React, { useState } from 'react';
import { Button } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { ServerConfigDialog } from './ServerConfigDialog';

interface SettingsButtonProps {
  /** 点击回调（如果提供，则由父组件控制对话框） */
  onClick?: () => void;
  /** 是否显示对话框（由父组件控制时使用） */
  dialogVisible?: boolean;
  /** 对话框关闭回调 */
  onDialogClose?: () => void;
}

export const SettingsButton: React.FC<SettingsButtonProps> = ({
  onClick,
  dialogVisible,
  onDialogClose,
}) => {
  const [internalVisible, setInternalVisible] = useState(false);

  // 如果父组件提供 onClick，则由父组件控制
  // 否则内部管理状态
  const isControlled = onClick !== undefined;
  const visible = isControlled ? dialogVisible : internalVisible;

  const handleClick = () => {
    if (isControlled) {
      onClick();
    } else {
      setInternalVisible(true);
    }
  };

  const handleClose = () => {
    if (isControlled) {
      onDialogClose?.();
    } else {
      setInternalVisible(false);
    }
  };

  const handleConfigured = () => {
    handleClose();
  };

  return (
    <>
      {/* 设置按钮 - 固定在右上角 */}
      <div
        style={{
          position: 'fixed',
          top: 16,
          right: 16,
          zIndex: 1000,
        }}
      >
        <Button
          type="text"
          icon={<SettingOutlined />}
          onClick={handleClick}
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
            color: '#fff',
            border: 'none',
            width: 40,
            height: 40,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.6)';
            e.currentTarget.style.transform = 'scale(1.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.4)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
          title="服务器设置"
        />
      </div>

      {/* 配置对话框（仅非受控模式时渲染） */}
      {!isControlled && (
        <ServerConfigDialog
          visible={visible || false}
          onConfigured={handleConfigured}
          onCancel={handleClose}
          isInitialSetup={false}
        />
      )}
    </>
  );
};
