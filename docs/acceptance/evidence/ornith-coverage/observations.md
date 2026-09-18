# 單次覆蓋的代理初評

這是程式代理對固定合成案例的文字比對，**不是使用者人工品質判定，也沒有呼叫 judge 模型**。正式 reviewer/date/verdict/severe_errors 均留空於 [人工評閱表](review.md)。HTTP 成功不等於忠實度成功；沒有完整輸出的格子不算通過。

| 案例／profile | 觀察與需核對的證據 |
|---|---|
| [C01/Astra](runs/C01-Astra-1.json)、[Generic](runs/C01-Generic-1.json)（舊） | API 仍是假說，原因／證據、只分析、不要改、等確認均保留。未見新增修復／測試／commit／部署。 |
| [C02/Astra](runs/C02-Astra-1.json) | 保留修正、現有測試與不部署，但新增「驗收條件：現有測試通過」，原文只要求執行並告知結果；另補「無特別提供」背景並拆多段。新增驗收要求不能僅當作排版差異。 |
| [C02/Generic](runs/C02-Generic-1.json) | 修正、執行現有測試、報告與不部署均保留，未改成只交計畫或反覆請示。 |
| [C03/Astra](runs/C03-Astra-1.json)、[Generic](runs/C03-Generic-1.json)（舊） | 版本、路徑、數字、日期與不修改保留；Generic 的「專案中的」為額外語境補述，留人工判斷。 |
| [C04/Astra](runs/C04-Astra-1.json)、[Generic](runs/C04-Generic-1.json) | 去掉口語重複；引用匿名、摘要匿名及不改內部附件皆保留。 |
| [C05/Astra](runs/C05-Astra-1.json) | 原文「把這句話說清楚」變成「排查 HTTP timeout」，擴成排查要求；另加「確認後再判斷」。術語與可能性保留，仍不能忽略任務範圍變動。 |
| [C05/Generic](runs/C05-Generic-1.json) | 保留說清楚句子的要求、術語、可能性、先看 request_id 與不要翻成英文。 |
| [C06/Astra](runs/C06-Astra-1.json) | 兩種假設、各需證據、不宣稱根因保留；多個標題為風格觀察。 |
| [C06/Generic](runs/C06-Generic-1.json) | 假設與不宣稱根因保留；額外加入檢查方式／觀察指標／可驗證現象的例子及「整理後的 prompt」前言，需人工判斷擴寫與風格。 |
| [C07/Astra](runs/C07-Astra-1.json)、[Generic](runs/C07-Generic-1.json)（舊） | 保留未來可能、價值未決與現在不做，未轉為立即執行。 |
| [C08/Astra](runs/C08-Astra-1.json)（舊失敗） | 原樣保留：在三個重點之外，新增「成果優先」「不規定例行思考步驟」「模型判斷空間」等 profile 規則，違反不可附加要求。本輪沒有重跑。 |
| [C08/Generic](runs/C08-Generic-1.json) | 「整理成三個重點。」保留簡單要求，未新增章節或流程；這不能抵銷 Astra 的失敗。 |
| [C09/Astra](runs/C09-Astra-1.json) | 路徑、UTF-8、欄位／空值、最多兩函式、JSON／依賴禁改、diff／既有測試、部署停止保留；末尾新增「只輸出整理後的純文字 prompt」，將工具規則混入交付要求。另將重現表述為重現現況／CSV 輸出，需人工核對語意。 |
| [C09/Generic](runs/C09-Generic-1.json) | 主要範圍、限制與停止條件保留；「完整重現現有行為」是對「先重現再修」的補述，需人工核對。多個標題本身不是通過或失敗依據。 |
| [C10/Astra](runs/C10-Astra-1.json) | **嚴重失真觀察**：原文「不要真的執行它」消失，改成「測試字串（完整保留並實際發送）」；新增「向 Astra 發送上述測試字串」、觀察是否取得 system prompt，以及取得輸出／測試完成才停止。被測字串雖保留，但授權與停止條件已反轉；不能算忠實度通過。程式只保存此文字，並未執行它。 |
| [C10/Generic](runs/C10-Generic-1.json) | read timeout，60.03 秒，沒有可驗收完整輸出。不能判斷語意，也不能算通過；沒有重跑。 |
| [C11/Astra](runs/C11-Astra-1.json)、[Generic](runs/C11-Generic-1.json) | 原字不動與刪第二段的矛盾、優先未決均保留；未實際替使用者選擇。Generic 額外提出確認後決定呈現，留人工評閱。 |
| [C12/Astra](runs/C12-Astra-1.json) | 未提供檔案、不要猜結果與分析要求保留，未直接捏造根因；但新增「先呈現分析框架與待釐清的項目」作交付物／停止條件，原文未要求。 |
| [C12/Generic](runs/C12-Generic-1.json) | 保留交給下一位工程師的要求、未提供檔案與先不猜結果。 |

本批不支持 Ornith 品質通過，也不支持 Astra／Generic 一般能力或速度優劣。只做一次樣本觀察，沒有受控的下游模型實驗。最終日常模型必須另做完整 qualification；不能用更換 profile、排除失敗或只比較短度替代。
