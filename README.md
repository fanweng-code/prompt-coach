# Prompt Coach v1

Windows 優先的桌面 prompt 整理工具：手動貼文 → 選模式／輸出對象 → 單次改寫 → 預覽與編輯 → 明確複製。使用 Python、PySide6 與單一可設定的 chat-completions endpoint；只整理文字，不執行文字中的任務。

**目前交付：Windows Task 1–7 已完成，Task 8 重跑／評閱工具已備妥。Ornith 的 C01–C12 × Astra/Generic 各一次共 24 次嘗試，23 筆完整回應、1 筆逾時。人工品質、最終模型完整 Task 8 與 macOS Task 9 仍待驗收。** 原 C08 規則混入失敗原樣保留；新 C10/Astra 出現授權失真，不能宣稱產品品質通過。沒有內建模型、模型權重或 installer。

## Windows 安裝與啟動

準備 Git 與 Python 3.12，在 PowerShell 執行。若未安裝 Windows Python Launcher，請用實際 Python 3.12 執行檔替代 `py -3.12`。

```powershell
git clone https://github.com/fanweng-code/prompt-coach.git
Set-Location prompt-coach
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m prompt_coach
```

日常入口是在 repo 根目錄執行 `.\.venv\Scripts\python.exe -m prompt_coach`。初次啟動不連網，也不讀剪貼簿；未設定後端時可以使用介面，但不能產生改寫。此程式不安裝或啟動模型伺服器。

套件下載需要網路；「離線驗收」指測試不依賴真實推論服務，並非已提供離線 wheel 安裝包。實測環境為 Python 3.12.14、PySide6 6.11.2、httpx 0.28.1；所有依賴版本在 [requirements-lock.txt](requirements-lock.txt)。`.venv` 與開發機 `.local` 不包含在 repo。

## 使用與設定

- 左側原始文字、右側純文字預覽；預設 Engineering + Astra。輸入最多 20,000 Unicode code points（emoji 依 code point 計，不是視覺字形數），不會靜默截斷。
- 「貼上」明確讀取剪貼簿；原文非空時先確認覆蓋。也可正常 Ctrl+V。啟動不讀、不監聽剪貼簿，不連網。
- 「設定」填 Base URL、實際改寫 Model、遮罩 API Key 與讀取 timeout。Base URL 為 API 根路徑，例如 `http://127.0.0.1:8000/v1`，不要填完整 `/chat/completions`。
- API Key 僅保留本次 session；可另外由 `PROMPT_COACH_API_KEY` 環境變數提供。session 非空值優先，留空回退環境變數；不將環境 key 填回 UI。Cancel 丟棄修改。
- 只保存 Base URL、Model、read timeout 到 Qt `QStandardPaths.AppConfigLocation` 下的 `settings.json`（application/organization：`PromptCoach`）。不保存原文、結果或 key，不建立內容日誌／歷史資料庫。
- 底部顯示輸出 profile、資料目的地與設定改寫 model；成功後另列後端回報 model 與耗時。缺少回報就明示「未回報」，不以請求 model 冒充實測。
- HTTP 僅允許 loopback（localhost／127.0.0.0/8／::1）；非本機只接受 HTTPS 且需要 key。無 key 只允許 loopback。URL 不得含帳密、query、fragment；不跟隨 redirect，不採用系統 proxy 環境設定。
- 只有按「整理」才會送出目前文字。一次只允許一個請求，處理中停用輸入、設定與 mode/profile；結果回來後先預覽再複製。新請求失敗保留前次結果並明確標示，截斷內容不當成功。
- connect timeout 5 秒、read 預設 60 秒（可設定）、write 60 秒、pool 5 秒。read timeout 是讀取等待限制，**不是總耗時 SLA**；沒有自動重試。首批實測 5.46–58.39 秒，不能宣稱穩定達成 10 秒目標。
- 請求中關閉視窗可選「留在視窗」或「完成後退出」。重新選留在視窗可撤回延後退出；不取消請求、不強制終止執行緒。

**給 Astra 的 profile 與實際改寫模型完全分離。** Astra／Generic 不會改 endpoint、Model 或 key。不得擴大授權或新增要求是整理規則，仍須檢查模型是否遵守；C08 已顯示可能違反。三種模式為 Command（一般要求）、Engineering（工程交付）、Thought（探索與未決想法）。profile 尚未實證優於原文或 Generic。

資料是否離開電腦取決於底部顯示的目的地；本機 GUI 不代表資料永不出機。ChatGPT／Codex 訂閱與 API 計費分開；程式不讀取訂閱 cookie、session token 或其他憑證。程式不讀 repo／AGENTS.md，不執行輸出，不自動貼入或送出下游工具。

