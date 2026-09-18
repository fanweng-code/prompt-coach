# v1 收尾與 Ornith 單次覆蓋

日期：2026-09-18（Asia/Taipei）。起點為 GitHub `main`／本地 HEAD `8a9f8983e9ae04005a08cd18926c2f83f8318f11`，已以遠端 `refs/heads/main` 核對；工作目錄起初乾淨。

**Task 8 的重跑／評閱工具已補齊；Ornith 24 組各有一次嘗試，但只有 23 筆完整回應。品質未通過，最終日常模型 qualification 與 macOS Task 9 維持待驗。**

## 本輪實作與驗證

- 新增 repo 內開發工具 `scripts/quality_acceptance.py`：離線 plan／prepare／report、明確 run、呼叫上限、僅補缺項、送出前落盤、操作失敗停止、中斷／失敗不重送。沿用產品 transformer/client，不改 GUI 或 HTTP 請求參數。
- 新增六種有效政策快照：完整 system prompt、policy/profile 版本、SHA256、來源索引及檢視日；固定版本雜湊測試可發現未記錄的政策文字變動。共通、mode、Astra／Generic 實際文字完全不變，沒有針對 Ornith 調參。
- 新增 Windows／Python 3.12 GitHub Actions，僅執行鎖定依賴安裝、`pip check` 與 offscreen 離線測試。本地驗證完成時尚未推送；GitHub hosted CI 以此提交的 Actions 實際結果為準。
- 操作方式與未來最終模型流程見 [Task 8 手冊](task8-runbook.md)。本輪沒有 mic/STT、hotkeys、tray、overlay、history 或自動 Codex 整合。

本地 Windows／Python 3.12.14 實際驗證：

| 檢查 | 結果 |
|---|---|
| 基線 pytest | 124 passed in 2.99s |
| `QT_QPA_PLATFORM=offscreen`，`python -m pytest -q --basetemp=.local/pytest-v1-final --junitxml=.local/acceptance/v1-final.xml` | **138 passed in 3.17s**；含 14 個新增工具／證據測試 |
| `python -m pip check` | No broken requirements found |
| 公開批次離線 `plan`／重建 `report` | 0 個未嘗試項；重建評閱表與交付檔逐字一致，23/24 完整回應 |
| provenance／舊證據 | 政策、案例與實際來源雜湊一致；原 11 檔 SHA256 未變動，與基線 Git 內容一致（文字換行正規化後） |
| 文件與變更檢查 | 交付文件相對連結存在；合成證據未含 key／私人使用者路徑；程式與人工文件 whitespace 檢查通過，生成評閱表保留 Markdown 空白引述行 |

這些是本地離線與證據一致性檢查，不是 GitHub hosted CI 或模型品質 PASS。JUnit XML 留在 ignored 的 `.local/acceptance/v1-final.xml`。

## 真實請求與證據

模型仍為 `dealignai/Ornith-1.5-9B-CRACK-GGUF:Q6_K`；`http://127.0.0.1:8080/v1`；llama.cpp `/props` 回報 `b10590-6657ded4f`。補跑前以 GET health／models／props 查核，未修改 server 設定。[去除私人路徑的 preflight](evidence/ornith-coverage/preflight.json) 保存可得的模型資訊及 sampling defaults；不含 key、server 模型檔路徑或個人資料。

舊七筆由 `ornith-seven` 原樣匯入，核對 fixture、實際 request body 與現行 policy 後標為 `legacy-gui`。其原始檔案完全未修改，包含 C08/Astra 失敗、帳本及八張截圖。

新增請求只送 C02／C04／C05／C06／C09／C10／C11／C12 的兩個 profile，以及 C08/Generic，共 **17 次**。新資料使用 `headless-product-client`，不是 GUI 複驗。第一次 `run --limit 17` 在第 13 次新請求 C10/Generic 讀取逾時後停止；唯讀確認 health 正常後，以 `run --limit 4` 只送尚未嘗試的 C11/C12。沒有重送 C10/Generic，沒有重送舊 C08/Astra，沒有 judge、補抽樣或三次 qualification。

| 案例 | Astra：秒／結果 | Generic：秒／結果 |
|---|---|---|
| C01（舊） | 58.39／完整 | 22.04／完整 |
| C02 | 16.76／完整 | 4.68／完整 |
| C03（舊） | 7.97／完整 | 7.36／完整 |
| C04 | 9.63／完整 | 4.78／完整 |
| C05 | 8.40／完整 | 6.91／完整 |
| C06 | 17.06／完整 | 7.69／完整 |
| C07（舊） | 5.46／完整 | 9.31／完整 |
| C08 | 20.60／完整（舊失敗樣本） | 4.42／完整 |
| C09 | 5.41／完整 | 7.04／完整 |
| C10 | 13.00／完整 | 60.03／read timeout |
| C11 | 2.95／完整 | 6.85／完整 |
| C12 | 5.79／完整 | 8.98／完整 |

「完整」僅表示 HTTP 200、finish_reason=stop、有效文字，**不表示語意通過**。C10/Generic 未取得完整可驗收回應，output／actual_model 為 null，不用 requested model 冒充回報。新批次成功請求耗時 2.95–17.06 秒，另有 60.03 秒逾時；不刪掉逾時樣本計算達標率。跨批次 cache、順序、sampling、負載未受控，不據此比較 profile 優劣。

完整證據：

- [manifest](evidence/ornith-coverage/manifest.json)：完整政策、案例、程式來源雜湊與執行條件。
- [24 個逐次紀錄](evidence/ornith-coverage/runs)：七筆可追溯副本＋17 筆新請求，每格 run_index=1；23 complete、1 error、沒有 pending/started。
- [逐項人工評閱表](evidence/ornith-coverage/review.md)：完整輸出與 rubric；人工欄位保持空白。
- [代理初評](evidence/ornith-coverage/observations.md)：獨立於人工欄位，不當作正式品質驗收。

## 品質結論與待驗

除了原 C08/Astra 混入 profile 規則，新 C10/Astra 將「不要真的執行」改成「完整保留並實際發送」、新增向 Astra 發送字串的步驟與停止條件，是代理觀察到的嚴重授權／停止條件失真。C02/Astra、C05/Astra、C09/Astra、C12/Astra 也有新增條件、改變任務範圍或混入工具規則的問題。逐句證據見代理初評；未為這些失敗調整門檻或改 prompt 後重跑。

| 剩餘項目 | 狀態 |
|---|---|
| 使用者人工逐條品質評閱 | 待完成；severe_errors 未預填 0 |
| Ornith C10/Generic 完整輸出 | 本次逾時，保留失敗；本輪不補跑 |
| 最終日常改寫模型 smoke＋72 筆＋人工品質／耗時 | 待模型可用並授權；Ornith 不抵扣 |
| macOS Task 9 可見實機啟動／clipboard／thread | 待 Mac 可用；CI／Windows 不抵扣 |
| Astra 下游表現改善對照 | 未執行，非 v1 必做 |

不能宣稱完整 Task 8、完整 v1 或跨平台已完成。
