# 公開內容隱私檢查

日期：2026-09-18。檢查 README、全部 tracked 檔案、8 張合成截圖、Git 歷史 blob 與 commit 作者／提交者 metadata。此記錄不重刊已發現的私人值。

## 發現與目前文件修正

| 位置 | 發現 | 處理 |
|---|---|---|
| README | 無私人 email 或實際使用者目錄；仍提及個人未來設備／模型計畫 | 改為一般性待驗敘述，新增公開資料邊界 |
| 設計、施工計畫、驗收文件 | 個人目錄、設備時程、與本專案無關的專案名稱／偏好 | 改為通用路徑、環境變數或移除無關內容；產品契約與合成測資不變 |
| Git commit metadata | 舊作者與提交者 email 使用私人信箱 | 本 repo 後續提交改用 GitHub 提供的 noreply email；舊 commit 不會因此改變 |
| 合成輸出 JSON／請求帳本 | 案例文字與預期合成輸入一致，無 Authorization header 或 key | 保留原樣供審核；`human_review` 仍空白 |
| 8 張 PNG | 逐張檢視，只有測試 App、合成文字、模型及 loopback 標示 | 未見私訊、桌面其他視窗、姓名或 key；保留原樣 |
| `.gitignore` | 已排除 runtime、venv 與 `.local`，但缺少常見憑證檔規則 | 加入 `.env`、根目錄 settings.json 及常見私鑰／憑證副檔名排除 |

公開 GitHub 帳號、repo URL 與既有公開模型 ID 是必要識別資訊。合成 `D:\work\app.py` 不是真實使用者路徑；loopback 地址也不是公網 IP。未發現已追蹤的真實 API key、私鑰、登入 cookie、個人 prompt 或設定檔；此結論是本次人工／模式掃描的觀察，不是絕對無洩漏保證。

## 歷史與快取限制

**目前文件修正不會清除舊 commit 中的私人 email、歷史路徑或無關個人資訊。** 本次普通提交也不代表已重寫遠端歷史。清理公開歷史需要另外替換 commit 並 force-push，會改變舊 SHA 及相關引用。

即使重寫，既有 clone／fork 與 GitHub 快取仍可能保存舊資料；必要時需與持有者或 GitHub Support 協調，不能承諾撤回所有已公開副本。參考 [GitHub 官方敏感資料移除說明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)。
