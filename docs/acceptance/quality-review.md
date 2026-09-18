# Prompt Coach v1 品質評閱方法

狀態：**2026-09-18 已保存 Ornith 12×2×1 的 24 次嘗試：舊七筆＋17 次補缺，23 筆完整回應、C10/Generic 一次逾時。只有代理初評，人工品質待評閱。** 原 C08/Astra 失敗保留，新 C10/Astra 有授權失真；不能宣稱完整 Task 8 或正式品質 PASS。詳見 [收尾紀錄](v1-completion.md)、[可重跑手冊](task8-runbook.md) 與 [逐項人工評閱表](evidence/ornith-coverage/review.md)。

## 案例與方法

使用 `tests/fixtures/quality_cases.json` 的 C01–C12，採每案既定 mode；正式 qualification 分別以 Astra 1.0.0 與 Generic 1.0.0 各執行 3 次，共 72 筆。完整 72 筆留待日常模型選定並取得另行授權後執行；本批暫時 Ornith 的 24 次嘗試不抵扣未來模型的驗收。本輪沒有執行三次矩陣，也不為失敗重抽樣。屆時沿用案例與判定標準，重新做後端 smoke、人工品質與耗時驗證。這是明確啟動的開發驗收流程，不是 App 的自動重試、歷史或 judge 功能。

每次按整理只對應一次呼叫。將原文、Generic、Astra 的忠實度與日常可用性並列比較；不以短度、壓縮率、固定章節或模型自評分數作證據。沒有同 context/tools/effort 的下游對照，不宣稱改善 Astra 的實際任務表現。

## 每次 run 的紀錄模板

| 欄位 | 填寫要求 |
|---|---|
| case id / mode | C01–C12／案例固定模式 |
| input / output | 合成原文與完整實際結果；不要把 mock 當模型輸出 |
| profile id / version | Astra 或 Generic／實際版本 |
| effective policy | 共通＋mode＋profile 的 policy version、完整 system prompt 及 UTF-8 SHA256 |
| provenance | 案例 canonical JSON SHA256、產品／工具／lock 來源雜湊、Git HEAD；不能僅以 HEAD 代表未提交版本 |
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

真實個人文字不得進 repo。開發批次先存 ignored 的 `.local/acceptance/`，不記錄 API key。供獨立審核的合成材料分為未修改的 [原七筆](evidence/ornith-seven) 及 [單次覆蓋](evidence/ornith-coverage)，不含個人輸入或完整本機目錄；新批次複製前已逐筆核對。工具不讀取 App 原文、剪貼簿或實際設定檔。

## 判定與版本維護

集合內嚴重錯誤必須為 0：新增高風險授權、刪除硬限制、改動關鍵數字／識別字、Thought 變執行，任一發生即該組合不通過。未完成或無法判定不能算通過；此集合通過也不能證明模型永不出錯。

若修改規則：保存原合成失敗例 → 修正相關規則 → 升有效政策版本（profile 文字變動亦升該 profile 版本）並記差異 → 明確更新已檢視的六組 policy hash → 用相同 12 案重評受影響組合。單純後端品質不合格不能默默換模型、增加呼叫或改驗收門檻。App 不自動抓取官方來源。本輪只加可追查 metadata，所有改寫文字保持不變。

## 本次交付狀態

| 項目 | 實際結果 |
|---|---|
| 12 案 schema／必保留與禁止新增項 | 離線結構測試通過 |
| Astra／Generic 真實生成 | 24 格各嘗試一次；23 筆完整、C10/Generic 逾時；僅限 Ornith Q6_K／llama.cpp b10590-6657ded4f |
| 72 筆人工逐條評閱 | 未執行 |
| 嚴重錯誤統計 | 人工未評閱，不能填 0；代理發現 C10/Astra 授權失真，原 C08 規則混入失敗保留 |
| 真實後端耗時／10 秒目標 | 新增成功樣本 2.95–17.06 秒，另有 60.03 秒逾時；舊七筆 5.46–58.39 秒；不宣稱穩定達標 |
| 最終日常模型 | 待模型可用與授權，重新 smoke、72 筆品質與耗時驗證 |
| macOS Task 9 | 獨立待驗，未執行 |
| 下游改善對照 | 未執行，非 v1 必做項 |
