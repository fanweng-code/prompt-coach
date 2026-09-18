# 公開內容隱私檢查

日期：2026-09-18。檢查 README、全部 tracked 檔案、8 張合成截圖、Git 歷史 blob 與 commit 作者／提交者 metadata。此記錄不重刊已發現的私人值。

## 發現與目前文件修正

| 位置 | 發現 | 處理 |
|---|---|---|
| README | 無私人 email 或實際使用者目錄；仍提及個人未來設備／模型計畫 | 改為一般性待驗敘述，新增公開資料邊界 |
| 設計、施工計畫、驗收文件 | 個人目錄、設備時程、與本專案無關的專案名稱／偏好 | 改為通用路徑、環境變數或移除無關內容；產品契約與合成測資不變 |
| Git commit metadata | 原作者與提交者 email 使用私人信箱 | 經使用者授權，已重寫 11 個 commit 並以 noreply email 取代；本 repo 後續提交亦使用 noreply |
| 合成輸出 JSON／請求帳本 | 案例文字與預期合成輸入一致，無 Authorization header 或 key | 保留原樣供審核；`human_review` 仍空白 |
| 8 張 PNG | 逐張檢視，只有測試 App、合成文字、模型及 loopback 標示 | 未見私訊、桌面其他視窗、姓名或 key；保留原樣 |
| `.gitignore` | 已排除 runtime、venv 與 `.local`，但缺少常見憑證檔規則 | 加入 `.env`、根目錄 settings.json 及常見私鑰／憑證副檔名排除 |

公開 GitHub 帳號、repo URL 與既有公開模型 ID 是必要識別資訊。合成 `D:\work\app.py` 不是真實使用者路徑；loopback 地址也不是公網 IP。未發現已追蹤的真實 API key、私鑰、登入 cookie、個人 prompt 或設定檔；此結論是本次人工／模式掃描的觀察，不是絕對無洩漏保證。

## 歷史與快取限制

**已依使用者明確授權，將清理後的 11 個 commit 以鎖定舊 main SHA 的 `--force-with-lease` 更新公開 `main`。** 已逐一核對重寫前後的程式、測試、JSON 與截圖 blob 不變；清理後歷史使用 noreply email，已移除指定個人路徑、設備時程、無關專案內容與舊 commit 引用。文件中的 task commit 對照已更新為清理後 SHA。

原始歷史備份僅留本機 ignored 目錄，未另推送備份分支或 tag。本機工作分支也已同步，避免再次發布舊歷史。清理後 SHA 與先前不同；若曾 clone 舊版，請重新 clone，不要把舊分支 merge 或 push 回來。

遠端重新 clone 驗證已確認：公開分支可達的 commit 均使用 noreply email，文字歷史未再命中本次指定私人資訊，8 張截圖與原始合成資料不變。不過匿名直接查詢舊 commit 的 GitHub API 仍回傳 HTTP 200；**伺服器舊物件／快取尚未完全移除**。GitHub Support 申請草稿只留本機，尚未代為送出。

即使重寫，既有 clone／fork 與 GitHub 快取仍可能保存舊資料；必要時需與持有者或 GitHub Support 協調，不能承諾撤回所有已公開副本。參考 [GitHub 官方敏感資料移除說明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)。
