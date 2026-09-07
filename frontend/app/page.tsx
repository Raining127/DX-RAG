'use client';

import { Layout } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
import FileUpload from '@/components/FileUpload';
import FileManager from '@/components/FileManager';
import KnowledgeBaseManager from '@/components/KnowledgeBaseManager';
import QAPanel from '@/components/QAPanel';
import SideMenu, { type MenuKey } from '@/components/SideMenu';
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
    eyebrow: 'COLLECTIONS / 01',
    title: '知识库管理',
    description: '管理彼此隔离的知识空间，为后续上传、检索与问答建立清晰边界。',
  },
  upload: {
    eyebrow: 'INGESTION / 02',
    title: '文件上传',
    description: '将原始资料送入解析、切分与向量化流水线，并保留可追踪的处理结果。',
  },
  qa: {
    eyebrow: 'RETRIEVAL / 03',
    title: '知识问答',
    description: '在指定知识库中检索上下文，让回答与可核验来源保持同一条证据链。',
  },
  files: {
    eyebrow: 'ARCHIVE / 04',
    title: '文件管理',
    description: '查看已入库文件及其处理状态，并通过不可变文件身份执行精确操作。',
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
  const [collections, setCollections] = useState<Collection[]>([]);
  const [collectionState, setCollectionState] =
    useState<CollectionState>('loading');
  const [collectionError, setCollectionError] = useState('');
  const [collectionMutation, setCollectionMutation] =
    useState<CollectionMutation | null>(null);
  const collectionRequestVersionRef = useRef(0);
  const collectionMutationRevisionRef = useRef(0);
  const panel = PANELS[selectedKey];

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
              <FileUpload {...collectionSource} />
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
              />
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
