'use client';

import {
  Alert,
  Button,
  Collapse,
  Empty,
  Input,
  Select,
  Skeleton,
  Spin,
} from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ApiError, queryQA } from '@/lib/api-client';
import {
  type CollectionSourceProps,
  resolveCollectionSelection,
} from '@/lib/collection-state';
import type { ChatMessage, Source } from '@/lib/types';

const { TextArea } = Input;
const MAX_HISTORY_MESSAGES = 20;

type QueryState = 'idle' | 'loading' | 'success' | 'error' | 'empty_kb';

interface DisplayMessage extends ChatMessage {
  id: string;
  sources?: Source[];
}

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_QUERY: '请输入有效的问题后重试。',
  INVALID_HISTORY_FORMAT: '对话历史格式无效，请切换知识库后重新开始。',
  COLLECTION_NOT_FOUND: '所选知识库不存在，请刷新列表后重试。',
  LLM_NOT_CONFIGURED: '问答模型尚未配置，请联系管理员。',
  LLM_AUTH_FAILED: '问答模型认证失败，请检查服务配置。',
  LLM_UNAVAILABLE: '问答模型暂时不可用，请稍后重试。',
  LLM_RESPONSE_ERROR: '问答模型返回了无法解析的响应，请重试。',
  EMBEDDING_MODEL_ERROR: '向量模型暂时不可用，请稍后重试。',
  NETWORK_ERROR: '无法连接后端服务，请检查服务状态后重试。',
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.code] ?? error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return '问题未能完成，请稍后重试。';
}

function toRequestHistory(history: DisplayMessage[]): ChatMessage[] {
  return history.slice(-MAX_HISTORY_MESSAGES).map(({ role, content }) => ({
    role,
    content,
  }));
}

