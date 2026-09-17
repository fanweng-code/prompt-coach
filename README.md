# Prompt Coach v1

Windows 優先的單機桌面 prompt 整理工具：手動貼文 → 選模式／輸出對象 → 單次改寫 → 預覽與人工編輯 → 明確複製。

**目前交付：離線工程驗收通過；實際推論與人工品質待驗收。macOS 待驗收。** 沒有內建模型，尚未設定真實 endpoint；啟動可使用介面，但不能因此宣稱已可產生經驗證的改寫。詳見 [Windows 驗收紀錄](docs/acceptance/windows-offline.md)。

## 日常啟動

在 PowerShell 進入專案後，使用唯一日常入口：

```powershell
Set-Location -LiteralPath 'C:\path\to\prompt-coach'
.\.venv\Scripts\python.exe -m prompt_coach
```

目前已準備 `.venv`。本機 Python 3.12.14 位於 `.local/python/cpython-3.12.14-windows-x86_64-none/python.exe`；`.venv` 依賴這個 runtime，請勿單獨移除它。

## 初次安裝／另一台 Windows

準備 Python 3.12，將 `$Python312` 指向實際執行檔；下列範例使用本次交付的專案內 runtime：

```powershell
$Python312 = 'C:\path\to\prompt-coach\.local\python\cpython-3.12.14-windows-x86_64-none\python.exe'
& $Python312 --version
& $Python312 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pip check
```

在新機器請改用該機已安裝的 Python 3.12 路徑。套件下載需要網路；「離線驗收」指測試不依賴真實推論服務，並非已提供離線 wheel 安裝包。所有實測依賴版本在 `requirements-lock.txt`。沒有 installer。

## 使用與設定

- 左側原始文字、右側純文字預覽；預設 Engineering + Astra。輸入最多 20,000 Unicode code points（emoji 依 code point 計，不是視覺字形數），不會靜默截斷。
- 「貼上」明確讀取剪貼簿；原文非空時先確認覆蓋。也可正常 Ctrl+V。啟動不讀、不監聽剪貼簿，不連網。
- 「設定」填 Base URL、實際改寫 Model、遮罩 API Key 與讀取 timeout。Base URL 為 API 根路徑，例如 `http://127.0.0.1:8000/v1`，不要填完整 `/chat/completions`。
- API Key 僅保留本次 session；可另外由 `PROMPT_COACH_API_KEY` 環境變數提供。session 非空值優先，留空回退環境變數；不將環境 key 填回 UI。Cancel 丟棄修改。
- 只保存 Base URL、Model、read timeout 到 Qt `QStandardPaths.AppConfigLocation` 下的 `settings.json`（application/organization：`PromptCoach`）。不保存原文、結果或 key，不建立內容日誌／歷史資料庫。
- 底部顯示輸出 profile、資料目的地與設定改寫 model；成功後另列後端回報 model 與耗時。缺少回報就明示「未回報」，不以請求 model 冒充實測。
- HTTP 僅允許 loopback（localhost／127.0.0.0/8／::1）；非本機只接受 HTTPS 且需要 key。無 key 只允許 loopback。URL 不得含帳密、query、fragment；不跟隨 redirect，不採用系統 proxy 環境設定。
- 只有按「整理」才會送出目前文字。一次只允許一個請求，處理中停用輸入、設定與 mode/profile；結果回來後先預覽再複製。新請求失敗保留前次結果並明確標示，截斷內容不當成功。
- connect timeout 5 秒、read 預設 60 秒（可設定）、write 60 秒、pool 5 秒。read timeout 是讀取等待限制，**不是總耗時 SLA**；沒有自動重試。10 秒體感目標尚無真實後端量測。
- 請求中關閉視窗可選「留在視窗」或「完成後退出」。重新選留在視窗可撤回延後退出；不取消請求、不強制終止執行緒。

**給 Astra 的 profile 與實際改寫模型完全分離。** Astra／Generic 不會改 endpoint、Model、key，也不擴大原文授權或新增要求。三種模式為 Command（一般要求）、Engineering（工程交付）、Thought（探索與未決想法）。profile 是依指引設計的整理策略，尚未實證優於原文或 Generic。

資料是否離開電腦取決於底部顯示的目的地；本機 GUI 不代表資料永不出機。ChatGPT／Codex 訂閱與 API 計費分開；程式不讀取訂閱 cookie、session token 或其他憑證。程式不讀 repo／AGENTS.md，不執行輸出，不自動貼入或送出下游工具。

## 離線測試與待驗

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.local/pytest-user
```

測試使用 fake client／MockTransport，socket 對外連線被攔截，不需要 key，不呼叫付費模型。124 項通過只能證明工程契約；無法保證生成語意忠實。

12 個合成品質案例在 `tests/fixtures/quality_cases.json`，人工評閱欄均空白。[品質評閱方法](docs/acceptance/quality-review.md) 為未來驗收準備，尚未執行 72 次真實改寫、人工評閱或 macOS 驗收（Task 8–9 未執行）。
