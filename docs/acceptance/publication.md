# 公開 repo 發布前驗證

日期：2026-09-18（Asia/Taipei）。使用者授權建立公開 GitHub repo、完成 README 並推送，供 GPT 獨立審核。目標為 `fanweng-code/prompt-coach`，公開分支 `main`。本輪只改文件並公開既有合成證據，未修改產品程式、profile、模型或後端設定，沒有新增推論。

## 本次實際重新驗證

在既有 Windows／Python 3.12.14 的 `.venv` 執行：

| 命令 | 結果 |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.local/pytest-publication --junitxml=.local/acceptance/publication.xml` | exit 0；124 passed in 3.15s |
| `.\.venv\Scripts\python.exe -m pip check` | exit 0；No broken requirements found |

這是離線工程測試重跑，並非新增真實模型推論、人工品質或 macOS 驗收。原始 JUnit XML 留在本機 ignored 目錄。

## 公開內容

- 程式、測試、12 案品質 fixture、依賴版本、設計／施工計畫與驗收文件，保留本機開發 commit 歷史。
- README 改為可從 GitHub clone 的 Windows 安裝流程，更新真實推論狀態、限制與審核入口。
- [REVIEW_GUIDE.md](../REVIEW_GUIDE.md) 提供閱讀順序與唯讀審核 prompt，不授權額外推論。
- [ornith-seven](evidence/ornith-seven) 中的 11 個檔案，逐位元複製自既有七筆合成驗收：完整輸出 Markdown、結果 JSON、請求帳本與 8 張合成 GUI 截圖。JSON 中人工評閱欄維持空白。

公開材料不包含 `.venv`、`.local`、runtime、模型權重、實際設定檔、key 或個人輸入。後續隱私複查發現初版文件仍帶有個人路徑、無關專案資訊，且 commit metadata 使用私人 email；文件已去識別化，歷史 metadata 的處理另見 [隱私檢查紀錄](privacy-review.md)。未另行選擇授權條款或新增 LICENSE。

## 結論限制

目前只有 Ornith Q6_K／llama.cpp b10590-6657ded4f 的七筆真實整合與代理初評。C08 混入 profile 規則的失敗例原樣保留。人工品質、日常模型完整 72 筆及 macOS Task 9 仍待驗；公開 repo 不改變這些驗收狀態。
