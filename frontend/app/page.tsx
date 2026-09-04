'use client';

import { Layout } from 'antd';
import { useState } from 'react';
import SideMenu, { type MenuKey } from '@/components/SideMenu';

const { Content, Sider } = Layout;

interface PanelDefinition {
  eyebrow: string;
  title: string;
  description: string;
  nextStep: string;
  sequence: string;
}

const PANELS: Record<MenuKey, PanelDefinition> = {
  'knowledge-base': {
    eyebrow: 'COLLECTIONS / 01',
    title: '知识库管理',
    description: '管理彼此隔离的知识空间，为后续上传、检索与问答建立清晰边界。',
    nextStep: '集合列表与创建、重命名、删除操作将在 Phase 11 接入。',
    sequence: 'Define → Isolate → Manage',
  },
  upload: {
    eyebrow: 'INGESTION / 02',
    title: '文件上传',
    description: '将原始资料送入解析、切分与向量化流水线，并保留可追踪的处理结果。',
    nextStep: '知识库选择、文件校验与上传状态将在 Phase 11 接入。',
    sequence: 'Validate → Parse → Index',
  },
  qa: {
    eyebrow: 'RETRIEVAL / 03',
    title: '知识问答',
    description: '在指定知识库中检索上下文，让回答与可核验来源保持同一条证据链。',
    nextStep: '对话、Markdown 回答与来源引用将在 Phase 11 接入。',
    sequence: 'Retrieve → Ground → Answer',
  },
  files: {
    eyebrow: 'ARCHIVE / 04',
    title: '文件管理',
    description: '查看已入库文件及其处理状态，并通过不可变文件身份执行精确操作。',
    nextStep: '文件列表、内容预览与删除确认将在 Phase 11 接入。',
    sequence: 'Inspect → Preview → Govern',
  },
};

export default function Home() {
  const [selectedKey, setSelectedKey] = useState<MenuKey>('knowledge-base');
  const panel = PANELS[selectedKey];

  return (
    <Layout className="app-shell">
      <Sider
        className="app-sider"
        width={280}
        breakpoint="lg"
        collapsedWidth={0}
        aria-label="应用侧边栏"
      >
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            DX
          </div>
          <div>
            <p className="brand-name">DX—RAG</p>
            <p className="brand-caption">Knowledge workspace</p>
          </div>
        </div>

        <div className="rail-label">WORKSPACES</div>
        <SideMenu selectedKey={selectedKey} onSelect={setSelectedKey} />

        <div className="sider-footer">
          <span className="status-dot" aria-hidden="true" />
          <div>
            <p>Foundation online</p>
            <span>Phase 10 · application shell</span>
          </div>
        </div>
      </Sider>

      <Layout className="workspace-layout">
        <header className="workspace-header">
          <div>
            <span className="header-kicker">LOCAL KNOWLEDGE SYSTEM</span>
            <span className="header-separator" aria-hidden="true" />
            <span className="header-version">V1 / TRUSTED NETWORK</span>
          </div>
          <span className="shell-state">SHELL READY</span>
        </header>

        <Content className="workspace-content">
          <section className="panel-heading" aria-labelledby="panel-title">
            <div>
              <p className="panel-eyebrow">{panel.eyebrow}</p>
              <h1 id="panel-title">{panel.title}</h1>
              <p className="panel-description">{panel.description}</p>
            </div>
            <div className="phase-stamp" aria-label="当前阶段 Phase 10">
              <span>PHASE</span>
              <strong>10</strong>
            </div>
          </section>

          <section
            key={selectedKey}
            className="placeholder-panel"
            data-panel-key={selectedKey}
            aria-live="polite"
          >
            <div className="placeholder-grid" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>

            <div className="placeholder-content">
              <span className="placeholder-index">{panel.eyebrow.slice(-2)}</span>
              <div className="placeholder-copy">
                <p className="placeholder-label">MODULE PLACEHOLDER</p>
                <h2>{panel.title}工作区已就绪</h2>
                <p>{panel.nextStep}</p>
              </div>
            </div>

            <footer className="placeholder-footer">
              <span>{panel.sequence}</span>
              <span>UI MODULE / DEFERRED TO PHASE 11</span>
            </footer>
          </section>
        </Content>
      </Layout>
    </Layout>
  );
}
