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
              colorPrimary: '#a8d46f',
              colorText: '#17221b',
              colorBgLayout: '#ecebe3',
              colorBorder: '#d7d8cc',
              borderRadius: 12,
              fontFamily:
                '"Aptos", "Microsoft YaHei", "PingFang SC", sans-serif',
            },
            components: {
              Layout: {
                bodyBg: '#ecebe3',
                siderBg: '#132019',
              },
              Menu: {
                darkItemBg: '#132019',
                darkItemColor: '#aebbb2',
                darkItemHoverBg: '#1c2c22',
                darkItemSelectedBg: '#a8d46f',
                darkItemSelectedColor: '#132019',
                itemBorderRadius: 10,
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