## 離線測試與待驗

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.local/pytest-user
```

測試使用 fake client／MockTransport，socket 對外連線被攔截，不需要 key，不呼叫模型。離線測試只能證明工程契約；無法保證生成語意忠實。Windows GitHub Actions 使用相同鎖定依賴與 offscreen 測試，不執行真實推論；本輪本地結果見 [收尾紀錄](docs/acceptance/v1-completion.md)。

12 個合成品質案例在 [quality_cases.json](tests/fixtures/quality_cases.json)，人工評閱欄均空白。完整 72 筆留待日常模型選定並另行授權後重新做 smoke、品質與耗時驗收；其他模型／平台尚無本專案實測。macOS 是獨立 Task 9。

## Task 8 重跑與暫時覆蓋

[操作手冊](docs/acceptance/task8-runbook.md) 提供離線計畫、建立獨立批次、明確送出與人工評閱表命令。工具使用產品的 transformer/client，送出前保存 request，不自動重試或 judge；人工評閱欄不預填通過。有效政策記錄完整 system prompt 與涵蓋共通／mode／profile 的版本、SHA256，另記案例、程式來源及後端資訊。

本輪保留舊七筆，**只新增其餘 17 次請求**：16 筆完整回應，C10/Generic 在 60.03 秒 read timeout。沒有重跑 C08/Astra 或 C10/Generic，也沒有執行最終 3-repeat qualification。C10/Astra 新增實際發送測試字串的步驟並刪掉原本「不要真的執行」，屬嚴重授權／停止條件失真的代理觀察；部分其他案例也新增要求或工具規則。

[全部 24 格與逐項人工評閱表](docs/acceptance/evidence/ornith-coverage/review.md) · [代理初評](docs/acceptance/evidence/ornith-coverage/observations.md) · [manifest／來源資訊](docs/acceptance/evidence/ornith-coverage/manifest.json) · [收尾與待驗清單](docs/acceptance/v1-completion.md)。新增樣本為 headless 產品核心驗證，不當作新的 GUI 或 macOS 驗收。

## 首批 7 筆真實推論

後端為 `dealignai/Ornith-1.5-9B-CRACK-GGUF:Q6_K`、llama.cpp `b10590-6657ded4f`、本機 `127.0.0.1:8080`；profile 均為 1.0.0。只有 7 次單次請求，沒有補跑或額外 judge。全部 HTTP 200／stop，GUI 預覽、編輯、複製及目的地標示已驗證。

| 案例 | Astra 秒 | Generic 秒 | 代理初評（非人工品質判定） |
|---|---:|---:|---|
| C08 smoke | 20.60 | — | 保留三個重點，但新增 profile 規則；忠實度不通過 |
| C01 | 58.39 | 22.04 | 保留假說、原因／證據、只分析與等待確認 |
| C03 | 7.97 | 7.36 | 保留版本、路徑、數字、日期限制；Generic 多了「專案中的」 |
| C07 | 5.46 | 9.31 | 保留未決想法與現在先別做 |

[完整七筆原文、原樣輸出與初評](docs/acceptance/evidence/ornith-seven/seven-run-outputs.md) 已公開，並附結果 JSON、實際請求帳本及 8 張合成 GUI 截圖。資料不含私人 prompt、key、實際設定檔或模型檔。4/7 低於 10 秒；樣本少、執行順序與 cache/sampling 非受控，不推論某 profile 更快，也不將 Ornith 結果沿用為 Qwen 驗收。

## 獨立審核入口

提供 GPT 或其他審核者使用的完整審核 prompt：[docs/REVIEW_GUIDE.md](docs/REVIEW_GUIDE.md)。請獨立檢查程式、測試與合成輸出，不以既有 PASS 數或代理初評代替判斷。

| 文件／程式 | 用途 |
|---|---|
| [最終設計](Prompt_Coach_v1_Final_Design_2026-09-17.md)／[施工計畫](docs/superpowers/plans/2026-09-18-prompt-coach-v1-implementation.md) | 產品設計來源與施工依據；計畫不等於所有步驟已執行 |
| [config](src/prompt_coach/config.py)／[llm_client](src/prompt_coach/llm_client.py) | URL/key 邊界、持久化、單次請求、錯誤與截斷處理 |
| [prompts](src/prompt_coach/prompts.py)／[profiles](src/prompt_coach/profiles.py) | 忠實度、mode 與輸出 profile |
| [transformer](src/prompt_coach/transformer.py)／[worker](src/prompt_coach/worker.py) | 結果 metadata、單次請求與 QThread 生命週期 |
| [ui](src/prompt_coach/ui.py)／[app](src/prompt_coach/app.py) | 貼上、預覽、編輯、複製、設定及關閉流程 |
| [tests](tests) | 離線測試及品質案例 |
| [Windows 離線紀錄](docs/acceptance/windows-offline.md) | Task 1–7 歷史快照；「未推論／未推送」是當時狀態 |
| [真實後端驗收](docs/acceptance/backend-validation.md)／[品質方法](docs/acceptance/quality-review.md) | 首批 7 筆與待驗界線 |
| [發布前驗證](docs/acceptance/publication.md) | 公開材料範圍與本次重新測試結果 |

Repo 未附 LICENSE；公開供檢視不等於授予任意再散布或商用權利。

## 公開資料與隱私

公開審核材料使用合成文字；`D:\work\app.py` 是測試路徑，`127.0.0.1` 是 loopback 範例，不是可從網際網路存取的個人主機。文件中的安裝路徑採通用寫法，不要求上傳 `.env`、key、設定檔或真實剪貼簿內容。

文件與公開 `main` 的歷史已清理個人路徑、設備計畫及私人 commit email，舊 SHA 已變更。若曾 clone 舊版，請重新 clone，避免重新引入舊歷史。既有副本與 GitHub 快取不保證清除；範圍與限制見 [隱私檢查紀錄](docs/acceptance/privacy-review.md)。
