# Task 8 重跑與人工評閱

這是明確啟動的合成開發驗收工具，不是 App 的歷史、日誌或自動 judge。從 repo 根目錄執行；先完成 README 的安裝。只讀固定的 C01–C12 fixture，透過現有 `PromptTransformer`／`LLMClient` 送出與產品相同的 system/user messages，不新增 sampling 或模型專用參數。

**Ornith 只做 12×2×1 暫時覆蓋。最終日常模型的 12×2×3 qualification、人工品質與 macOS Task 9 均未完成。** 舊 C08/Astra 是已完成但品質有問題的樣本，不能因為品質不佳而視為「缺項」。

## 先離線檢查與評閱

```powershell
# 不寫檔、不連網：查看固定案例矩陣
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance plan

# 查看已保存批次；已嘗試、失敗與中斷項目均不會列為可重送缺項
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance plan --batch docs/acceptance/evidence/ornith-coverage

# 產生新的可編輯人工評閱表，不覆寫既有檔案
New-Item -ItemType Directory -Force .local | Out-Null
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance report --batch docs/acceptance/evidence/ornith-coverage --output .local/ornith-human-review.md
```

`plan` 只代表尚未嘗試的格數；`report` 分別列完整回應／已記錄嘗試。零缺項不等於全部成功，更不等於品質通過。`started` 代表可能已送出但沒有完整落盤；`error` 是產品 client 判定的操作錯誤；兩者均保留，不自動重試。遇到操作錯誤批次立即停下，保留尚未嘗試項；排除原因後只能繼續尚未嘗試的項目。

評閱表依案例並列原文、Astra、Generic、原樣完整輸出與逐條 rubric。填寫 `must_preserve`、`must_not_add`、`execution_allowed` 的結果及證據，再填 reviewer/date/verdict/severe_errors/style_notes。未評閱的嚴重錯誤數必須留空，不能預填 0。代理初評另存，不能冒充人工填答。完整回應只代表符合 API 文字契約。

## 明確建立新批次

工具不讀 App 設定或剪貼簿。endpoint/model 必須明確指定，key 只從 `PROMPT_COACH_API_KEY` 環境變數讀取，使用現有產品 URL／認證驗證。不要把 key 放進命令、證據或 repo。`--backend-version` 是操作者提供的版本，未知保持 `unreported`；它不是工具自動驗證的模型身分。

以下為**未來指定後端並授權後**的操作模板，請先替換 Base URL／model。`prepare` 不送推論；目錄必須不存在。

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance prepare --batch .local/acceptance/selected-model --base-url http://127.0.0.1:8000/v1 --model SELECTED_MODEL --backend-version unreported
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance plan --batch .local/acceptance/selected-model

# 這個命令才會送出真實請求；limit 是本次最多新增的呼叫數
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance run --batch .local/acceptance/selected-model --limit 1
```

新批次預設一次，每格依 C01→C12、Astra→Generic 排序。重複執行 `run` 只繼續缺項；不重試失敗，不增加 judge。每格送出前以獨占檔案保存 request／`started` 並 flush/fsync，完成後原子更新結果。中斷後不要刪掉紀錄來求更好的結果。原始紀錄不可手動改寫；人工評閱填在另外的 Markdown。

最終模型可用並獲准後，另建新目錄，於 `prepare` 明確加 `--repeats 3`（72 格），不使用 `--seed-ornith-seven`。先依原 Task 8 做可見 GUI smoke／編輯／複製，將 GUI 證據獨立保存，再按授權上限執行矩陣。headless 工具不驗證 UI busy／clipboard／退出；原 Windows GUI 證據也不能當 macOS Task 9。

## 這次 Ornith 的補缺方式

本輪從舊七筆補剩餘 17 格；以下是已執行批次的建立方式，**不是要求再建一批重跑**：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance prepare --batch .local/acceptance/ornith-coverage --base-url http://127.0.0.1:8080/v1 --model dealignai/Ornith-1.5-9B-CRACK-GGUF:Q6_K --backend-version b10590-6657ded4f --seed-ornith-seven
.\.venv\Scripts\python.exe -X utf8 -m scripts.quality_acceptance run --batch .local/acceptance/ornith-coverage --limit 17
```

匯入會核對七個既定組合、fixture 原文、mode/profile、版本、HTTP 結果、實際送出的完整 system/user body 與現行政策。不同模型、版本、政策或三次矩陣不能匯入這七筆。原 `ornith-seven` 檔案不修改；新批次的 `legacy-gui` 紀錄是可追溯副本，17 個新樣本標為 `headless-product-client`。

## 有效政策與來源

- `prompts.py` 的 `POLICY_VERSION` 涵蓋共通規則、mode 與 profile 的組合；現為 1.0.0，本輪未改任何改寫文字。
- `policy_snapshot` 保存六種組合的完整 system prompt、UTF-8 SHA256、policy/profile 版本、source references 與 reviewed date。雜湊直接針對真正送出的 system 字串，不只看 profile 版本。
- `tests/fixtures/policy_hashes.json` 固定已檢視的六組雜湊；意外修改會使測試失敗。修改共通／mode 規則需升 `POLICY_VERSION`；修改 profile 規則也需升該 profile 版本。保留失敗例、記錄差異後才更新快照並重新評閱。
- `manifest.json` 另保存完整案例及 canonical JSON SHA256、Git HEAD、產品／工具／lock 檔的來源雜湊（UTF-8、換行正規化為 LF）、Python／OS／httpx 與 timeout。工作目錄可能有未提交變更，**HEAD 不能單獨代表執行程式**；來源雜湊才標定此次內容。
- 每筆保存實際 request body、原樣輸出、requested/reported model、UTC 時間、耗時、HTTP finish_reason／usage／timings（後端有提供時）。缺少 reported model 保持 null，不推測。
- 舊七筆沒有事前生成這套 manifest；其政策一致性是本輪與舊 request ledger 逐字比對後回溯確認，不能宣稱已重建當時全部環境。原檔 SHA256 保存於 `legacy_sha256`。
- `legacy_sha256` 是當時 Windows checkout 的原始位元組雜湊，JSON／Markdown 使用 CRLF；Git 的 LF checkout 會有不同位元組雜湊。跨平台核對文字可在記憶體中還原 CRLF 後計算，勿覆寫原檔；PNG 不轉換。政策、案例與 manifest 的 canonical 雜湊不受 checkout 換行影響。
- sampling 使用 server defaults，cache、執行順序及其他負載未受控；版本和雜湊方便追查與重跑，不保證逐字生成相同結果。

`run` 會拒絕政策、來源或案例已變更的批次，避免混算。純讀取 `plan`／`report` 可在後續版本檢視歷史批次。新模型、政策或程式版本需另建批次並保留舊結果。

## CI 與驗收界線

GitHub Actions 僅在 Windows／Python 3.12 安裝鎖定依賴、`pip check`、執行 offscreen pytest。測試阻擋 socket 連線，沒有 API key、真實推論或自動評分；套件安裝仍需要網路。CI 成功不代表可見桌面、模型品質或 macOS 已驗收。
