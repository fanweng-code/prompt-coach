# Windows 真實整合與 Ornith 首批品質觀察

日期：2026-09-18（Asia/Taipei）。**使用者直接授權的 7 筆合成推論已完成並停止；完整 Task 8 與人工品質尚未通過。** 本批為暫時後端觀察，不能代表未來日常 Qwen 模型通過。

## 範圍與可重現條件

| 欄位 | 實際值 |
|---|---|
| 產品程式 | Task 1–7 commit `[historical commit reference removed]`；本輪未修改產品程式或 profile |
| 平台 | Windows；Python 3.12.14；PySide6 6.11.2；httpx 0.28.1 |
| Base URL | `http://127.0.0.1:8080/v1`，本機 loopback、免 key |
| requested / reported model | 全部一致：`dealignai/Ornith-1.5-9B-CRACK-GGUF:Q6_K` |
| 執行中後端版本 | `/props` 回報 `b10590-6657ded4f`；本機 binary version 為 build 10590、commit 6657ded4f |
| 模型資訊 | `/v1/models` 回報 Q6_K、n_ctx 65536；未變更後端設定 |
| profile | Astra 1.0.0 / Generic 1.0.0；只影響整理規則，與實際改寫模型分離 |
| 請求 | `stream=false`，一個 system + 一個 user message；無重試、無 judge、無額外推論 |
| timeout | connect 5 秒、read 60 秒；read timeout 不是總耗時保證 |
| 量測方式 | App 的 `elapsed_s`（worker 內整理操作耗時）；HTTP 耗時、後端 usage/timings 另留原始紀錄 |

使用本機 ignored 的 `live_desktop.py` 啟動現有 `build_window`、worker、transformer、LLMClient 與真實 HTTPTransport；只加入請求上限、紀錄及截圖。這不是 fake/mock 回應。每次透過可見 Windows GUI 按「整理」，攔截器先核對下一筆案例/profile 與產品 builder 產生的訊息完全相同，再送往固定 loopback URL。請求帳本在網路送出前落盤，上限為 7。未接觸原有使用者 App 的設定與視窗。

## 真實整合驗證

| 驗證 | 實際證據與結果 |
|---|---|
| 單次請求 | 帳本恰好 7 筆，對應 7 次整理；全部只有 `model`、`stream`、`messages` 欄位，沒有重試 |
| 完整結果 | 7 次 HTTP 200、`finish_reason=stop`、非空完整 content，全部顯示於 GUI 並存下結果；未發生截斷或錯誤 |
| GUI 回應 | busy 狀態可見，避免重複整理；20ms Qt 主執行緒 timer 在每次推論期間持續觸發，次數見下表；完成後恢復操作 |
| 預覽／編輯／複製 | C08 結果先預覽，再由代理透過 GUI 加上「（人工編輯驗收標記）」、按 Copy、貼入專用合成編輯器並截圖；原始模型輸出獨立保留。此處人工編輯指 UI 操作，不是使用者人工品質評閱 |
| 資料目的地 | 每筆畫面顯示本機 loopback `127.0.0.1:8080`、設定 model、後端回報 model 與耗時 |
| profile 分離 | 切換 Command / Engineering / Thought 與 Astra / Generic 後，請求仍使用同一 endpoint/model；結果標籤保留產生該結果的 mode/profile/version |
| 收尾 | 七筆後關閉本次兩個驗收視窗；測試 harness 設有退出時還原原剪貼簿 MIME 的流程。原有使用者 App 保留 |

GUI busy timer 能證明主事件迴圈持續運行，不等同任意視窗操作都已覆蓋；本次未重做 Task 7 所有錯誤／關閉對話框案例。無 source 變更，因此本輪未重跑先前 124 項離線測試，也不把該離線數字當成本輪真實品質證據。

## 逐筆耗時與代理初評

每個 case/profile 僅一次（run index=1），C08 smoke 只計一次。人工評閱者、日期、verdict 仍空白。

| 次序 | case / mode | profile | 秒 | busy timer 次數 | 代理初評，非人工判定 |
|---|---|---|---:|---:|---|
| 1 | C08 / Command | Astra | 20.60 | 1031 | 本案忠實度不通過：三個重點仍在，但把 profile 規則新增到輸出 |
| 2 | C01 / Engineering | Astra | 58.39 | 2920 | 保留 API 假說、原因與證據、先不改程式、等待確認；五個標題屬風格觀察 |
| 3 | C01 / Engineering | Generic | 22.04 | 1102 | 同樣保留假說、證據與停止限制；未見新增執行授權 |
| 4 | C03 / Engineering | Astra | 7.97 | 399 | 版本、路徑、retry=0、timeout=10、差異說明與日期前不修改逐項保留 |
| 5 | C03 / Engineering | Generic | 7.36 | 368 | 同上；「專案中的」為原文未明示的輕微語境補述，待人工判斷 |
| 6 | C07 / Thought | Astra | 5.46 | 273 | 保留未來可能、價值未知、現在先別做；未轉執行工單 |
| 7 | C07 / Thought | Generic | 9.31 | 466 | 同上；價值未知改放括號，仍未轉執行 |