export default function QAPanel({
  collections,
  collectionState,
  collectionError,
  collectionMutation,
  onRetryCollections,
}: CollectionSourceProps) {
  const [selectedCollection, setSelectedCollection] = useState<string>();

  const [history, setHistory] = useState<DisplayMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [pendingQuestion, setPendingQuestion] = useState('');
  const [queryState, setQueryState] = useState<QueryState>('idle');
  const [queryError, setQueryError] = useState('');
  const conversationEndRef = useRef<HTMLDivElement>(null);
  const requestVersionRef = useRef(0);
  const handledMutationRevisionRef = useRef(0);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, pendingQuestion, queryState]);

  const resetConversation = useCallback(() => {
    setHistory([]);
    setQuestion('');
    setPendingQuestion('');
    setQueryState('idle');
    setQueryError('');
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

    requestVersionRef.current += 1;
    setSelectedCollection(resolvedCollection);
    resetConversation();
  }, [
    collectionState,
    collectionMutation,
    resetConversation,
    resolvedCollection,
    selectedCollection,
  ]);

  const handleCollectionChange = (value: string) => {
    requestVersionRef.current += 1;
    setSelectedCollection(value);
    resetConversation();
  };

  const sendQuestion = async (questionToSend = question) => {
    const normalizedQuestion = questionToSend.trim();
    if (!normalizedQuestion || !resolvedCollection || queryState === 'loading') {
      return;
    }

    const requestHistory = toRequestHistory(history);
    const requestVersion = requestVersionRef.current + 1;
    requestVersionRef.current = requestVersion;
    setPendingQuestion(normalizedQuestion);
    setQuestion('');
    setQueryError('');
    setQueryState('loading');

    try {
      const response = await queryQA(
        normalizedQuestion,
        resolvedCollection,
        undefined,
        requestHistory,
      );
      if (requestVersion !== requestVersionRef.current) {
        return;
      }
      const stamp = Date.now();
      const completedPair: DisplayMessage[] = [
        {
          id: `${stamp}-user`,
          role: 'user',
          content: normalizedQuestion,
        },
        {
          id: `${stamp}-assistant`,
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
        },
      ];
      setHistory((current) =>
        [...current, ...completedPair].slice(-MAX_HISTORY_MESSAGES),
      );
      setPendingQuestion('');
      setQueryState('success');
    } catch (error) {
      if (requestVersion !== requestVersionRef.current) {
        return;
      }
      if (error instanceof ApiError && error.code === 'COLLECTION_EMPTY') {
        setQueryError('知识库暂无文档，请先上传文件。');
        setQueryState('empty_kb');
      } else {
        setQueryError(getErrorMessage(error));
        setQueryState('error');
      }
    }
  };

  const renderSources = (message: DisplayMessage) => {
    if (!message.sources || message.sources.length === 0) {
      return null;
    }

    return (
      <Collapse
        className="qa-sources"
        ghost
        items={[
          {
            key: 'sources',
            label: `查看来源 · ${message.sources.length}`,
            children: (
              <ol className="qa-source-list">
                {message.sources.map((source) => (
                  <li key={source.chunk_id}>
                    <span>{source.file_name}</span>
                    <code>{source.relevance_score.toFixed(3)}</code>
                  </li>
                ))}
              </ol>
            ),
          },
        ]}
      />
    );
  };

  const canSend =
    collectionState === 'ready' &&
    Boolean(resolvedCollection) &&
    Boolean(question.trim()) &&
    queryState !== 'loading';

  return (
    <section className="qa-panel" aria-label="知识问答">
      <header className="qa-toolbar">
        <div className="qa-collection-control">
          <span className="qa-section-label">ACTIVE KNOWLEDGE BASE</span>
          {collectionState === 'loading' ? (
            <Skeleton.Input active size="small" />
          ) : null}
          {collectionState === 'ready' ? (
            <Select
              aria-label="问答知识库"
              value={resolvedCollection}
              options={collections.map((collection) => ({
                value: collection.name,
                label: collection.name,
              }))}
              onChange={handleCollectionChange}
            />
          ) : null}
          {collectionState === 'empty' ? (
            <span className="qa-no-collection">暂无知识库</span>
          ) : null}
        </div>
        <div className="qa-history-meter" aria-label={`对话历史 ${history.length} 条`}>
          <span>{String(history.length).padStart(2, '0')}</span>
          <small>/ {MAX_HISTORY_MESSAGES} MESSAGES</small>
        </div>
      </header>

      {collectionState === 'error' ? (
        <Alert
          className="qa-collection-error"
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

      <div className="qa-conversation" data-state={queryState} aria-live="polite">
        {history.length === 0 && !pendingQuestion && collectionState !== 'error' ? (
          <div className="qa-idle">
            <span className="qa-idle-mark" aria-hidden="true">?</span>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                collectionState === 'empty' ? (
                  <div>
                    <strong>先创建一个知识库</strong>
                    <span>创建并上传文档后，即可开始基于证据的问答。</span>
                  </div>
                ) : (
                  <div>
                    <strong>从一个可核验的问题开始</strong>
                    <span>回答会基于所选知识库，并附上相关来源。</span>
                  </div>
                )
              }
            />
          </div>
        ) : null}

        {history.map((message) => (
          <article
            className={`qa-message qa-message-${message.role}`}
            key={message.id}
          >
            <div className="qa-message-meta">
              <span>{message.role === 'user' ? 'YOU' : 'DX—RAG'}</span>
              <span>{message.role === 'user' ? 'QUESTION' : 'GROUNDED ANSWER'}</span>
            </div>
            <div className="qa-message-body">
              {message.role === 'assistant' ? (
                <div className="qa-markdown">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <p>{message.content}</p>
              )}
              {message.role === 'assistant' ? renderSources(message) : null}
            </div>
          </article>
        ))}

        {pendingQuestion ? (
          <article className="qa-message qa-message-user qa-message-pending">
            <div className="qa-message-meta">
              <span>YOU</span>
              <span>QUESTION</span>
            </div>
            <div className="qa-message-body">
              <p>{pendingQuestion}</p>
            </div>
          </article>
        ) : null}

        {queryState === 'loading' ? (
          <article className="qa-message qa-message-assistant qa-loading-answer">
            <div className="qa-message-meta">
              <span>DX—RAG</span>
              <span>RETRIEVING</span>
            </div>
            <div className="qa-message-body">
              <Spin size="small" />
              <span>正在检索证据并组织回答…</span>
            </div>
          </article>
        ) : null}

        {queryState === 'error' || queryState === 'empty_kb' ? (
          <Alert
            className="qa-query-error"
            type={queryState === 'empty_kb' ? 'warning' : 'error'}
            showIcon
            message={queryState === 'empty_kb' ? '知识库暂时无法回答' : '问答请求失败'}
            description={queryError}
            action={
              <Button
                danger={queryState === 'error'}
                onClick={() => void sendQuestion(pendingQuestion)}
              >
                重试
              </Button>
            }
          />
        ) : null}
        <div ref={conversationEndRef} />
      </div>

      <footer className="qa-composer">
        <TextArea
          aria-label="输入问题"
          value={question}
          placeholder="输入关于当前知识库的问题…"
          autoSize={{ minRows: 2, maxRows: 5 }}
          disabled={collectionState !== 'ready' || queryState === 'loading'}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.ctrlKey && event.key === 'Enter') {
              event.preventDefault();
              void sendQuestion();
            }
          }}
        />
        <div className="qa-composer-actions">
          <span>CTRL + ENTER TO SEND</span>
          <Button
            type="primary"
            size="large"
            disabled={!canSend}
            loading={queryState === 'loading'}
            onClick={() => void sendQuestion()}
          >
            发送问题
          </Button>
        </div>
      </footer>
    </section>
  );
}
