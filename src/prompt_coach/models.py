from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal


class Mode(StrEnum):
    COMMAND = "Command"
    ENGINEERING = "Engineering"
    THOUGHT = "Thought"


class ProfileId(StrEnum):
    ASTRA = "Astra"
    GENERIC = "Generic"


@dataclass(frozen=True)
class AppConfig:
    base_url: str = ""
    model: str = ""
    read_timeout_s: float = 60.0


@dataclass(frozen=True)
class RequestSettings:
    base_url: str
    model: str
    read_timeout_s: float
    api_key: str = field(repr=False)
    is_loopback: bool
    host: str


@dataclass(frozen=True)
class Completion:
    text: str
    actual_model: str | None


@dataclass(frozen=True)
class RewriteResult:
    text: str
    mode: Mode
    profile_id: ProfileId
    profile_version: str
    requested_model: str
    actual_model: str | None
    elapsed_s: float
    status: Literal["success"] = "success"


ERROR_MESSAGES = {
    "input": "請輸入 1–20,000 個 Unicode 字元，不能只有空白。",
    "config": "設定無效或無法讀寫，請檢查 Base URL、Model 與讀取 timeout。",
    "auth": "認證失敗，請檢查 API Key 與權限。",
    "rate_limit": "已達頻率或額度限制，請稍後再試；不會自動重試。",
    "timeout": "請求逾時，請檢查後端或調整讀取 timeout。",
    "connection": "無法連線，請檢查後端與連線設定。",
    "http": "後端回傳 HTTP 錯誤，請檢查服務狀態。",
    "invalid_response": "後端未回傳有效的完整文字，請檢查 endpoint/model。",
    "unsupported_response": "此 endpoint/model 的回應型態不符合 v1 完整文字契約。",
    "truncated": "後端回應已截斷，未完成整理；保留前次結果。",
    "internal": "整理失敗，請再試一次。",
}


class RewriteError(Exception):
    def __init__(self, code: str, message: str | None = None):
        self.code = code if code in ERROR_MESSAGES else "internal"
        self.message = message or ERROR_MESSAGES[self.code]
        super().__init__(self.message)