實測範圍 5.46–58.39 秒；4/7 低於 10 秒、3/7 超過。這只描述本批，不能宣稱十秒目標穩定達成。C01 Astra 的 58.39 秒接近目前 read timeout。樣本少、執行順序固定且後端 cache/sampling 非受控；不從這些差異推論某 profile 更快。

逐條初評依既有 fixture：C01 兩筆均未新增修復、新增測試、commit 或部署；C03 兩筆均保留 `Python 3.12`、`D:\work\app.py`、`retry=0`、`timeout=10`、`2026-09-24` 與不修改限制；C07 兩筆均未新增 deadline、驗收條件或立即實作。C08 沒有六段模板或專家角色套話，但新增「成果優先」「不規定例行思考步驟」「模型判斷空間」等規則，違反禁止附加要求的條目。不能因此將人工嚴重錯誤統計填 0，也不能將其餘六筆記為正式品質 PASS。

## 問題分類與處置

- **程式缺陷：** 目前未發現導致 C08 內容增加的程式缺陷。帳本確認 system/user 正確分離，產品接收後端 content，沒有把 profile 拼接進結果的路徑；不將模型回應問題當成 UI／HTTP 失敗。
- **規則歧義：** 共同規則已明確禁止新增要求；C08 原文也是簡單要求。目前沒有足以支持設計/profile 變更的證據。
- **模型能力／prompt 敏感性：** C08 呈現 profile 指令混入輸出的現象，暫歸此組合的指令遵循問題。單次樣本不足以精確分離模型能力與 prompt 敏感性的成因。保留失敗例，不針對暫時模型調 prompt、不降標準、不補跑。

## 完整輸出與 GUI 證據

全部為合成資料，原始紀錄留本機 ignored 目錄；這些檔案不會隨 Git checkout 攜帶。完整七筆原文、原樣輸出、metadata 與逐筆初評位於 [seven-run-outputs.md](../../.local/acceptance/backend-runs/seven-run-outputs.md)。

- [請求帳本（7 筆）](../../.local/acceptance/backend-runs/request-ledger.json)
- [完整結果與 HTTP / timing metadata](../../.local/acceptance/backend-runs/representative-runs.json)
- [授權後唯讀 preflight](../../.local/acceptance/backend-runs/authorized-preflight.json)
- [C08 結果 GUI](../../.local/acceptance/backend-runs/01-C08-Astra.png)、[編輯／複製結果](../../.local/acceptance/backend-runs/c08-edited-copy.png)
- [C01 Astra](../../.local/acceptance/backend-runs/02-C01-Astra.png)、[C01 Generic](../../.local/acceptance/backend-runs/03-C01-Generic.png)
- [C03 Astra](../../.local/acceptance/backend-runs/04-C03-Astra.png)、[C03 Generic](../../.local/acceptance/backend-runs/05-C03-Generic.png)
- [C07 Astra](../../.local/acceptance/backend-runs/06-C07-Astra.png)、[C07 Generic](../../.local/acceptance/backend-runs/07-C07-Generic.png)

唯讀紀錄核對命令（不發網路請求）：`.\.venv\Scripts\python.exe -X utf8 .local/acceptance/backend-runs/finalize_report.py`。實際完成：7 請求、7 結果、預期組合、目前 profile/system 訊息一致、HTTP 200/stop、8 個截圖檔案存在，且人工欄位仍空白。此為證據一致性檢查，不是品質 PASS。

## 待驗與最終模型驗收

1. 這七筆的使用者人工逐條品質評閱仍待完成，代理初評僅供參考。
2. 日常使用模型選定後，另行授權完整 72 筆；沿用 C01–C12、兩個 profile 各三次及原判定標準，重新做後端 smoke、品質與耗時驗證。其他日常模型尚未測試；本批 Ornith 結果不得沿用為其他模型的驗收。
3. macOS 相容性仍是獨立 Task 9，尚未執行。

未使用付費模型，未變更後端設定，未執行其餘批次、Task 9、push 或部署；本輪沒有宣稱完整 Task 8、產品品質或 Astra 下游改善已通過。
