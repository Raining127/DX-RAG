'use client';

import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import type { ReactNode } from 'react';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <ConfigProvider
          locale={zhCN}
          theme={{
            token: {
              colorPrimary: '#42654c',
              colorText: '#24342b',
              colorBgLayout: '#f5f6f3',
              colorBorder: '#dce2d9',
              borderRadius: 8,
              controlHeight: 38,
              fontFamily:
                '"Aptos", "Microsoft YaHei", "PingFang SC", sans-serif',
            },
            components: {
              Layout: {
                bodyBg: '#f5f6f3',
                siderBg: '#1c2c24',
              },
              Menu: {
                darkItemBg: '#1c2c24',
                darkItemColor: '#b7c6bc',
                darkItemHoverBg: '#2a3c31',
                darkItemSelectedBg: '#354e3e',
                darkItemSelectedColor: '#f1f6ef',
                itemBorderRadius: 8,
              },
            },
          }}
        >
          {children}
        </ConfigProvider>
      </body>
    </html>
  );
}
