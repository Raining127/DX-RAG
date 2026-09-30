'use client';

import { Button, Drawer, Layout } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
import FileUpload from '@/components/FileUpload';
import FileManager from '@/components/FileManager';
import KnowledgeBaseManager from '@/components/KnowledgeBaseManager';
import QAPanel from '@/components/QAPanel';
import SideMenu, { type MenuKey } from '@/components/SideMenu';
import WorkspaceIcon from '@/components/WorkspaceIcon';
import { ApiError, listCollections } from '@/lib/api-client';
import type {
  CollectionMutation,
  CollectionState,
} from '@/lib/collection-state';
import type { Collection } from '@/lib/types';

const { Content, Sider } = Layout;

interface PanelDefinition {
  eyebrow: string;
  title: string;
  description: string;
}

const PANELS: Record<MenuKey, PanelDefinition> = {
  'knowledge-base': {
    eyebrow: '你的知识空间',
    title: '知识库管理',
    description: '按主题整理资料，为每个知识空间建立清晰的边界。',
  },
  upload: {
    eyebrow: '让资料成为知识',
    title: '文件上传',
    description: '选择知识库并上传文档，完成后即可基于资料提问。',
  },
  qa: {
    eyebrow: '连接问题与知识',
    title: '知识问答',
    description: '从你的资料中寻找答案，每次回答都可以展开查看参考来源。',
  },
  files: {
    eyebrow: '资料一目了然',
    title: '文件管理',
    description: '查看已入库的资料，预览内容并管理文件。',
  },
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return '无法读取知识库列表，请稍后重试。';
}

