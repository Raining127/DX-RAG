/**
 * TypeScript contracts for the DX-RAG backend API.
 *
 * These types mirror backend/app/models/schemas.py and the response
 * contracts in SPEC Section 6. There is intentionally no universal success
 * response wrapper.
 */

export interface Collection {
  name: string;
  file_count: number;
}

export type CollectionItem = Collection;

export interface CollectionCreateRequest {
  name: string;
}

export interface CollectionRenameRequest {
  new_name: string;
}

export interface CollectionResponse {
  message: string;
  name: string;
}

export interface CollectionRenameResponse {
  message: string;
  old_name: string;
  new_name: string;
}

export interface CollectionListResponse {
  collections: Collection[];
}

export type IngestionStatus = "SUCCESS" | "SUCCESS_WITH_WARNINGS";

export type UploadWarningCode = "OCR_PAGE_FAILED" | "PAGE_RENDER_FAILED";

export interface UploadWarning {
  page_number: number;
  error_code: UploadWarningCode;
}

export interface UploadResponse {
  status: IngestionStatus;
  message: string;
  file_id: string;
  file_name: string;
  chunks: number;
  collection_name: string;
  warnings: UploadWarning[];
}

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface QueryRequest {
  question: string;
  collection_name: string;
  top_k?: number;
  history?: ChatMessage[];
}

export interface Source {
  file_id: string;
  file_name: string;
  chunk_id: string;
  relevance_score: number;
}

export type SourceObject = Source;

export interface QueryResponse {
  answer: string;
  sources: Source[];
  query: string;
  collection_name: string;
}

export interface FileRecord {
  file_id: string;
  file_name: string;
  size: number;
  upload_time: string;
  chunk_count: number;
  status: IngestionStatus;
}

export interface FileListResponse {
  collection_name: string;
  files: FileRecord[];
}

export interface PreviewResponse {
  file_id: string;
  file_name: string;
  collection_name: string;
  content: string;
  preview_chars: number;
  total_chars: number;
}

export type FilePreviewResponse = PreviewResponse;

export interface FileDeleteResponse {
  message: string;
  file_name: string;
  collection_name: string;
}

export interface HealthResponse {
  status: "ok";
}

export type ApiErrorCode =
  | "INVALID_COLLECTION_NAME"
  | "COLLECTION_NOT_FOUND"
  | "COLLECTION_ALREADY_EXISTS"
  | "RENAME_FAILED"
  | "UNSUPPORTED_FILE_TYPE"
  | "INVALID_FILE_NAME"
  | "EMPTY_FILE"
  | "FILE_TOO_LARGE"
  | "FILE_ALREADY_EXISTS"
  | "FILE_NOT_FOUND"
  | "FILE_PARSE_ERROR"
  | "REQUEST_VALIDATION_ERROR"
  | "ENCRYPTED_PDF"
  | "INVALID_QUERY"
  | "INVALID_TOP_K"
  | "INVALID_HISTORY_FORMAT"
  | "LLM_NOT_CONFIGURED"
  | "LLM_AUTH_FAILED"
  | "LLM_UNAVAILABLE"
  | "LLM_RESPONSE_ERROR"
  | "EMBEDDING_MODEL_ERROR"
  | "OCR_NOT_CONFIGURED"
  | "OCR_AUTH_FAILED"
  | "COLLECTION_EMPTY"
  | "INTERNAL_ERROR"
  | "NETWORK_ERROR"
  | "INVALID_RESPONSE"
  | (string & {});

export interface ErrorDetails {
  [key: string]: unknown;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details: ErrorDetails;
}

export interface ErrorResponse {
  error: ErrorDetail;
}
