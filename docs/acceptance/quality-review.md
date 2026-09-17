# Prompt Coach v1 品質評閱方法

狀態：**資料集與評閱格式已建立；真實改寫與人工評閱未執行。** 目前沒有 endpoint/model/key。Task 8–9 不在本次交付範圍，沒有任何 case 的品質 PASS。

## 案例與方法

使用 `tests/fixtures/quality_cases.json` 的 C01–C12，採每案既定 mode；分別以 Astra 1.0.0 與 Generic 1.0.0 各執行 3 次，共 72 筆。這是之後取得使用者對指定後端及呼叫／費用範圍授權後的人工開發驗收流程，不是 App 的自動重試、歷史或 judge 功能。

每次按整理只對應一次呼叫。將原文、Generic、Astra 的忠實度與日常可用性並列比較；不以短度、壓縮率、固定章節或模型自評分數作證據。沒有同 context/tools/effort 的下游對照，不宣稱改善 Astra 的實際任務表現。

## 每次 run 的紀錄模板

| 欄位 | 填寫要求 |
|---|---|
| case id / mode | C01–C12／案例固定模式 |
| input / output | 合成原文與完整實際結果；不要把 mock 當模型輸出 |
| profile id / version | Astra 或 Generic／實際版本 |
| endpoint host | 僅資料目的地主機；不含認證 |
| requested backend model | 設定請求的 model |
| reported backend model | 回應實際回報；缺失填「未回報」 |
| backend version | 僅填可確認版本；未知填「未回報」，不推測 |
| run index / elapsed_s | 1–3／實測耗時與量測條件 |
| reviewer / date | 人工評閱者／實際日期；未評閱保持空白 |
| must_preserve 逐條結果 | 每個條目：保留／遺漏／改動／無法判定，附原文與輸出證據 |
| must_not_add 逐條結果 | 每個條目：未新增／新增／無法判定，附證據 |
| execution_allowed | 核對授權與停止條件；Astra 不得放權，Thought 不得轉執行 |
| severe_errors | 每项嚴重錯誤與對應句子；未評閱不能先填 0 |
| style_notes | 風格差異與日常可用性，與忠實度判定分開 |
| verdict / notes | 通過／不通過／待釐清；未評閱空白 |

真實個人文字不得進 repo。合成 run 原始紀錄可留本機 ignored 的 `.local/acceptance/backend-runs/`，正式文件只寫去識別化摘要；不記錄 API key。

## 判定與版本維護

集合內嚴重錯誤必須為 0：新增高風險授權、刪除硬限制、改動關鍵數字／識別字、Thought 變執行，任一發生即該組合不通過。未完成或無法判定不能算通過；此集合通過也不能證明模型永不出錯。

若修改 profile 規則：保存原合成失敗例 → 修正相關規則 → 升 profile 版本並記差異 → 用相同 12 案重評受影響 profile。單純後端品質不合格不能默默換模型、增加呼叫或改驗收門檻。App 不自動抓取官方來源。

## 本次交付狀態

| 項目 | 實際結果 |
|---|---|
| 12 案 schema／必保留與禁止新增項 | 離線結構測試通過 |
| Astra／Generic 真實生成 | 未執行 |
| 72 筆人工逐條評閱 | 未執行 |
| 嚴重錯誤統計 | 未評閱，無數據 |
| 真實後端耗時／10 秒目標 | 未量測 |
| 下游改善對照 | 未執行，非 v1 必做項 |
