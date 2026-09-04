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
