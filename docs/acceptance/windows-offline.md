# Windows 離線工程驗收

日期：2026-09-18（Asia/Taipei）。範圍：Task 1–7。**離線工程驗收通過；實際推論待驗收；人工品質待驗收；macOS 待驗收。** Task 8–9 未執行，沒有真實 endpoint、key、本地模型或付費推論呼叫。

## 環境與交付

| 項目 | 實測／實際狀態 |
|---|---|
| 工作目錄 | `C:\path\to\prompt-coach` |
| Windows | NT 10.0.26200，build 26200.9457，DisplayVersion 25H2；registry ProductName 回報 Windows 10 Home（保留原始回報，不以此推定行銷名稱） |
| Python | 3.12.14，uv 下載的 CPython，專案內 `.local/python/cpython-3.12.14-windows-x86_64-none/python.exe` |
| 執行／重現 venv | `.venv`／乾淨 `.venv-verify` |
| 核心版本 | PySide6／shiboken6 6.11.2、httpx 0.28.1、pytest 9.1.1、pytest-qt 4.5.0、setuptools 84.0.0；完整 pin 見 `requirements-lock.txt` |
| package | prompt-coach 0.1.0，editable 安裝；唯一日常入口 ` .\.venv\Scripts\python.exe -m prompt_coach` |
| 正式設定路徑 | Qt 回報 `%LOCALAPPDATA%\PromptCoach\PromptCoach\settings.json`；本次未建立此正式設定檔 |
| 桌面測試設定 | `.local/acceptance/desktop-settings.json`，只有合成 loopback URL、model、read timeout |
| 設計 SHA256 | `8ff1d496272b58dfaf52ec0bc8dec02d7b23245c23aa51ddfaac2633a908ec1e`，與計畫記錄相符；設計原件未修改 |

Task 1 安全設定與型別、Task 2 忠實度規則／獨立 profile、Task 3 單次 HTTP client、Task 4 Qt worker、Task 5 貼上／預覽／複製、Task 6 設定與入口、Task 7 12 案資料／文件／Windows 離線驗收均已交付。沒有新增產品 mock 模式、重試／judge、模型路由、歷史、錄音、repo 讀取或安裝器。

## 實際命令與結果

以下測試均使用合成資料，HTTP 僅 MockTransport，測試 fixture 清除環境 key 並攔截 socket 真實連線。XML 位於本機 ignored 目錄，不 commit。

| Task／範圍 | 使用 venv Python 的命令（省略共同前綴 `-m`） | exit | 結果／本機 XML |
|---|---|---:|---|
| T1 | `pytest tests/test_config.py -q --basetemp=.local/pytest-t1 --junitxml=.local/acceptance/t1.xml` | 0 | 32 passed |
| T2 | `pytest tests/test_transformer.py -q --junitxml=.local/acceptance/t2.xml` | 0 | 13 passed |
| T3 | `pytest tests/test_llm_client.py tests/test_transformer.py -q --junitxml=.local/acceptance/t3.xml` | 0 | 55 passed（包含 T2） |
| T4 | `pytest tests/test_worker.py -q --junitxml=.local/acceptance/t4.xml` | 0 | 5 passed |
| T5 | `pytest tests/test_ui.py tests/test_worker.py -q --junitxml=.local/acceptance/t5.xml` | 0 | 19 passed（包含 T4） |
| T6 | `pytest tests/test_app.py tests/test_ui.py tests/test_worker.py -q --basetemp=.local/pytest-t6 --junitxml=.local/acceptance/t6.xml` | 0 | 34 passed |
| T7 回歸紅燈 | `pytest tests/test_ui.py -q -k 'stay_revokes or finish_during' --junitxml=.local/acceptance/t7-close-red.xml` | 1 | 2 failed，成功重現退出缺陷 |
| T7 退出修復 | `pytest tests/test_ui.py tests/test_worker.py -q --junitxml=.local/acceptance/t7-close-green.xml` | 0 | 21 passed |
| 乾淨安裝 | `.venv-verify`：`pip install -r requirements-lock.txt`，`pip install --no-deps --no-build-isolation -e .` | 0／0 | 從精確 lock 重現；沒有修訂 lock |
| 依賴一致性 | `.venv-verify`：`pip check` | 0 | No broken requirements found |
| 最終全量 | `.venv-verify`：`pytest -q --basetemp=.local/pytest-final --junitxml=.local/acceptance/windows-offline.xml` | 0 | **124 passed，0 failed／error／skip** |

全量第一次是 122 passed；新增兩個真實退出缺陷的回歸後，最終為 124。各 task 的測試數有重疊，不能相加當成独立總數。T1–T6 初次新模組測試保存了缺少模組的 collection 紅燈 XML；這些只證明 scaffold 缺口，不冒充已進入行為的失敗。T7 案例資料缺檔與上述兩個退出回歸則是實際測試失敗。

## 真實 Windows 桌面與剪貼簿

