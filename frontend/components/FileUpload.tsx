'use client';

import {
  Alert,
  Button,
  Empty,
  Progress,
  Select,
  Skeleton,
  Upload,
} from 'antd';
import type { UploadFile, UploadProps } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, uploadFile } from '@/lib/api-client';
import {
  type CollectionSourceProps,
  resolveCollectionSelection,
} from '@/lib/collection-state';
import type { UploadResponse, UploadWarning } from '@/lib/types';
import {
  SUPPORTED_EXTENSIONS,
  validateUploadFile,
} from '@/lib/upload-validation';

const { Dragger } = Upload;

type UploadState = 'idle' | 'uploading' | 'success' | 'warning' | 'error';

const ERROR_MESSAGES: Record<string, string> = {
  UNSUPPORTED_FILE_TYPE: '文件类型不受支持，请选择支持列表中的格式。',
  INVALID_FILE_NAME: '文件名不安全，请移除路径或危险字符后重试。',
  EMPTY_FILE: '不能上传空文件。',
  FILE_TOO_LARGE: '文件大小超过 50MB 限制。',
  FILE_ALREADY_EXISTS: '该知识库中已存在同名文件。',
  COLLECTION_NOT_FOUND: '所选知识库不存在，请刷新列表后重试。',
  FILE_PARSE_ERROR: '文件内容无法解析，请检查文件后重试。',
  NETWORK_ERROR: '无法连接后端服务，请检查服务状态后重试。',
};

const WARNING_MESSAGES: Record<UploadWarning['error_code'], string> = {
  OCR_PAGE_FAILED: 'OCR 识别失败',
  PAGE_RENDER_FAILED: '页面渲染失败',
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.code] ?? error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return '上传未完成，请稍后重试。';
}

interface FileUploadProps extends CollectionSourceProps {
  onFileUploaded: (collectionName: string) => void;
}

