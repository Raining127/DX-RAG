'use client';

import {
  Alert,
  Button,
  Empty,
  Modal,
  Popconfirm,
  Select,
  Skeleton,
  Table,
  Tag,
} from 'antd';
import type { TableColumnsType } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ApiError,
  deleteFile,
  listFiles,
  previewFile,
} from '@/lib/api-client';
import {
  type CollectionSourceProps,
  resolveCollectionSelection,
} from '@/lib/collection-state';
import type { FileRecord, PreviewResponse } from '@/lib/types';

type FileState = 'idle' | 'loading' | 'success' | 'empty' | 'error';
type PreviewState = 'idle' | 'loading' | 'success' | 'error';

interface ActionError {
  message: string;
  retry: () => void;
}

interface FileManagerProps extends CollectionSourceProps {
  onFileDeleted: (collectionName: string) => void;
}

const ERROR_MESSAGES: Record<string, string> = {
  COLLECTION_NOT_FOUND: '所选知识库不存在，请刷新知识库列表后重试。',
  FILE_NOT_FOUND: '该文件已不存在，请重新加载文件列表。',
  NETWORK_ERROR: '无法连接后端服务，请检查服务状态后重试。',
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.code] ?? error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return '操作未完成，请稍后重试。';
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const units = ['KB', 'MB', 'GB'];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value >= 10 ? value.toFixed(1) : value.toFixed(2)} ${units[unitIndex]}`;
}

function formatUploadTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

export default function FileManager({
  collections,
  collectionState,
  collectionError,
  collectionMutation,
  onRetryCollections,
  onFileDeleted,
}: FileManagerProps) {
  const [selectedCollection, setSelectedCollection] = useState<string>();

  const [files, setFiles] = useState<FileRecord[]>([]);
  const [fileState, setFileState] = useState<FileState>('idle');
  const [fileError, setFileError] = useState('');
  const [actionError, setActionError] = useState<ActionError | null>(null);
  const [notice, setNotice] = useState('');
  const [deletingFileId, setDeletingFileId] = useState<string | null>(null);

  const [previewTarget, setPreviewTarget] = useState<FileRecord | null>(null);
  const [previewState, setPreviewState] = useState<PreviewState>('idle');
  const [previewResult, setPreviewResult] = useState<PreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState('');

  const fileRequestVersionRef = useRef(0);
  const previewRequestVersionRef = useRef(0);
  const selectedCollectionRef = useRef<string>();
  const handledMutationRevisionRef = useRef(0);

  const loadFileList = useCallback(async (collectionName: string) => {
    const requestVersion = fileRequestVersionRef.current + 1;
    fileRequestVersionRef.current = requestVersion;
    setFileState('loading');
    setFileError('');
    setActionError(null);
    setNotice('');

    try {
      const response = await listFiles(collectionName);
      if (requestVersion !== fileRequestVersionRef.current) {
        return;
      }
      setFiles(response.files);
      setFileState(response.files.length > 0 ? 'success' : 'empty');
    } catch (error) {
      if (requestVersion !== fileRequestVersionRef.current) {
        return;
      }
      setFiles([]);
      setFileError(getErrorMessage(error));
      setFileState('error');
    }
  }, []);

  const closePreview = useCallback(() => {
    previewRequestVersionRef.current += 1;
    setPreviewTarget(null);
    setPreviewState('idle');
    setPreviewResult(null);
    setPreviewError('');
  }, []);

  const resolvedCollection = resolveCollectionSelection(
    selectedCollection,
    collections,
    collectionMutation,
    handledMutationRevisionRef.current,
  );

  useEffect(() => {
    if (
      collectionState === 'loading' ||
      collectionState === 'error'
    ) {
      return;
    }

    if (collectionMutation) {
      handledMutationRevisionRef.current = collectionMutation.revision;
    }
    if (resolvedCollection === selectedCollection) {
      return;
    }

    closePreview();
    selectedCollectionRef.current = resolvedCollection;
    setSelectedCollection(resolvedCollection);
    if (resolvedCollection) {
      void loadFileList(resolvedCollection);
    } else {
      fileRequestVersionRef.current += 1;
      setFiles([]);
      setFileError('');
      setFileState('idle');
      setActionError(null);
      setNotice('');
    }
  }, [
    closePreview,
    collectionMutation,
    collectionState,
    loadFileList,
    resolvedCollection,
    selectedCollection,
  ]);

  const handleCollectionChange = (collectionName: string) => {
    closePreview();
    selectedCollectionRef.current = collectionName;
    setSelectedCollection(collectionName);
    void loadFileList(collectionName);
  };

  const loadPreview = async (file: FileRecord) => {
    if (!resolvedCollection) {
      return;
    }

    const requestVersion = previewRequestVersionRef.current + 1;
    previewRequestVersionRef.current = requestVersion;
    setPreviewTarget(file);
    setPreviewState('loading');
    setPreviewResult(null);
    setPreviewError('');

    try {
      const response = await previewFile(file.file_id, resolvedCollection);
      if (requestVersion !== previewRequestVersionRef.current) {
        return;
      }
      setPreviewResult(response);
      setPreviewState('success');
    } catch (error) {
      if (requestVersion !== previewRequestVersionRef.current) {
        return;
      }
      setPreviewError(getErrorMessage(error));
      setPreviewState('error');
    }
  };

  const handleDelete = async (file: FileRecord) => {
    if (!resolvedCollection) {
      return;
    }

    const collectionName = resolvedCollection;
    setDeletingFileId(file.file_id);
    setActionError(null);
    setNotice('');

    try {
      const response = await deleteFile(file.file_id, collectionName);
      if (selectedCollectionRef.current !== collectionName) {
        return;
      }
      const remaining = files.filter((item) => item.file_id !== file.file_id);
      setFiles(remaining);
      onFileDeleted(collectionName);
      setFileState(remaining.length > 0 ? 'success' : 'empty');
      setNotice(`文件 “${response.file_name}” 已从 ${response.collection_name} 删除。`);
      if (previewTarget?.file_id === file.file_id) {
        closePreview();
      }
    } catch (error) {
      if (selectedCollectionRef.current !== collectionName) {
        return;
      }
      setActionError({
        message: getErrorMessage(error),
        retry: () => void handleDelete(file),
      });
    } finally {
      setDeletingFileId(null);
    }
  };

  const columns: TableColumnsType<FileRecord> = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 250,
      render: (fileName: string, record) => (
        <div className="file-name-cell">
          <span className="file-extension">
            {fileName.includes('.') ? fileName.split('.').pop()?.toUpperCase() : 'FILE'}
          </span>
          <div>
            <strong>{fileName}</strong>
            <small title={record.file_id}>ID · {record.file_id.slice(0, 8)}</small>
          </div>
        </div>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 110,
      render: (size: number) => <span className="file-mono">{formatFileSize(size)}</span>,
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      width: 170,
      render: (uploadTime: string) => (
        <span className="file-time">{formatUploadTime(uploadTime)}</span>
      ),
    },
    {
      title: '切片',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 90,
      align: 'right',
      render: (count: number) => <span className="file-chunk-count">{count}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 170,
      render: (status: FileRecord['status']) => (
        <Tag color={status === 'SUCCESS' ? 'success' : 'warning'}>
          {status === 'SUCCESS' ? '已入库' : '已入库 · 有警告'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 150,
      render: (_, record) => {
        const deleting = deletingFileId === record.file_id;
        return (
          <div className="file-actions">
            <Button type="text" disabled={deleting} onClick={() => void loadPreview(record)}>
              预览
            </Button>
            <Popconfirm
              title="永久删除这个文件？"
              description="将级联删除原文件、所有切片、向量与元数据，并使关键词索引失效。此操作无法恢复。"
              okText="确认永久删除"
              cancelText="取消"
              okButtonProps={{ danger: true, loading: deleting }}
              onConfirm={() => handleDelete(record)}
            >
              <Button type="text" danger loading={deleting}>
                删除
              </Button>
            </Popconfirm>
          </div>
        );
      },
    },
  ];

  return (
    <section className="file-manager" aria-label="文件管理" aria-live="polite">
      <header className="file-toolbar">
        <div>
          <span className="file-section-label">ARCHIVE REGISTER</span>
          <strong>{files.length}</strong>
          <small>FILES IN CURRENT KNOWLEDGE BASE</small>
        </div>
        <div className="file-collection-control">
          <label htmlFor="file-collection">知识库</label>
          {collectionState === 'loading' ? <Skeleton.Input active size="small" /> : null}
          {collectionState === 'ready' ? (
            <Select
              id="file-collection"
              aria-label="文件管理知识库"
              value={resolvedCollection}
              options={collections.map((collection) => ({
                value: collection.name,
                label: `${collection.name} · ${collection.file_count} 个文件`,
              }))}
              onChange={handleCollectionChange}
            />
          ) : null}
          {collectionState === 'empty' ? (
            <span className="file-no-collection">暂无知识库</span>
          ) : null}
        </div>
      </header>

      {collectionState === 'error' ? (
        <Alert
          className="file-alert"
          type="error"
          showIcon
          message="知识库列表加载失败"
          description={collectionError}
          action={
            <Button danger onClick={onRetryCollections}>
              重新加载
            </Button>
          }
        />
      ) : null}

      {notice ? (
        <Alert
          className="file-alert"
          type="success"
          showIcon
          closable
          message={notice}
          onClose={() => setNotice('')}
        />
      ) : null}

      {actionError ? (
        <Alert
          className="file-alert"
          type="error"
          showIcon
          closable
          message="文件操作失败"
          description={actionError.message}
          action={
            <Button size="small" danger onClick={actionError.retry}>
              重试
            </Button>
          }
          onClose={() => setActionError(null)}
        />
      ) : null}

      <div className="file-content" data-state={fileState}>
        {collectionState === 'empty' ? (
          <Empty description="暂无知识库，请先在知识库管理中创建" />
        ) : null}

        {fileState === 'loading' ? (
          <div className="file-table-skeleton" aria-label="正在加载文件列表">
            <Skeleton active paragraph={{ rows: 6 }} />
          </div>
        ) : null}

        {fileState === 'error' ? (
          <Alert
            className="file-list-error"
            type="error"
            showIcon
            message="无法读取文件列表"
            description={fileError}
            action={
              <Button
                danger
                onClick={() => resolvedCollection && void loadFileList(resolvedCollection)}
              >
                重试
              </Button>
            }
          />
        ) : null}

        {fileState === 'empty' ? (
          <Empty
            className="file-empty"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <strong>知识库中暂无文件</strong>
                <span>上传文档并完成入库后，文件记录会显示在这里。</span>
              </div>
            }
          />
        ) : null}

        {fileState === 'success' ? (
          <Table<FileRecord>
            className="file-table"
            rowKey="file_id"
            columns={columns}
            dataSource={files}
            pagination={false}
            scroll={{ x: 940 }}
          />
        ) : null}
      </div>

      <Modal
        className="file-preview-modal"
        title={`已入库内容预览 · ${previewTarget?.file_name ?? ''}`}
        open={Boolean(previewTarget)}
        width={820}
        footer={null}
        onCancel={closePreview}
        destroyOnClose
      >
        {previewState === 'loading' ? (
          <div className="file-preview-loading">
            <Skeleton active paragraph={{ rows: 8 }} />
          </div>
        ) : null}

        {previewState === 'error' && previewTarget ? (
          <Alert
            type="error"
            showIcon
            message="文件预览加载失败"
            description={previewError}
            action={
              <Button danger onClick={() => void loadPreview(previewTarget)}>
                重试
              </Button>
            }
          />
        ) : null}

        {previewState === 'success' && previewResult ? (
          <div className="file-preview-result">
            <div className="file-preview-meta">
              <span>PERSISTED CHUNK CONTENT</span>
              <span>
                {previewResult.preview_chars.toLocaleString()} /{' '}
                {previewResult.total_chars.toLocaleString()} CHARACTERS
              </span>
            </div>
            {previewResult.preview_chars < previewResult.total_chars ? (
              <Alert
                className="file-preview-truncated"
                type="warning"
                showIcon
                message="预览内容已截断"
                description={`当前显示前 ${previewResult.preview_chars.toLocaleString()} 个字符，完整已入库文本共 ${previewResult.total_chars.toLocaleString()} 个字符。`}
              />
            ) : null}
            <pre>{previewResult.content}</pre>
          </div>
        ) : null}
      </Modal>
    </section>
  );
}