正式 `-m prompt_coach` 入口已啟動到可見 Windows 桌面，觀察預設 Engineering + Astra、左右純文字與後端未設定，再正常關閉。沙箱中的視窗不在可控制桌面上，後續使用獲准的桌面 process 啟動；不是 offscreen 截圖。

接著以 `.venv-verify` 執行本機 ignored 的 `desktop_session.py`：沿用產品 `build_window`，Qt 真實剪貼簿、隔離設定，socket 禁止網路，不注入假成功结果。另一個合成文字／圖片 fixture 視窗僅供驗收，未加入產品。由 Computer Use 在可見桌面點擊與輸入，觀察如下：

| 操作 | 實際觀察 |
|---|---|
| 啟動 | 左右空白；記憶體 MIME 快照前後相同（`desktop-startup.json` 的 `clipboard_unchanged=true`）；startup 不連線另由離線測試保證 |
| 手動 Paste | 按貼上後才出現合成文字；中文、emoji、`<b>` 字面保留 |
| 普通 Ctrl+V | 原文編輯器正常插入剪貼簿文字，無全域快捷鍵 |
| 非文字 clipboard | 合成 QImage 放入 Windows clipboard 後按貼上，提示無文字；既有原文保持不變 |
| 覆蓋 Cancel | 對話框取消後仍保留完整既有原文 |
| 覆蓋 Yes | 確認後才以剪貼簿替換原文 |
| 預覽／Copy | 人工輸入合成預覽、明確 Copy，再 Ctrl+V 到另一個文字編輯器，內容一致；並非模型生成結果 |
| 設定 Save | URL／model／合成 key 可輸入，key 呈遮罩；目的地顯示本機 loopback、host:port 與設定 model |
| 設定檔檢查 | 只有 base_url、model、read_timeout_s；沒有合成 key、原文或結果 |
| 新 process 重開 | URL／model／timeout 恢復，API Key 欄空白；來源／結果也空白 |
| busy／失敗／退出 | 由 pytest-qt + fake／MockTransport 證明，包含實際 `QThread.finished` 生命週期、主迴圈存活與兩項邊界修復；不宣稱真實推論已測 |

本機合成截圖：`.local/acceptance/desktop-preview-copy.png`、`desktop-nontext.png`、`desktop-overwrite.png`、`desktop-settings-saved.png`、`desktop-reopened-settings.png`。前四張由可見 Qt 視窗擷取；重開設定截圖來自 Windows Computer Use。工具 inline 截圖亦留在本次任務。原剪貼簿只存記憶體，不輸出／寫檔；fixture 結束時還原。

## 最小修正與檢查

- 已有 uv，但沒有可用 3.12；下載至專案內。uv 建立 minor-version link 因本磁碟不支援而失敗，已解壓 runtime 可實測執行，直接以其完整路徑建立 venv。未改系統 PATH。
- Git 在此磁碟回報 ownership 不明，僅使用每次命令 `-c safe.directory=...`，未修改全域 Git 設定；沿用既有 Git identity。本機 branch 為 `implementation/v1-offline`，未配置 remote、push 或部署。
- 超長測資原本被 pytest 自動展開成測試名稱，觸發 Windows 32,767 字元環境變數限制；改成簡短案例 ID，未縮短測資或放寬限制。
- lock 排除本專案 editable 路徑，保留所有外部套件與 setuptools 精確 pin，避免把本機絕對路徑綁进乾淨安裝。
- 依獨立唯讀 review 重現並修復：先選完成後退出再改留在視窗，舊退出旗標仍生效；請求在退出對話框內完成，巢狀 close 被 Qt 忽略。新增回歸先證明兩項失敗，再在 `worker.py`／`ui.py` 撤回延後退出及接受原 close event；沒有取消請求或強制 terminate。
- 靜態檢查：serializer 僅三欄；沒有內容 logger、API key 持久化、HTTP body logging；GUI 錯誤使用安全訊息，未知例外不外洩任意內容。精確 stage 原始碼／合成 fixture／文件，`git diff --check` 與 staged whitespace check 通過，venv／`.local` 不納入 Git。

## 本機提交與待驗

| 邊界 | commit |
|---|---|
| 基線設計／計畫 | `[historical commit reference removed]` |
| T1 設定／契約 | `[historical commit reference removed]` |
| T2 忠實度／profile | `[historical commit reference removed]` |
| T3 HTTP client | `[historical commit reference removed]` |
| T4 worker | `[historical commit reference removed]` |
| T5 主視窗 | `[historical commit reference removed]` |
| T6 設定／入口 | `[historical commit reference removed]` |
| T7 案例／文件／退出回歸 | 本紀錄所屬的 `test: add quality cases and Windows offline acceptance` commit，使用 `git log -1` 查詢 |

尚未驗收：真實後端相容性／實際推論、12×2×3 的人工語意品質、實際耗時／10 秒目標、macOS 真機啟動／clipboard／thread。12 案的人工評閱欄均空白。mock PASS 不能取代這些項目，也不代表完整 Windows v1 推論品質或跨平台完成。