export default function FileUpload({
  collections,
  collectionState,
  collectionError,
  collectionMutation,
  onRetryCollections,
  onFileUploaded,
}: FileUploadProps) {
  const [selectedCollection, setSelectedCollection] = useState<string>();

  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState('');
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [retryFile, setRetryFile] = useState<File | null>(null);
  const handledMutationRevisionRef = useRef(0);

  const clearOutcome = useCallback(() => {
    setUploadState('idle');
    setUploadResult(null);
    setUploadError('');
    setFileList([]);
    setRetryFile(null);
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

    setSelectedCollection(resolvedCollection);
    clearOutcome();
  }, [
    clearOutcome,
    collectionMutation,
    collectionState,
    resolvedCollection,
    selectedCollection,
  ]);

  const runUpload = async (
    file: File,
    callbacks?: {
      onProgress?: (event: { percent: number }) => void;
      onSuccess?: (body: UploadResponse) => void;
      onError?: (error: Error) => void;
    },
  ) => {
    if (!resolvedCollection) {
      const message = '请先选择一个知识库。';
      setUploadState('error');
      setUploadError(message);
      callbacks?.onError?.(new Error(message));
      return;
    }

    setUploadState('uploading');
    setUploadResult(null);
    setUploadError('');
    setRetryFile(file);
    setFileList((current) =>
      current.map((item) => ({ ...item, status: 'uploading', percent: 12 })),
    );
    callbacks?.onProgress?.({ percent: 12 });

    try {
      const response = await uploadFile(file, resolvedCollection);
      onFileUploaded(resolvedCollection);
      callbacks?.onProgress?.({ percent: 100 });
      callbacks?.onSuccess?.(response);
      setFileList((current) =>
        current.map((item) => ({ ...item, status: 'done', percent: 100 })),
      );
      setUploadResult(response);
      setUploadState(response.status === 'SUCCESS' ? 'success' : 'warning');
      setRetryFile(null);
    } catch (error) {
      const message = getErrorMessage(error);
      const normalizedError = error instanceof Error ? error : new Error(message);
      callbacks?.onError?.(normalizedError);
      setFileList((current) =>
        current.map((item) => ({ ...item, status: 'error' })),
      );
      setUploadError(message);
      setUploadState('error');
    }
  };

  const beforeUpload: UploadProps['beforeUpload'] = (file) => {
    const validationError = validateUploadFile(file);
    if (validationError) {
      setUploadState('error');
      setUploadError(validationError);
      setUploadResult(null);
      setRetryFile(null);
      setFileList([]);
      return Upload.LIST_IGNORE;
    }

    if (!resolvedCollection) {
      setUploadState('error');
      setUploadError('请先选择一个知识库。');
      return Upload.LIST_IGNORE;
    }

    return true;
  };

  const customRequest: UploadProps['customRequest'] = ({
    file,
    onError,
    onProgress,
    onSuccess,
  }) => {
    void runUpload(file as File, {
      onProgress,
      onSuccess: (response) => onSuccess?.(response),
      onError,
    });
  };

  const handleCollectionChange = (value: string) => {
    setSelectedCollection(value);
    clearOutcome();
  };

  return (
    <section className="upload-manager" aria-label="文件上传" aria-live="polite">
      <div className="upload-console">
        <aside className="upload-manifest">
          <p className="upload-section-label">INGESTION MANIFEST</p>
          <h2>选择目标空间</h2>
          <p className="upload-manifest-copy">
            文件将进入所选知识库的解析、切分、向量化与索引流水线。
          </p>

          {collectionState === 'loading' ? (
            <Skeleton active paragraph={{ rows: 2 }} />
          ) : null}

          {collectionState === 'error' ? (
            <Alert
              type="error"
              showIcon
              message="知识库列表加载失败"
              description={collectionError}
              action={
                <Button size="small" danger onClick={onRetryCollections}>
                  重试
                </Button>
              }
            />
          ) : null}

          {collectionState === 'empty' ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无知识库，请先在知识库管理中创建"
            />
          ) : null}

          {collectionState === 'ready' ? (
            <div className="upload-field">
              <label htmlFor="upload-collection">目标知识库</label>
              <Select
                id="upload-collection"
                aria-label="目标知识库"
                value={resolvedCollection}
                options={collections.map((collection) => ({
                  value: collection.name,
                  label: `${collection.name} · ${collection.file_count} 个文件`,
                }))}
                onChange={handleCollectionChange}
              />
            </div>
          ) : null}

          <dl className="upload-rules">
            <div>
              <dt>单文件上限</dt>
              <dd>50 MB</dd>
            </div>
            <div>
              <dt>上传模式</dt>
              <dd>单文件</dd>
            </div>
            <div>
              <dt>支持格式</dt>
              <dd>11 种</dd>
            </div>
          </dl>
        </aside>

        <div className="upload-stage" data-state={uploadState}>
          <Dragger
            className="upload-dragger"
            accept={SUPPORTED_EXTENSIONS.join(',')}
            beforeUpload={beforeUpload}
            customRequest={customRequest}
            disabled={collectionState !== 'ready' || uploadState === 'uploading'}
            fileList={fileList}
            maxCount={1}
            multiple={false}
            progress={{ strokeColor: '#54742f', showInfo: true }}
            onChange={({ fileList: nextFileList }) => {
              setFileList(nextFileList.slice(-1));
            }}
            onRemove={() => {
              clearOutcome();
              return true;
            }}
          >
            <div className="upload-drop-symbol" aria-hidden="true">
              <span>↑</span>
            </div>
            <p className="upload-drop-title">拖拽文件到这里，或点击选择</p>
            <p className="upload-drop-hint">
              TXT · MD · CSV · JSON · LOG · PDF · DOCX · XLSX / XLSM / XLTX / XLTM
            </p>
          </Dragger>

          {uploadState === 'uploading' ? (
            <div className="upload-progress" role="status">
              <div>
                <span>PIPELINE ACTIVE</span>
                <strong>{fileList[0]?.name ?? retryFile?.name}</strong>
              </div>
              <Progress
                percent={fileList[0]?.percent ?? 12}
                showInfo={false}
                status="active"
              />
              <p>正在上传并执行解析、切分与索引，请保持页面开启。</p>
            </div>
          ) : null}

          {uploadState === 'success' && uploadResult ? (
            <Alert
              className="upload-outcome"
              type="success"
              showIcon
              message="文件已完成入库"
              description={
                <span>
                  {uploadResult.file_name} 已写入 {uploadResult.collection_name}，生成{' '}
                  <strong>{uploadResult.chunks}</strong> 个切片。
                </span>
              }
              action={<Button onClick={clearOutcome}>继续上传</Button>}
            />
          ) : null}

          {uploadState === 'warning' && uploadResult ? (
            <Alert
              className="upload-outcome"
              type="warning"
              showIcon
              message="文件已入库，但部分页面处理失败"
              description={
                <div>
                  <p>
                    {uploadResult.file_name} 已生成 {uploadResult.chunks} 个切片。
                  </p>
                  <ul>
                    {uploadResult.warnings.map((warning) => (
                      <li key={`${warning.page_number}-${warning.error_code}`}>
                        第 {warning.page_number} 页：
                        {WARNING_MESSAGES[warning.error_code]}
                      </li>
                    ))}
                  </ul>
                </div>
              }
              action={<Button onClick={clearOutcome}>继续上传</Button>}
            />
          ) : null}

          {uploadState === 'error' ? (
            <Alert
              className="upload-outcome"
              type="error"
              showIcon
              message="上传未完成"
              description={uploadError}
              action={
                retryFile ? (
                  <Button danger onClick={() => void runUpload(retryFile)}>
                    重试
                  </Button>
                ) : (
                  <Button danger onClick={clearOutcome}>
                    重新选择
                  </Button>
                )
              }
            />
          ) : null}
        </div>
      </div>
    </section>
  );
}
