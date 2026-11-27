'use client';

import { Alert, Button, Collapse, Input, Select, Skeleton, Spin } from 'antd';
import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import WorkspaceIcon from '@/components/WorkspaceIcon';
import { ApiError, streamQueryQA } from '@/lib/api-client';
import {
  type CollectionSourceProps,
  resolveCollectionSelection,
} from '@/lib/collection-state';
import type { ChatMessage, QueryStreamEvent, Source } from '@/lib/types';

const { TextArea } = Input;
const MAX_HISTORY_MESSAGES = 20;
const QUERY_TIMEOUT_MS = 4 * 60 * 1000;
const SCROLL_THRESHOLD = 32;

type TurnStatus = 'loading' | 'done' | 'stopped' | 'error' | 'incomplete';

interface Turn {
  id: number;
  question: string;
  answer: string;
  status: TurnStatus;
  stage: string;
  notice: string;
  sources: Source[];
  errorCode?: string;
}

interface ActiveRequest {
  id: number;
  turnId: number;
  collection: string;
  startedAt: number;
  controller: AbortController;
}

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_QUERY: '请输入有效的问题后重试。',
  INVALID_HISTORY_FORMAT: '对话历史格式无效，请切换知识库后重新开始。',
  COLLECTION_NOT_FOUND: '所选知识库不存在，请刷新列表后重试。',
  COLLECTION_EMPTY: '知识库暂无文档，请先上传文件。',
  LLM_NOT_CONFIGURED: '问答模型尚未配置，请联系管理员。',
  LLM_AUTH_FAILED: '问答模型认证失败，请检查服务配置。',
  LLM_UNAVAILABLE: '问答模型暂时不可用，请稍后重试。',
  LLM_RESPONSE_ERROR: '问答模型返回了无法解析的响应，请重试。',
  EMBEDDING_MODEL_ERROR: '向量模型暂时不可用，请稍后重试。',
  NETWORK_ERROR: '无法连接后端服务，请检查服务状态后重试。',
  STREAM_INTERRUPTED: '回答连接已中断，请重新生成。',
  STREAM_PROTOCOL_ERROR: '回答数据异常，请重新生成。',
  QUERY_TIMEOUT: '问答超时，请重新生成。',
};

function errorMessage(code: string, fallback: string): string {
  return ERROR_MESSAGES[code] ?? (fallback || '问题未能完成，请稍后重试。');
}

function stageMessage(stage: string): string {
  switch (stage) {
    case 'retrieving': return '正在检索资料';
    case 'generating': return '正在生成回答';
    case 'retrying': return '正在重试';
    default: return '正在处理';
  }
}

function incompleteMessage(reason: string): string {
  switch (reason) {
    case 'length': return '回答已截断，未完成。';
    case 'empty': return '回答为空，未完成。';
    default: return '回答未完成。';
  }
}

function requestHistory(turns: Turn[]): ChatMessage[] {
  return turns.flatMap((turn): ChatMessage[] => turn.status === 'done'
    ? [{ role: 'user', content: turn.question }, { role: 'assistant', content: turn.answer }]
    : []).slice(-MAX_HISTORY_MESSAGES);
}