export default function Home() {
  const [selectedKey, setSelectedKey] = useState<MenuKey>('knowledge-base');
  const [isNarrowViewport, setIsNarrowViewport] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [fileRevisions, setFileRevisions] = useState<Record<string, number>>({});
  const [collectionState, setCollectionState] =
    useState<CollectionState>('loading');
  const [collectionError, setCollectionError] = useState('');
  const [collectionMutation, setCollectionMutation] =
    useState<CollectionMutation | null>(null);
  const collectionRequestVersionRef = useRef(0);
  const collectionMutationRevisionRef = useRef(0);
  const panel = PANELS[selectedKey];
  const handlePanelSelect = (key: MenuKey) => {
    setSelectedKey(key);
    setMobileNavOpen(false);
  };

  const loadCollections = useCallback(async () => {
    const requestVersion = collectionRequestVersionRef.current + 1;
    collectionRequestVersionRef.current = requestVersion;
    setCollectionState('loading');
    setCollectionError('');

    try {
      const response = await listCollections();
      if (requestVersion !== collectionRequestVersionRef.current) {
        return;
      }
      setCollections(response.collections);
      setCollectionMutation(null);
      setCollectionState(response.collections.length > 0 ? 'ready' : 'empty');
    } catch (error) {
      if (requestVersion !== collectionRequestVersionRef.current) {
        return;
      }
      setCollectionError(getErrorMessage(error));
      setCollectionState('error');
    }
  }, []);

  useEffect(() => {
    void loadCollections();
  }, [loadCollections]);

  const handleCollectionCreated = useCallback((name: string) => {
    collectionRequestVersionRef.current += 1;
    collectionMutationRevisionRef.current += 1;
    setCollections((current) => [...current, { name, file_count: 0 }]);
    setCollectionMutation({
      revision: collectionMutationRevisionRef.current,
      type: 'create',
      name,
    });
    setCollectionState('ready');
    setCollectionError('');
  }, []);

  const handleCollectionRenamed = useCallback(
    (oldName: string, newName: string) => {
      collectionRequestVersionRef.current += 1;
      collectionMutationRevisionRef.current += 1;
      setCollections((current) =>
        current.map((collection) =>
          collection.name === oldName
            ? { ...collection, name: newName }
            : collection,
        ),
      );
      setCollectionMutation({
        revision: collectionMutationRevisionRef.current,
        type: 'rename',
        oldName,
        newName,
      });
      setCollectionState('ready');
      setCollectionError('');
    },
    [],
  );

  const handleCollectionDeleted = useCallback(
    (name: string) => {
      collectionRequestVersionRef.current += 1;
      collectionMutationRevisionRef.current += 1;
      const remaining = collections.filter(
        (collection) => collection.name !== name,
      );
      setCollections(remaining);
      setCollectionMutation({
        revision: collectionMutationRevisionRef.current,
        type: 'delete',
        name,
      });
      setCollectionState(remaining.length > 0 ? 'ready' : 'empty');
      setCollectionError('');
    },
    [collections],
  );

  const handleFileUploaded = useCallback((collectionName: string) => {
    setCollections((current) =>
      current.map((collection) =>
        collection.name === collectionName
          ? { ...collection, file_count: collection.file_count + 1 }
          : collection,
      ),
    );
    setFileRevisions((current) => ({
      ...current,
      [collectionName]: (current[collectionName] ?? 0) + 1,
    }));
  }, []);

  const handleFileDeleted = useCallback((collectionName: string) => {
    setCollections((current) =>
      current.map((collection) =>
        collection.name === collectionName
          ? { ...collection, file_count: Math.max(0, collection.file_count - 1) }
          : collection,
      ),
    );
  }, []);

  const collectionSource = {
    collections,
    collectionState,
    collectionError,
    collectionMutation,
    onRetryCollections: () => void loadCollections(),
  };

  return (
    <Layout className="app-shell">
      <Sider
        className="app-sider"
        width={232}
        breakpoint="lg"
        collapsedWidth={0}
        collapsed={isNarrowViewport}
        onBreakpoint={setIsNarrowViewport}
        trigger={null}
        aria-hidden={isNarrowViewport}
        aria-label="应用侧边栏"
      >
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            <WorkspaceIcon name="knowledge-base" />
          </div>
          <div>
            <p className="brand-name">DX-RAG</p>
            <p className="brand-caption">知识工作台</p>
          </div>
        </div>

        <div className="rail-label">工作空间</div>
        <SideMenu selectedKey={selectedKey} onSelect={handlePanelSelect} />

        <div className="sider-footer">
          <div>
            <p>让知识，触手可及。</p>
            <span>整理资料 · 提问 · 查看来源</span>
          </div>
        </div>
      </Sider>

      <Drawer
        className="mobile-navigation"
        title="DX-RAG · 知识工作台"
        placement="left"
        width={280}
        open={isNarrowViewport && mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      >
        <div id="mobile-workspace-navigation">
          <SideMenu selectedKey={selectedKey} onSelect={handlePanelSelect} />
        </div>
      </Drawer>

      <Layout className="workspace-layout">
        <header className="workspace-header">
          <div className="workspace-breadcrumb">
            <Button
              className="mobile-menu-toggle"
              type="text"
              aria-label="打开导航"
              aria-expanded={mobileNavOpen}
              aria-controls="mobile-workspace-navigation"
              icon={<WorkspaceIcon name="menu" />}
              onClick={() => setMobileNavOpen(true)}
            />
            <span className="header-kicker">知识工作台</span>
            <span className="header-separator" aria-hidden="true">/</span>
            <span className="header-current">{panel.title}</span>
          </div>
          <span className="workspace-badge">
            {process.env.NEXT_PUBLIC_PREVIEW_MODE === '1' ? '演示预览' : '本地工作空间'}
          </span>
        </header>

        <Content className={`workspace-content${selectedKey === 'qa' ? ' workspace-content-qa' : ''}`}>
          <section className="panel-heading" aria-labelledby="panel-title">
            <div>
              <p className="panel-eyebrow">{panel.eyebrow}</p>
              <h1 id="panel-title">{panel.title}</h1>
              <p className="panel-description">{panel.description}</p>
            </div>
          </section>

          <div className="feature-panels">
            <div
              className="feature-panel"
              data-panel-key="knowledge-base"
              hidden={selectedKey !== 'knowledge-base'}
            >
              <KnowledgeBaseManager
                collections={collections}
                collectionState={collectionState}
                collectionError={collectionError}
                onRetryCollections={() => void loadCollections()}
                onCollectionCreated={handleCollectionCreated}
                onCollectionRenamed={handleCollectionRenamed}
                onCollectionDeleted={handleCollectionDeleted}
              />
            </div>
            <div
              className="feature-panel"
              data-panel-key="upload"
              hidden={selectedKey !== 'upload'}
            >
              <FileUpload {...collectionSource} onFileUploaded={handleFileUploaded} />
            </div>
            <div
              className="feature-panel"
              data-panel-key="qa"
              hidden={selectedKey !== 'qa'}
            >
              <QAPanel {...collectionSource} />
            </div>
            <div
              className="feature-panel"
              data-panel-key="files"
              hidden={selectedKey !== 'files'}
            >
              <FileManager
                {...collectionSource}
                onFileDeleted={handleFileDeleted}
                fileRevisions={fileRevisions}
              />
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
