"""Unified error response model, AppError exception, and error catalog.

SPEC Section 6.7 — {error: {code, message, details}}
SPEC Section 9.1 — Error categories (400/404/409/413/422/500/502)
SPEC Section 9.2 — Error code catalog (23 application codes + INTERNAL_ERROR)
SPEC Section 9.4 — Unhandled errors → 500 INTERNAL_ERROR
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """A single error detail object."""

    code: str = Field(description="Machine-readable error code in UPPER_SNAKE_CASE")
    message: str = Field(description="Human-readable error description in Chinese")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Optional additional context"
    )


class ErrorResponse(BaseModel):
    """Unified error response envelope (SPEC Section 6.7)."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Error Catalog (SPEC Section 9.2)
# ---------------------------------------------------------------------------

# Each entry: (http_status, default_chinese_message)

_ERROR_CATALOG: Dict[str, tuple] = {
    # --- Collections ---
    "INVALID_COLLECTION_NAME": (400, "知识库名称格式无效"),
    "COLLECTION_NOT_FOUND": (404, "知识库不存在"),
    "COLLECTION_ALREADY_EXISTS": (409, "知识库名称已存在"),
    "RENAME_FAILED": (500, "重命名操作失败"),
    # --- Upload ---
    "UNSUPPORTED_FILE_TYPE": (400, "不支持的文件类型"),
    "INVALID_FILE_NAME": (400, "文件名包含非法字符或路径成分"),
    "EMPTY_FILE": (400, "文件为空"),
    "FILE_TOO_LARGE": (413, "文件大小超出限制"),
    "FILE_ALREADY_EXISTS": (409, "文件已存在"),
    # --- Files ---
    "FILE_NOT_FOUND": (404, "文件不存在"),
    # --- Ingest ---
    "FILE_PARSE_ERROR": (422, "文件解析失败"),
    "ENCRYPTED_PDF": (422, "PDF文件已加密，无法解析"),
    "OCR_NOT_CONFIGURED": (500, "DashScope API密钥未配置"),
    "OCR_AUTH_FAILED": (500, "DashScope API认证失败"),
    # WARNING-ONLY codes (SPEC Section 9.2: used in UploadResponse.warnings[],
    # NOT raised as standalone AppError — HTTP status is a sentinel, never exposed)
    "OCR_PAGE_FAILED": (500, "OCR识别单页失败"),
    "PAGE_RENDER_FAILED": (500, "页面渲染失败"),
    # --- Query ---
    "INVALID_QUERY": (400, "查询问题不能为空"),
    "INVALID_TOP_K": (400, "top_k参数超出有效范围"),
    "INVALID_HISTORY_FORMAT": (400, "历史记录格式无效"),
    "LLM_NOT_CONFIGURED": (500, "DeepSeek API密钥未配置"),
    "LLM_AUTH_FAILED": (500, "DeepSeek API认证失败"),
    "LLM_UNAVAILABLE": (502, "LLM服务不可用，重试已耗尽"),
    "LLM_RESPONSE_ERROR": (500, "LLM响应解析失败"),
    "EMBEDDING_MODEL_ERROR": (500, "嵌入模型加载或编码失败"),
    "COLLECTION_EMPTY": (409, "知识库中没有数据块"),
    # --- Global ---
    "INTERNAL_ERROR": (500, "服务器内部错误"),
}


def _get_catalog_entry(code: str) -> tuple:
    """Return (http_status, message) for a known code, or INTERNAL_ERROR fallback."""
    return _ERROR_CATALOG.get(
        code, _ERROR_CATALOG["INTERNAL_ERROR"]
    )


# ---------------------------------------------------------------------------
# Application Error
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Typed application error raised by services and endpoints.

    Usage::

        raise AppError("FILE_TOO_LARGE", details={"max_size_mb": 50})
        raise AppError("COLLECTION_NOT_FOUND")
        raise AppError("LLM_UNAVAILABLE", message="自定义错误描述")
    """

    def __init__(
        self,
        code: str,
        *,
        details: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> None:
        self.code = code
        _http_status, default_message = _get_catalog_entry(code)
        self.http_status: int = _http_status
        self.message: str = message if message is not None else default_message
        self.details: Dict[str, Any] = details if details is not None else {}
        super().__init__(self.message)