export default function QAPanel({
  collections,
  collectionState,
  collectionError,
  collectionMutation,
  onRetryCollections,
  isActive = true,
}: CollectionSourceProps & { isActive?: boolean }) {
  const [selectedCollection, setSelectedCollection] = useState<string>();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState('');
  const turnsRef = useRef<Turn[]>([]);
  const activeRef = useRef<ActiveRequest | null>(null);
  const nextIdRef = useRef(0);
  const conversationRef = useRef<HTMLDivElement>(null);
  const followRef = useRef(true);
  const handledMutationRevisionRef = useRef(0);

  const resolvedCollection = resolveCollectionSelection(
    selectedCollection, collections, collectionMutation, handledMutationRevisionRef.current,
  );
  // The resolved identity can change before the reset effect runs.
  const collectionRef = useRef(resolvedCollection);
  collectionRef.current = resolvedCollection;

  const changeTurns = useCallback((change: (current: Turn[]) => Turn[]) => {
    const next = change(turnsRef.current);
    turnsRef.current = next;
    setTurns(next);
  }, []);

  const resetConversation = useCallback(() => {
    const active = activeRef.current;
    activeRef.current = null;
    active?.controller.abort();
    changeTurns(() => []);
    setQuestion('');
    followRef.current = true;
  }, [changeTurns]);

  useEffect(() => {
    if (collectionState === 'loading' || collectionState === 'error') return;
    if (collectionMutation) handledMutationRevisionRef.current = collectionMutation.revision;
    if (resolvedCollection === selectedCollection) return;
    resetConversation();
    setSelectedCollection(resolvedCollection);
  }, [collectionState, collectionMutation, resetConversation, resolvedCollection, selectedCollection]);

  useEffect(() => () => {
    const active = activeRef.current;
    activeRef.current = null;
    active?.controller.abort();
  }, []);

  useEffect(() => {
    const conversation = conversationRef.current;
    if (isActive && conversation && conversation.clientHeight > 0 && followRef.current) {
      conversation.scrollTop = conversation.scrollHeight;
    }
  }, [turns, isActive]);

  const handleCollectionChange = (value: string) => {
    if (value === resolvedCollection) return;
    resetConversation();
    setSelectedCollection(value);
  };

  const updateTurn = (turnId: number, change: (turn: Turn) => Turn) => {
    changeTurns((current) => current.map((turn) => turn.id === turnId ? change(turn) : turn));
  };

  const isCurrent = (request: ActiveRequest) =>
    activeRef.current?.id === request.id && collectionRef.current === request.collection;

  const finish = (request: ActiveRequest, change: (turn: Turn) => Turn) => {
    if (!isCurrent(request)) return;
    activeRef.current = null;
    updateTurn(request.turnId, change);
  };

  const startRequest = (turn: Turn, collection: string, startedAt: number) => {
    const request: ActiveRequest = {
      id: ++nextIdRef.current,
      turnId: turn.id,
      collection,
      startedAt,
      controller: new AbortController(),
    };
    activeRef.current = request;
    const history = requestHistory(turnsRef.current);
    const onEvent = (event: QueryStreamEvent) => {
      if (!isCurrent(request)) return;
      switch (event.type) {
        case 'status':
          updateTurn(turn.id, (current) => ({ ...current, stage: event.stage }));
          break;
        case 'delta':
          updateTurn(turn.id, (current) => ({ ...current, answer: current.answer + event.text }));
          break;
        case 'done':
          finish(request, (current) => ({ ...current, status: 'done', sources: event.sources }));
          break;
        case 'incomplete':
          finish(request, (current) => ({ ...current, status: 'incomplete', notice: incompleteMessage(event.reason) }));
          break;
        case 'error':
          finish(request, (current) => ({ ...current, status: 'error', errorCode: event.code,
            notice: errorMessage(event.code, event.message) }));
          break;
      }
    };
    void streamQueryQA(turn.question, collection, {
      history, signal: request.controller.signal, startedAt, onEvent,
    }).then(() => {
      // A transport that ends without a terminal event cannot complete a turn.
      finish(request, (current) => ({ ...current, status: 'error', errorCode: 'STREAM_INTERRUPTED',
        notice: ERROR_MESSAGES.STREAM_INTERRUPTED }));
    }).catch((error: unknown) => {
      const code = error instanceof ApiError ? error.code : 'NETWORK_ERROR';
      const fallback = error instanceof Error ? error.message : '';
      finish(request, (current) => ({ ...current, status: 'error', errorCode: code,
        notice: errorMessage(code, fallback) }));
    });
  };

  const sendQuestion = () => {
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion || !resolvedCollection || collectionState !== 'ready' || activeRef.current) return;
    const startedAt = Date.now();
    const turn: Turn = { id: ++nextIdRef.current, question: normalizedQuestion, answer: '',
      status: 'loading', stage: 'retrieving', notice: '', sources: [] };
    changeTurns((current) => [...current, turn]);
    setQuestion('');
    startRequest(turn, resolvedCollection, startedAt);
  };

  const retryTurn = (turn: Turn) => {
    const latest = turnsRef.current[turnsRef.current.length - 1];
    if (!resolvedCollection || collectionState !== 'ready' || activeRef.current ||
        latest?.id !== turn.id || latest.status === 'done' || latest.status === 'loading') return;
    const startedAt = Date.now();
    const retry: Turn = { ...latest, answer: '', status: 'loading', stage: 'retrieving',
      notice: '', sources: [], errorCode: undefined };
    updateTurn(turn.id, () => retry);
    startRequest(retry, resolvedCollection, startedAt);
  };

  const stop = () => {
    const request = activeRef.current;
    if (!request || !isCurrent(request)) return;
    const timedOut = Date.now() >= request.startedAt + QUERY_TIMEOUT_MS;
    finish(request, (turn) => ({ ...turn, status: timedOut ? 'error' : 'stopped',
      errorCode: timedOut ? 'QUERY_TIMEOUT' : undefined,
      notice: timedOut ? ERROR_MESSAGES.QUERY_TIMEOUT : '已停止，回答未完成。' }));
    request.controller.abort();
  };

  const renderSources = (sources: Source[]) => sources.length ? (
    <Collapse className="qa-sources" ghost items={[{
      key: 'sources', label: `参考来源 · ${sources.length}`,
      children: <ol className="qa-source-list">{sources.map((source) => (
        <li key={source.chunk_id}>
          <span className="qa-source-file"><WorkspaceIcon name="files" /><span>{source.file_name}</span></span>
          <span className="qa-source-score">相关性 <code>{source.relevance_score.toFixed(3)}</code></span>
        </li>
      ))}</ol>,
    }]} />
  ) : null;

  const latest = turns[turns.length - 1];
  const loading = latest?.status === 'loading';
  const queryState = !latest ? 'idle' : loading ? 'loading' : latest.status === 'done' ? 'success'
    : latest.errorCode === 'COLLECTION_EMPTY' ? 'empty_kb' : 'error';
  const canSend = collectionState === 'ready' && Boolean(resolvedCollection) &&
    Boolean(question.trim()) && !loading;

  return (
    <section className="qa-panel" aria-label="知识问答">
      <header className="qa-toolbar">
        <div className="qa-collection-control">
          <span className="qa-section-label">当前知识库</span>
          {collectionState === 'loading' ? <Skeleton.Input active size="small" /> : null}
          {collectionState === 'ready' ? (
            <Select aria-label="问答知识库" value={resolvedCollection}
              options={collections.map((collection) => ({ value: collection.name, label: collection.name }))}
              onChange={handleCollectionChange} />
          ) : null}
          {collectionState === 'empty' ? <span className="qa-no-collection">暂无知识库</span> : null}
        </div>
        <div className="qa-history-meter" aria-label={`当前会话 ${turns.length} 轮对话`}>
          <span>{turns.length} 轮</span><small>上下文最多 {MAX_HISTORY_MESSAGES} 条消息</small>
        </div>
      </header>

      {collectionState === 'error' ? (
        <Alert className="qa-collection-error" type="error" showIcon message="知识库列表加载失败"
          description={collectionError} action={<Button danger onClick={onRetryCollections}>重新加载</Button>} />
      ) : null}

      <div className="qa-conversation" ref={conversationRef} data-state={queryState}
        onScroll={(event) => {
          const element = event.currentTarget;
          if (element.clientHeight > 0) {
            followRef.current = element.scrollHeight - element.scrollTop - element.clientHeight <= SCROLL_THRESHOLD;
          }
        }}>
        {turns.length === 0 && collectionState !== 'error' ? (
          <div className="qa-idle">
            <div className="qa-idle-symbol"><WorkspaceIcon name="qa" /></div>
            <h2>{collectionState === 'empty' ? '先创建一个知识库' : '你的资料，有问有答'}</h2>
            <p>{collectionState === 'empty' ? '创建知识库并上传文档后，就可以在这里提问。'
              : '选择知识库，描述你的问题。让分散的资料，成为清晰的答案。'}</p>
            <div className="qa-idle-notes"><span>支持多轮追问</span><span aria-hidden="true">·</span><span>来源可展开查看</span></div>
          </div>
        ) : null}

        {turns.map((turn, index) => (
          <Fragment key={turn.id}>
            <article className="qa-message qa-message-user">
              <div className="qa-message-meta"><span>你</span><span>问题</span></div>
              <div className="qa-message-body"><p>{turn.question}</p></div>
            </article>
            {turn.answer ? (
              <article className="qa-message qa-message-assistant">
                <div className="qa-message-meta"><span>DX-RAG · 知识助手</span><span>基于当前知识库</span></div>
                <div className="qa-message-body">
                  <div className="qa-markdown"><ReactMarkdown>{turn.answer}</ReactMarkdown></div>
                  {turn.status === 'done' ? renderSources(turn.sources) : null}
                </div>
              </article>
            ) : null}
            {turn.status === 'loading' ? (
              <div className="qa-turn-status" role="status" aria-live="polite"><Spin size="small" /> {stageMessage(turn.stage)}…</div>
            ) : turn.status !== 'done' ? (
              <div className="qa-turn-notice" role="status" aria-live="polite">
                <span>{turn.notice}</span>
                {index === turns.length - 1 ? (
                  <span className="qa-turn-actions"><Button onClick={() => retryTurn(turn)}>重新生成</Button></span>
                ) : null}
              </div>
            ) : index === turns.length - 1 ? (
              <div className="qa-turn-status" role="status" aria-live="polite">回答完成</div>
            ) : null}
          </Fragment>
        ))}
      </div>

      <footer className="qa-composer">
        <TextArea aria-label="输入问题" value={question} placeholder="输入关于当前知识库的问题…"
          autoSize={{ minRows: 2, maxRows: 5 }} disabled={collectionState !== 'ready'}
          onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => {
            if (event.ctrlKey && event.key === 'Enter') { event.preventDefault(); sendQuestion(); }
          }} />
        <div className="qa-composer-actions">
          <span><kbd>Ctrl</kbd> + <kbd>Enter</kbd> 发送 · 支持多轮追问</span>
          {loading ? <Button className="qa-stop-button" size="large" onClick={stop}>停止生成</Button> : null}
          <Button type="primary" size="large" disabled={!canSend} onClick={sendQuestion}>发送问题</Button>
        </div>
      </footer>
    </section>
  );
}
