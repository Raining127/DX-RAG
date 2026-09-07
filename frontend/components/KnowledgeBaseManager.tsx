'use client';

import {
  Alert,
  Button,
  Empty,
  Input,
  Modal,
  Popconfirm,
  Skeleton,
} from 'antd';
import { useMemo, useState } from 'react';
import {
  ApiError,
  createCollection,
  deleteCollection,
  renameCollection,
} from '@/lib/api-client';
import type { CollectionState } from '@/lib/collection-state';
import type { Collection } from '@/lib/types';
import {
  COLLECTION_NAME_REQUIREMENT,
  validateCollectionName,
} from '@/lib/validators';

type ViewState = 'loading' | 'success' | 'empty' | 'error';

interface OperationError {
  message: string;
  retry?: () => void;
}

interface KnowledgeBaseManagerProps {
  collections: Collection[];
  collectionState: CollectionState;
  collectionError: string;
  onRetryCollections: () => void;
  onCollectionCreated: (name: string) => void;
  onCollectionRenamed: (oldName: string, newName: string) => void;
  onCollectionDeleted: (name: string) => void;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return '操作未完成，请稍后重试。';
}

export default function KnowledgeBaseManager({
  collections,
  collectionState,
  collectionError,
  onRetryCollections,
  onCollectionCreated,
  onCollectionRenamed,
  onCollectionDeleted,
}: KnowledgeBaseManagerProps) {
  const [operationError, setOperationError] =
    useState<OperationError | null>(null);
  const [notice, setNotice] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createTouched, setCreateTouched] = useState(false);
  const [createError, setCreateError] = useState('');

  const [renameTarget, setRenameTarget] = useState<Collection | null>(null);
  const [renameName, setRenameName] = useState('');
  const [renameTouched, setRenameTouched] = useState(false);
  const [renameError, setRenameError] = useState('');

  const [pendingAction, setPendingAction] = useState<string | null>(null);

  const totalFiles = useMemo(
    () => collections.reduce((total, item) => total + item.file_count, 0),
    [collections],
  );
  const viewState: ViewState =
    collectionState === 'ready' ? 'success' : collectionState;

  const openCreateModal = () => {
    setCreateName('');
    setCreateTouched(false);
    setCreateError('');
    setNotice('');
    setOperationError(null);
    setCreateOpen(true);
  };

  const closeCreateModal = () => {
    if (pendingAction !== 'create') {
      setCreateOpen(false);
    }
  };

  const handleCreate = async () => {
    setCreateTouched(true);
    const validationError = validateCollectionName(createName);
    if (validationError) {
      return;
    }

    setPendingAction('create');
    setCreateError('');

    try {
      const response = await createCollection(createName);
      onCollectionCreated(response.name);
      setCreateOpen(false);
      setNotice(`知识库 “${response.name}” 已创建。`);
    } catch (error) {
      setCreateError(getErrorMessage(error));
    } finally {
      setPendingAction(null);
    }
  };

  const openRenameModal = (collection: Collection) => {
    setRenameTarget(collection);
    setRenameName(collection.name);
    setRenameTouched(false);
    setRenameError('');
    setNotice('');
    setOperationError(null);
  };

  const closeRenameModal = () => {
    if (pendingAction !== 'rename') {
      setRenameTarget(null);
    }
  };

  const renameValidationError = renameTarget && renameName === renameTarget.name
    ? '新名称需要与当前名称不同'
    : validateCollectionName(renameName);

  const handleRename = async () => {
    if (!renameTarget) {
      return;
    }

    setRenameTouched(true);
    if (renameValidationError) {
      return;
    }

    setPendingAction('rename');
    setRenameError('');

    try {
      const response = await renameCollection(renameTarget.name, renameName);
      onCollectionRenamed(response.old_name, response.new_name);
      setRenameTarget(null);
      setNotice(
        `知识库 “${response.old_name}” 已重命名为 “${response.new_name}”。`,
      );
    } catch (error) {
      setRenameError(getErrorMessage(error));
    } finally {
      setPendingAction(null);
    }
  };

  const handleDelete = async (name: string) => {
    const actionKey = `delete:${name}`;
    setPendingAction(actionKey);
    setOperationError(null);
    setNotice('');

    try {
      await deleteCollection(name);
      onCollectionDeleted(name);
      setNotice(`知识库 “${name}” 已删除。`);
    } catch (error) {
      setOperationError({
        message: getErrorMessage(error),
        retry: () => void handleDelete(name),
      });
    } finally {
      setPendingAction(null);
    }
  };

  const createValidationError = validateCollectionName(createName);

  return (
    <section className="kb-manager" aria-label="知识库列表" aria-live="polite">
      <header className="kb-toolbar">
        <div className="kb-summary">
          <div>
            <span className="kb-summary-value">{collections.length}</span>
            <span className="kb-summary-label">COLLECTIONS</span>
          </div>
          <div>
            <span className="kb-summary-value">{totalFiles}</span>
            <span className="kb-summary-label">INDEXED FILES</span>
          </div>
        </div>
        <Button type="primary" size="large" onClick={openCreateModal}>
          创建知识库
        </Button>
      </header>

      {notice ? (
        <Alert
          className="kb-alert"
          type="success"
          showIcon
          closable
          message={notice}
          onClose={() => setNotice('')}
        />
      ) : null}

      {operationError ? (
        <Alert
          className="kb-alert"
          type="error"
          showIcon
          closable
          message="操作未完成"
          description={operationError.message}
          onClose={() => setOperationError(null)}
          action={
            operationError.retry ? (
              <Button size="small" danger onClick={operationError.retry}>
                重试
              </Button>
            ) : undefined
          }
        />
      ) : null}

      <div className="kb-content" data-state={viewState}>
        {viewState === 'loading' ? (
          <div className="kb-skeleton-grid" aria-label="正在加载知识库">
            {[0, 1, 2].map((item) => (
              <div className="kb-skeleton-card" key={item}>
                <Skeleton active paragraph={{ rows: 2 }} title={{ width: '58%' }} />
              </div>
            ))}
          </div>
        ) : null}

        {viewState === 'error' ? (
          <Alert
            className="kb-load-error"
            type="error"
            showIcon
            message="无法读取知识库"
            description={collectionError}
            action={
              <Button danger onClick={onRetryCollections}>
                重新加载
              </Button>
            }
          />
        ) : null}

        {viewState === 'empty' ? (
          <Empty
            className="kb-empty"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <strong>暂无知识库，点击创建</strong>
                <span>先建立一个隔离空间，再开始上传与检索。</span>
              </div>
            }
          >
            <Button type="primary" onClick={openCreateModal}>
              创建第一个知识库
            </Button>
          </Empty>
        ) : null}

        {viewState === 'success' ? (
          <div className="kb-grid">
            {collections.map((collection, index) => {
              const deleting = pendingAction === `delete:${collection.name}`;

              return (
                <article className="kb-card" key={collection.name}>
                  <div className="kb-card-index" aria-hidden="true">
                    {String(index + 1).padStart(2, '0')}
                  </div>
                  <div className="kb-card-body">
                    <p className="kb-card-label">KNOWLEDGE BASE</p>
                    <h2>{collection.name}</h2>
                    <p className="kb-file-count">
                      <strong>{collection.file_count}</strong>
                      <span>个已索引文件</span>
                    </p>
                  </div>
                  <footer className="kb-card-actions">
                    <Button
                      type="text"
                      disabled={deleting}
                      onClick={() => openRenameModal(collection)}
                    >
                      重命名
                    </Button>
                    <Popconfirm
                      title="删除这个知识库？"
                      description="将级联删除其中的文件、切片与索引，且无法恢复。"
                      okText="确认删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true, loading: deleting }}
                      onConfirm={() => handleDelete(collection.name)}
                    >
                      <Button type="text" danger loading={deleting}>
                        删除
                      </Button>
                    </Popconfirm>
                  </footer>
                </article>
              );
            })}
          </div>
        ) : null}
      </div>

      <Modal
        title="创建知识库"
        open={createOpen}
        okText="创建"
        cancelText="取消"
        confirmLoading={pendingAction === 'create'}
        okButtonProps={{ disabled: Boolean(createValidationError) }}
        onOk={() => void handleCreate()}
        onCancel={closeCreateModal}
        destroyOnClose
      >
        <div className="kb-modal-copy">
          <p>知识库彼此隔离，名称也将用于后端 Collection 与上传目录。</p>
          <label htmlFor="create-collection-name">知识库名称</label>
          <Input
            id="create-collection-name"
            value={createName}
            status={createTouched && createValidationError ? 'error' : undefined}
            placeholder="例如 product-handbook"
            autoFocus
            showCount
            onChange={(event) => {
              setCreateName(event.target.value);
              setCreateTouched(true);
              setCreateError('');
            }}
            onPressEnter={() => void handleCreate()}
          />
          <p
            className={
              createTouched && createValidationError
                ? 'kb-field-note kb-field-note-error'
                : 'kb-field-note'
            }
          >
            {createTouched && createValidationError
              ? createValidationError
              : COLLECTION_NAME_REQUIREMENT}
          </p>
          {createError ? (
            <Alert
              type="error"
              showIcon
              message="创建失败"
              description={`${createError} 修正后可再次点击“创建”重试。`}
            />
          ) : null}
        </div>
      </Modal>

      <Modal
        title={`重命名 ${renameTarget?.name ?? ''}`}
        open={Boolean(renameTarget)}
        okText="保存新名称"
        cancelText="取消"
        confirmLoading={pendingAction === 'rename'}
        okButtonProps={{ disabled: Boolean(renameValidationError) }}
        onOk={() => void handleRename()}
        onCancel={closeRenameModal}
        destroyOnClose
      >
        <div className="kb-modal-copy">
          <p>重命名会同步更新 Collection、文件目录与已入库切片的引用。</p>
          <label htmlFor="rename-collection-name">新名称</label>
          <Input
            id="rename-collection-name"
            value={renameName}
            status={renameTouched && renameValidationError ? 'error' : undefined}
            autoFocus
            showCount
            onChange={(event) => {
              setRenameName(event.target.value);
              setRenameTouched(true);
              setRenameError('');
            }}
            onPressEnter={() => void handleRename()}
          />
          <p
            className={
              renameTouched && renameValidationError
                ? 'kb-field-note kb-field-note-error'
                : 'kb-field-note'
            }
          >
            {renameTouched && renameValidationError
              ? renameValidationError
              : COLLECTION_NAME_REQUIREMENT}
          </p>
          {renameError ? (
            <Alert
              type="error"
              showIcon
              message="重命名失败"
              description={`${renameError} 修正后可再次点击“保存新名称”重试。`}
            />
          ) : null}
        </div>
      </Modal>
    </section>
  );
}
