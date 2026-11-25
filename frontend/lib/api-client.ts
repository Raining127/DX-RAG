import type {
  ChatMessage,
  CollectionCreateRequest,
  CollectionListResponse,
  CollectionRenameRequest,
  CollectionRenameResponse,
  CollectionResponse,
  ErrorDetails,
  ErrorResponse,
  FileDeleteResponse,
  FileListResponse,
  HealthResponse,
  PreviewResponse,
  QueryRequest,
  QueryResponse,
  QueryStreamEvent,
  Source,
  UploadResponse,
} from "./types";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

/** Backend base URL, configurable at build time for the Next.js browser app. */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ErrorDetails;
  readonly response: ErrorResponse;

  constructor(
    message: string,
    options: {
      status: number;
      code: string;
      details?: ErrorDetails;
    },
  ) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details || {};
    this.response = {
      error: {
        code: this.code,
        message: this.message,
        details: this.details,
      },
    };
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isErrorResponse(value: unknown): value is ErrorResponse {
  if (!isRecord(value) || !isRecord(value.error)) {
    return false;
  }

  return (
    typeof value.error.code === "string" &&
    typeof value.error.message === "string"
  );
}

function getErrorDetails(value: unknown): ErrorDetails {
  return isRecord(value) ? value : {};
}

async function parseErrorResponse(response: Response): Promise<never> {
  let payload: unknown;

  try {
    payload = await response.json();
  } catch {
    payload = undefined;
  }

  if (isErrorResponse(payload)) {
    const details = getErrorDetails(payload.error.details);
    const error = new ApiError(payload.error.message, {
      status: response.status,
      code: payload.error.code,
      details,
    });
    console.error("DX-RAG API request failed", {
      code: error.code,
      status: error.status,
    });
    throw error;
  }

  const error = new ApiError(`Request failed with status ${response.status}`, {
    status: response.status,
    code: "INVALID_RESPONSE",
  });
  console.error("DX-RAG API request failed", {
    code: error.code,
    status: error.status,
  });
  throw error;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (cause) {
    const error = new ApiError("Unable to connect to the backend service", {
      status: 0,
      code: "NETWORK_ERROR",
      details: cause instanceof Error ? { cause: cause.message } : {},
    });
    console.error("DX-RAG API request failed", {
      code: error.code,
      status: error.status,
    });
    throw error;
  }

  if (!response.ok) {
    return parseErrorResponse(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch (cause) {
    const error = new ApiError("Backend returned an invalid JSON response", {
      status: response.status,
      code: "INVALID_RESPONSE",
      details: cause instanceof Error ? { cause: cause.message } : {},
    });
    console.error("DX-RAG API request failed", {
      code: error.code,
      status: error.status,
    });
    throw error;
  }
}

function jsonRequest(body: unknown, method: "POST" | "PUT"): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

function collectionPath(name: string): string {
  return `/collections/${encodeURIComponent(name)}`;
}

export function createCollection(name: string): Promise<CollectionResponse> {
  const body: CollectionCreateRequest = { name };
  return request<CollectionResponse>("/collections", jsonRequest(body, "POST"));
}

export function listCollections(): Promise<CollectionListResponse> {
  return request<CollectionListResponse>("/collections");
}

export function renameCollection(
  oldName: string,
  newName: string,
): Promise<CollectionRenameResponse> {
  const body: CollectionRenameRequest = { new_name: newName };
  return request<CollectionRenameResponse>(
    collectionPath(oldName),
    jsonRequest(body, "PUT"),
  );
}

export function deleteCollection(name: string): Promise<CollectionResponse> {
  return request<CollectionResponse>(collectionPath(name), { method: "DELETE" });
}

export function uploadFile(
  file: File,
  collectionName?: string,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (collectionName !== undefined) {
    formData.append("collection_name", collectionName);
  }

  return request<UploadResponse>("/upload", {
    method: "POST",
    body: formData,
  });
}

export function queryQA(
  question: string,
  collectionName: string,
  topK?: number,
  history?: ChatMessage[],
): Promise<QueryResponse> {
  const body: QueryRequest = {
    question,
    collection_name: collectionName,
  };

  if (topK !== undefined) {
    body.top_k = topK;
  }
  if (history !== undefined) {
    body.history = history;
  }

  return request<QueryResponse>("/query", jsonRequest(body, "POST"));
}

const STREAM_TIMEOUT_MS = 4 * 60 * 1000;

export interface StreamQueryOptions {
  topK?: number;
  history?: ChatMessage[];
  signal?: AbortSignal;
  /** Date.now() at submission; omit when this call is made at submission. */
  startedAt?: number;
  onEvent: (event: QueryStreamEvent) => void;
}

type SSEFrame = { event: string; data: string };

/** Incrementally interpret SSE lines; network chunks are not frame boundaries. */
class SSEParser {
  private buffer = "";
  private event = "";
  private data: string[] = [];

  feed(text: string, final = false): SSEFrame[] {
    this.buffer += text;
    const frames: SSEFrame[] = [];
    let offset = 0;
    for (let i = 0; i < this.buffer.length; i += 1) {
      const character = this.buffer[i];
      if (character !== "\r" && character !== "\n") continue;
      // Wait for the next chunk to decide whether a trailing CR is a CRLF.
      if (character === "\r" && i + 1 === this.buffer.length && !final) break;
      const line = this.buffer.slice(offset, i);
      if (character === "\r" && this.buffer[i + 1] === "\n") i += 1;
      offset = i + 1;
      if (line === "") {
        if (this.data.length) {
          frames.push({ event: this.event || "message", data: this.data.join("\n") });
        }
        this.event = "";
        this.data = [];
      } else if (!line.startsWith(":")) {
        const separator = line.indexOf(":");
        const field = separator < 0 ? line : line.slice(0, separator);
        let value = separator < 0 ? "" : line.slice(separator + 1);
        if (value.startsWith(" ")) value = value.slice(1);
        if (field === "event") this.event = value;
        if (field === "data") this.data.push(value);
      }
    }
    this.buffer = this.buffer.slice(offset);
    // An unfinished line or frame at EOF is deliberately not dispatched.
    return frames;
  }
}

function streamError(code: string, message: string): ApiError {
  return new ApiError(message, { status: 0, code });
}

function protocolError(): ApiError {
  return streamError("STREAM_PROTOCOL_ERROR", "回答数据异常，请重新生成");
}

function parseStreamEvent(frame: SSEFrame, answer: string): QueryStreamEvent | undefined {
  if (!["status", "delta", "done", "incomplete", "error"].includes(frame.event)) {
    return undefined;
  }
  let data: unknown;
  try {
    data = JSON.parse(frame.data);
  } catch {
    throw protocolError();
  }
  if (!isRecord(data) || Array.isArray(data)) throw protocolError();
  switch (frame.event) {
    case "status":
      if (typeof data.stage !== "string") throw protocolError();
      return { type: "status", stage: data.stage };
    case "delta":
      if (typeof data.text !== "string") throw protocolError();
      return { type: "delta", text: data.text };
    case "incomplete":
      if (typeof data.reason !== "string") throw protocolError();
      return { type: "incomplete", reason: data.reason };
    case "error":
      if (typeof data.code !== "string" || typeof data.message !== "string") throw protocolError();
      return { type: "error", code: data.code, message: data.message };
    case "done": {
      if (!answer.trim() || !Array.isArray(data.sources)) throw protocolError();
      const sources: Source[] = data.sources.map((source: unknown) => {
        if (!isRecord(source) || Array.isArray(source) ||
            typeof source.file_id !== "string" || typeof source.file_name !== "string" ||
            typeof source.chunk_id !== "string" || typeof source.relevance_score !== "number" ||
            !Number.isFinite(source.relevance_score)) throw protocolError();
        return { file_id: source.file_id, file_name: source.file_name,
          chunk_id: source.chunk_id, relevance_score: source.relevance_score };
      });
      return { type: "done", sources };
    }
  }
}

/** Read one SSE query. Terminal server events are delivered through onEvent. */
export async function streamQueryQA(
  question: string,
  collectionName: string,
  options: StreamQueryOptions,
): Promise<void> {
  const deadline = (options.startedAt ?? Date.now()) + STREAM_TIMEOUT_MS;
  const controller = new AbortController();
  let stopped: ApiError | undefined;
  let terminalAccepted = false;
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let rejectStop!: (error: ApiError) => void;
  const stoppedPromise = new Promise<never>((_, reject) => { rejectStop = reject; });

  const timeoutError = () => streamError("QUERY_TIMEOUT", "问答超时，请重新生成");
  const stop = (error: ApiError) => {
    if (terminalAccepted || stopped) return;
    stopped = Date.now() >= deadline ? timeoutError() : error;
    controller.abort();
    rejectStop(stopped);
  };
  const checkActive = () => {
    if (stopped) throw stopped;
    if (Date.now() >= deadline) throw timeoutError();
  };
  const onAbort = () => stop(streamError("STREAM_CANCELLED", "已停止生成"));
  options.signal?.addEventListener("abort", onAbort, { once: true });
  const timer = setTimeout(() => stop(timeoutError()), Math.max(0, deadline - Date.now()));

  const execute = async () => {
    checkActive();
    if (options.signal?.aborted) throw streamError("STREAM_CANCELLED", "已停止生成");
    const body: QueryRequest = { question, collection_name: collectionName };
    if (options.topK !== undefined) body.top_k = options.topK;
    if (options.history !== undefined) body.history = options.history;
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}/query/stream`, {
        ...jsonRequest(body, "POST"),
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        signal: controller.signal,
      });
    } catch {
      checkActive();
      throw streamError("NETWORK_ERROR", "无法连接后端服务");
    }
    checkActive();
    if (!response.ok) return parseErrorResponse(response);
    if (!response.body) throw streamError("STREAM_INTERRUPTED", "回答连接已中断，请重新生成");
    reader = response.body.getReader();
    const decoder = new TextDecoder();
    const parser = new SSEParser();
    let answer = "";
    while (true) {
      let chunk: ReadableStreamReadResult<Uint8Array>;
      try {
        chunk = await reader.read();
      } catch {
        checkActive();
        throw streamError("STREAM_INTERRUPTED", "回答连接已中断，请重新生成");
      }
      checkActive();
      const frames = chunk.done
        ? parser.feed(decoder.decode(), true)
        : parser.feed(decoder.decode(chunk.value, { stream: true }));
      for (const frame of frames) {
        checkActive();
        const event = parseStreamEvent(frame, answer);
        if (!event) continue;
        checkActive();
        if (event.type === "delta") answer += event.text;
        if (event.type === "done" || event.type === "incomplete" || event.type === "error") {
          // Accept the first valid terminal before invoking the consumer: an
          // abort triggered by that callback cannot overwrite the result.
          terminalAccepted = true;
          options.onEvent(event);
          return;
        }
        options.onEvent(event);
      }
      if (chunk.done) throw streamError("STREAM_INTERRUPTED", "回答连接已中断，请重新生成");
    }
  };

  try {
    await Promise.race([execute(), stoppedPromise]);
  } catch (cause) {
    // Timers can run late; compare the actual deadline before accepting errors.
    if (!terminalAccepted && Date.now() >= deadline) throw timeoutError();
    throw cause;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", onAbort);
    controller.abort();
    if (reader) void reader.cancel().catch(() => {});
  }
}

function filesPath(collectionName: string): string {
  return `/files?collection_name=${encodeURIComponent(collectionName)}`;
}

export function listFiles(collectionName: string): Promise<FileListResponse> {
  return request<FileListResponse>(filesPath(collectionName));
}

export function previewFile(
  fileId: string,
  collectionName: string,
): Promise<PreviewResponse> {
  return request<PreviewResponse>(
    `/files/${encodeURIComponent(fileId)}/preview?collection_name=${encodeURIComponent(collectionName)}`,
  );
}

export function deleteFile(
  fileId: string,
  collectionName: string,
): Promise<FileDeleteResponse> {
  return request<FileDeleteResponse>(
    `/files/${encodeURIComponent(fileId)}?collection_name=${encodeURIComponent(collectionName)}`,
    { method: "DELETE" },
  );
}

export function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}
