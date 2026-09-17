# 獨立審核入口

請以實際程式、測試與原始合成資料形成判斷，不將 README／驗收報告的結論當成已獨立證實。

## 建議閱讀順序

1. [README](../README.md)：安裝、產品行為、已驗與待驗。
2. [最終設計](../Prompt_Coach_v1_Final_Design_2026-09-17.md) 與 [施工計畫](superpowers/plans/2026-09-18-prompt-coach-v1-implementation.md)：規格與施工依據。
3. [src/prompt_coach](../src/prompt_coach) 與 [tests](../tests)：實際實作與測試覆蓋。
4. [七筆原文／輸出](acceptance/evidence/ornith-seven/seven-run-outputs.md)、[結果 JSON](acceptance/evidence/ornith-seven/representative-runs.json)、[請求帳本](acceptance/evidence/ornith-seven/request-ledger.json)：原意、數字、路徑、限制與授權。

[Windows 離線紀錄](acceptance/windows-offline.md) 是 Task 1–7 當時快照，其中「沒有真實後端／尚未推送」描述當時狀態。後續驗收與發布請讀 [後端驗收](acceptance/backend-validation.md) 和 [發布驗證](acceptance/publication.md)；未改寫歷史為當時已驗收。

## 可直接交給 GPT 的審核 prompt

```text
請獨立審核 https://github.com/fanweng-code/prompt-coach 。
先讀 README.md、docs/REVIEW_GUIDE.md、最終設計與施工計畫，再實際讀 src、tests 及公開的七筆合成推論材料。
請記錄你取得的 branch/commit；若無法存取某檔案或執行測試，列明限制，不推測已讀取或測試通過。

本次是唯讀審核。不要修改 repo、呼叫推論 endpoint、要求 API key 或執行額外模型批次。
若環境允許，可依 README 執行離線測試；靜態閱讀、實際測試與品質觀察必須分開標示。

請重點檢查：
1. 是否符合設計：只改寫、不執行；原意、硬限制、數字、路徑、否定詞、不確定性、授權與停止條件是否被保留。
2. profile 與實際改寫模型是否分離；Astra 不得新增要求或擴大權限；Thought 不得轉成執行工單。
3. URL/key/設定檔邊界、資料目的地標示、敏感內容日誌、單次請求、錯誤／截斷結果處理。
4. Qt worker 生命週期、busy 狀態、關閉對話框競態、留在視窗／完成後退出、結果保留及 Copy 行為。
5. 測試是否有重要缺口或只驗 implementation 自身；能執行的離線測試請記命令和結果。
6. 對七筆原文與輸出自行逐條評閱，不沿用代理 verdict；區分程式缺陷、規則歧義與模型能力／prompt 敏感性，不為暫時模型降低標準。

請以嚴重度排序 findings，附 file:line、觸發條件、具體影響、證據及最小修正建議。
不確定的事項分開列為待確認，不把假設寫成已重現 bug；若沒有 findings 也請列明覆蓋範圍。
最後列出尚未驗收：人工品質、最終模型完整 72 筆及 macOS Task 9。
124 項離線 PASS 或 7 次 HTTP 成功均不能證明完整 Task 8、產品品質或未來 Qwen 通過。
```

## 公開證據邊界

公開材料只含既有七筆合成推論的逐字輸入／輸出、送出 body、HTTP/timing metadata、逐筆代理初評及 GUI 截圖；沒有新增推論。截圖只顯示合成測資與 loopback 目的地。runtime、實際設定檔、模型、preflight 機器路徑與其他 `.local` 內容未發布。

原始 JSON 的 `human_review` 保持空白。這些資料可供獨立檢查本批文字與請求，但不足以測出模型一般能力、重現當時所有 sampling/cache 條件，或取代人工操作與最終模型驗收。
