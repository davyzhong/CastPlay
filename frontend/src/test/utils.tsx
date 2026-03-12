/**
 * 测试工具函数
 */
import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'

// All-in-one Provider 包装器
const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  )
}

// 自定义 render 函数
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options })
}

// 重新导出所有 testing-library 的内容
export * from '@testing-library/react'
export { customRender as render }
