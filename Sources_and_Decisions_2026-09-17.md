# 來源、證據限制與設計決策

查核日：2026-09-17。網站頁面和搜尋索引可能不同步；對會影響安裝的模型與runtime，以實作時鎖定的release、commit及artifact revision再確認。這份資料不提供自動更新保證。

## 官方與一手來源

| ID | 來源 | URL | 用途與限制 |
|---|---|---|---|
| S01 | OpenAI Model guidance：GPT-6 Astra | https://developers.openai.com/api/docs/guides/latest-model | 指令、釐清、驗證與API參數建議。查核時官方索引提供Astra內容，部分直接頁面快取仍顯示較早模型；施工時再次核對。不是精簡prompt必勝的實驗證據。 |
| S02 | OpenAI Reasoning best practices | https://developers.openai.com/api/docs/guides/reasoning-best-practices | 清楚直接的prompt、避免不必要思考指令。不可推論所有細節越少越好。 |
| S03 | Qt for Python：QClipboard | https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html | 剪貼簿介面；不代表本專案已跨平台測試。 |
| S04 | Qt for Python：QThread | https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html | worker與signal/生命週期設計基礎。 |
| S05 | HTTPX：Timeouts | https://www.python-httpx.org/advanced/timeouts/ | connect/read/write/pool timeout語意，不是整體SLA。 |
| S06 | OpenAI：ChatGPT/API subscription billing separation | https://help.openai.com/en/articles/8156019 | 程式呼叫API與ChatGPT訂閱額度分開。 |


## 證據等級

官方文檔證明有此介面或發布聲明；維護者/量化作者的測量證明其公布的條件下有報告；使用者自己的原始run才支持本機驗收。三者不得互換。

相同來源的搜尋摘要與頁面不算兩份獨立驗證。字眼如「designed for」「supports」「loaded」不能直接改寫成「長agent穩定可用」。

## 主要設計決策紀錄

| 決策 | 類型 | 原因 |
|---|---|---|
| 先Clipboard-first小視窗 | 使用者已選定 | 降低複雜度與半途而廢風險 |
| 單一可配置相容endpoint | 使用者已選定 | 現在雲端與未來本地可切換，先不做多provider |
| 三模式×兩profile | 使用者同意的修訂方向 | 意圖與目標表達分離 |
| 主動Paste、不自動讀clipboard | 本次安全/UX定稿 | 避免啟動時讀進敏感內容；不引入新平台 |
| 簡單Settings與session-only key | 本次可用性定稿 | GUI優先，不把日常使用綁到CLI或明文key檔案 |
| 不保證十秒／不保證精簡必勝 | 可信度邊界 | 由後端與實測決定 |

## 實際完成與未完成

本次產物：Prompt Coach 的 Markdown 規格、工作清單與來源表。可以檢查檔案存在、編碼、內容與封裝完整性。

未完成：應用程式實作、GUI運行、API呼叫、模型下載、Mac驗收、GitHub repo建立/修改、持續追蹤、自動提醒。任何後續報告都應延續這個界線，不把文件定稿當成軟體驗收。
