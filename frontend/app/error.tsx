'use client';

import { Button, Result } from 'antd';

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ reset }: ErrorPageProps) {
  return (
    <main className="route-error-shell" role="alert" aria-live="assertive">
      <div className="route-error-panel">
        <span className="route-error-label">WORKSPACE INTERRUPTED / RECOVERABLE</span>
        <Result
          status="error"
          title="界面发生意外错误"
          subTitle="当前功能区域未能正常显示。你可以重新加载该区域，已保存的后端数据不会受到影响。"
          extra={
            <Button type="primary" onClick={reset}>
              重新加载功能区域
            </Button>
          }
        />
      </div>
    </main>
  );
}
