# you asked

message time: 2026-05-06 13:09:32

[文件: main.py]

好的，請幫我做一個開發者導向的文檔。內容可能先闡述一下"主架構是 parse用戶生成的字串，然後取第一個單字做為 command。對於每個合法 command 會呼叫目標函式。既然 parsing 正確，那只要函示 behavior 正確程式就沒毛病。"，然後先列舉每個函示的 expected behaviour, 交互作用

---

# deepseek response

# 開發者導向技術文檔

## 1. 整體架構概述

本程式是一個**事件迴圈命令列介面 (REPL)**。使用者輸入字串後，程式以空白分割，取第一個單字作為命令（command），其餘部分作為參數。主迴圈根據命令名稱呼叫對應的處理函數。  

所有交易資料儲存於一個 Python 字典（`dict[int, dict]`），鍵為交易 ID，值為包含所有欄位的交易記錄。此結構提供 O(1) 的 ID 查詢與刪除效能。  

程式狀態的變更（新增、刪除、編輯、匯入）都會自動推入 `undo_stack`，支援復原／重做（最多 20 層）。交易日誌、週期規則、預算設定分別儲存於三個 JSON 檔案。  

**核心設計原則**：  
- 解析正確 ⇒ 呼叫對應函數 ⇒ 只要函數行為正確，程式即正確。  
- 所有修改操作皆先呼叫 `save_state()` 保存當前狀態，再執行實際變更，最後呼叫 `save_transactions()` 持久化。  
- 唯讀操作（list, balance, search, perftest, help）不影響狀態，不觸發 `save_state`。

---

## 2. 命令解析與調度

位於 `main()` 函數的 `while True` 迴圈中。  
- 使用 `input("\n>> ").strip()` 取得使用者輸入。  
- 以 `split()` 分割為 `parts` 列表。  
- `cmd = parts[0].lower()` 決定命令。  
- 根據命令名稱，以 `if/elif` 分支呼叫對應函數，並傳入必要參數（如 `transactions` 字典）。  
- 多數命令會更新 `transactions` 變數（因為字典可能被重新指派，例如 `undo` 或 `rebuild_ids` 後）。  

**命令與函數對照表**（節錄主要部分）：

| 命令 | 處理函數 | 說明 |
|------|----------|------|
| `add` | `add_transaction` | 互動式新增交易 |
| `misc` | `run_macro(..., "misc", ...)` | 快速雜支 |
| `macro` | `run_macro` | 使用預設巨集 |
| `list` | `list_transactions` | 顯示交易列表 |
| `balance` | `show_balance` | 顯示帳戶餘額 |
| `delete` | `delete_transaction` | 刪除交易並重新編號 |
| `edit` | `edit_transaction` | 修改交易欄位 |
| `comment` | `add_comment` | 新增或編輯註解 |
| `undo` | `undo` | 復原上一操作 |
| `redo` | `redo` | 重做被復原的操作 |
| `recur add` | `add_recurring` | 新增週期規則 |
| `recur list` | `list_recurring` | 列出週期規則 |
| `recur delete` | `delete_recurring` | 刪除週期規則 |
| `recur run` | `run_recurring` | 執行到期週期交易 |
| `budget set` | `set_budget` | 設定預算 |
| `budget show` | `show_budget_report` | 顯示預算報表 |
| `search` | `search_transactions` | 搜尋交易 |
| `export` | `export_transactions` | 匯出至 JSON/CSV |
| `import` | `import_transactions` | 匯入並合併或取代 |
| `perftest` | `perf_test_list_vs_dict` | 效能比較 |
| `help` | `show_help` | 顯示幫助選單 |
| `exit` | 跳出迴圈，儲存後結束 | |

---

## 3. 核心資料結構

### `transactions_dict: dict[int, dict]`
範例單筆交易結構：
```python
{
    "id": 1,
    "date": "2026-05-06 14:30:00",
    "desc": "Coffee",
    "amount": 3.5,
    "dr": "Food",
    "cr": "Cash",
    "comment": "Starbucks"
}
```
- 所有交易以此字典儲存，**鍵為 ID，值為交易記錄**。  
- ID 由程式自動產生（最大 ID + 1），刪除後會呼叫 `rebuild_ids()` 重新編號，確保連續性。

### 全域堆疊
```python
undo_stack: list[dict]   # 儲存 deep copy 的 transactions_dict
redo_stack: list[dict]
MAX_UNDO = 20
```
- 每次修改前呼叫 `save_state(transactions_dict)`，將當前狀態深拷貝後推入 `undo_stack`，並清空 `redo_stack`。  
- `undo()` 將目前狀態推入 `redo_stack`，然後彈出 `undo_stack` 的最後狀態作為新狀態。  
- `redo()` 對稱操作。

---

## 4. 函數預期行為 (Expected Behaviour)

### 4.1 資料管理

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `load_transactions()` | 無 | `dict` | 讀取 `DATA_FILE`（JSON），若檔案不存在或格式錯誤回傳空字典。若儲存為 list 則轉為 dict。確保每個交易有 `comment` 欄位。 |
| `save_transactions(transactions_dict)` | `transactions_dict` | `None` | 將字典寫入 `DATA_FILE`，indent=4。 |
| `rebuild_ids(transactions_dict)` | `transactions_dict` | `dict` | 依原 ID 排序，重新指派 ID 為 1..N，回傳新字典。不修改原字典（實際呼叫處會接收回傳值）。 |
| `save_state(transactions_dict)` | `transactions_dict` | `None` | 深拷貝後推入 `undo_stack`，若超過 `MAX_UNDO` 則移除最早狀態；清空 `redo_stack`。 |
| `undo(transactions_dict)` | `transactions_dict` | `dict` | 若 `undo_stack` 非空，將目前狀態推入 `redo_stack`，彈出上個狀態並呼叫 `save_transactions()`，回傳新狀態。 |
| `redo(transactions_dict)` | `transactions_dict` | `dict` | 若 `redo_stack` 非空，將目前狀態推入 `undo_stack`，彈出重做狀態並儲存，回傳新狀態。 |

### 4.2 交易操作（會修改狀態）

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `add_transaction(transactions_dict, description, amount, debit_acc, credit_acc, comment="")` | 同左 | `dict` | 先呼叫 `save_state`；計算新 ID；建立交易條目；加入字典；儲存；印出成功訊息。回傳更新後的字典。 |
| `delete_transaction(transactions_dict, tx_id)` | 同上 | `dict` | 先 `save_state`；若 ID 不存在則警告並回傳原字典；刪除該條目；呼叫 `rebuild_ids` 重新編號；儲存；回傳新字典。 |
| `edit_transaction(transactions_dict, tx_id, field, new_value)` | 同上 | `dict` | 先 `save_state`；若 ID 不存在則警告；依 `field` 修改對應欄位（支援 `description/desc`, `amount`, `dr/debit`, `cr/credit`, `date`, `comment`）；金額需轉 float；儲存；回傳原字典（無重新編號）。 |
| `add_comment(transactions_dict, tx_id, comment_text)` | 同上 | `dict` | 直接呼叫 `edit_transaction` 將 `field="comment"`。 |

### 4.3 查詢與報表（唯讀）

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `list_transactions(transactions_dict, sort_key="date")` | `sort_key` 可為 `"date"` 或 `"amount"` | `None` | 若無交易則提示；轉為 list，依 `sort_key` 排序；使用 `rich.table` 顯示表格，欄位含 ID, Date, Description, Dr, Cr, Amount, Comment（截短）。 |
| `show_balance(transactions_dict)` | 無 | `None` | 計算每個帳戶餘額：Dr 加金額，Cr 減金額；顯示表格，正餘額綠色，負餘額紅色。 |
| `search_transactions(transactions_dict, **filters)` | 關鍵字參數：`min_amount`, `max_amount`, `account`, `keyword`, `from_date`, `to_date` | `None` | 走訪所有交易，逐條件比對；符合者加入結果列表；以表格顯示搜尋結果。若無結果則提示。 |

### 4.4 巨集

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `run_macro(transactions_dict, name, amount)` | `name` 為 `"lunch"`, `"bus"`, `"misc"` | `dict` | 查詢 `MACROS` 字典取得借貸帳戶；呼叫 `add_transaction`，描述為 `f"Macro: {name}"`；回傳更新後的字典。若名稱不存在則警告。 |

### 4.5 週期交易（獨立檔案 `recurring.json`）

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `load_recurring()` | 無 | `list[dict]` | 讀取 `RECUR_FILE`，若不存在或錯誤回傳空列表。 |
| `save_recurring(recur_list)` | `recur_list` | `None` | 寫入 JSON。 |
| `add_recurring(description, amount, debit_acc, credit_acc, interval_days, next_date=None)` | 同上 | `None` | 若未提供 `next_date` 則設為今日；計算新 ID；建立規則條目；加入列表；儲存。 |
| `list_recurring()` | 無 | `None` | 載入規則，以表格顯示 ID, 描述, 金額, 借方, 貸方, 間隔天數, 下次到期日。 |
| `delete_recurring(rule_id)` | `rule_id` | `None` | 載入規則，過濾掉該 ID；若數量不變則警告，否則儲存。 |
| `run_recurring(transactions_dict)` | `transactions_dict` | `dict` | 載入規則；取得今天日期；對每個規則，若 `next_due` ≤ 今天，則呼叫 `add_transaction` 新增一筆交易（描述前綴 `"Recurring: "`，註解標記規則 ID）；更新該規則的 `next_due` += `interval_days`；若有新增則儲存規則；回傳更新後的 `transactions_dict`。 |

### 4.6 預算追蹤（獨立檔案 `budget.json`）

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `load_budgets()` | 無 | `dict` | 讀取 `BUDGET_FILE`，格式 `{account: {"amount": float, "period": str}}`。 |
| `save_budgets(budgets)` | `budgets` | `None` | 寫入 JSON。 |
| `set_budget(account, amount, period="monthly")` | 同上 | `None` | 載入預算字典，設定該帳戶的預算額度與週期；儲存。 |
| `show_budget_report(transactions_dict)` | `transactions_dict` | `None` | 載入預算；計算當月（從本月1日開始）各預算帳戶的實際支出（僅統計 `dr` 為該帳戶的交易）；顯示表格含帳戶、預算、實際、剩餘、狀態；最後顯示總計面板。 |

### 4.7 匯入／匯出

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `export_transactions(transactions_dict, filename)` | `filename` | `None` | 根據副檔名 (`.json` 或 `.csv`) 寫入；CSV 欄位：`id,date,desc,amount,dr,cr,comment`。 |
| `import_transactions(transactions_dict, filename, replace=False)` | `filename`, `replace` | `dict` | 讀取 JSON 或 CSV；轉換型別；若 `replace=True` 則新字典完全取代；否則合併：找出目前最大 ID，對每個匯入交易指派新 ID（max_id+1, max_id+2...），追加到字典；呼叫 `save_state` 後再儲存；回傳新字典。 |

### 4.8 效能測試

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `perf_test_list_vs_dict()` | 無 | `None` | 嘗試載入 `test_data.json`（需預先產生）；分別用 list 和 dict 執行 1000 次隨機查詢與刪除 500 筆後重建；比較時間並顯示表格。 |

### 4.9 輔助

| 函數 | 參數 | 返回值 | 預期行為 |
|------|------|--------|----------|
| `show_help()` | 無 | `None` | 使用 `rich.Panel` 顯示完整的命令列表與範例。 |

---

## 5. 函數間的交互作用

下圖（文字描述）說明重要函數之間的呼叫關係：

```
使用者命令
    │
    ├── add/macro ──► add_transaction
    │                    ├── save_state (push to undo)
    │                    ├── save_transactions
    │                    └── (implicitly returns new dict)
    │
    ├── delete ──► delete_transaction
    │                 ├── save_state
    │                 ├── rebuild_ids
    │                 └── save_transactions
    │
    ├── edit/comment ──► edit_transaction
    │                       ├── save_state
    │                       └── save_transactions
    │
    ├── undo ──► undo
    │               ├── 推入 redo_stack
    │               ├── 彈出 undo_stack
    │               └── save_transactions
    │
    ├── redo ──► redo (對稱)
    │
    ├── recur run ──► run_recurring
    │                     └── 對每個到期規則呼叫 add_transaction
    │
    ├── import ──► import_transactions
    │                   ├── save_state (before modification)
    │                   ├── 合併或取代邏輯
    │                   └── save_transactions
    │
    └── list/balance/search/perftest ──► 唯讀函數，不改變狀態
```

**重要交互點**：
- `add_transaction`、`delete_transaction`、`edit_transaction`、`import_transactions` 都會**先呼叫 `save_state`**，確保可復原。
- `delete_transaction` 會呼叫 `rebuild_ids`，導致 ID 重新編號；而 `edit_transaction` 不重建 ID，保留原編號。
- `run_recurring` 內部會呼叫 `add_transaction`，因此也會觸發 `save_state` 與儲存，且會更新 `recurring.json`。
- `show_budget_report` 依賴 `transactions_dict` 計算當月支出，不會修改任何檔案。
- 匯出不會影響狀態，匯入則會（且會觸發 `save_state`）。

---

## 6. 錯誤處理與邊界條件

- **檔案讀寫**：所有 `load_*` 函數皆以 `try-except` 捕捉 `JSONDecodeError` 與 `FileNotFoundError`，回傳空容器。
- **使用者輸入**：
  - 金額轉換失敗 (`ValueError`) 時印出錯誤訊息，不執行操作。
  - ID 不存在時印出警告，原字典不變。
  - 命令參數數量不足時顯示用法提示。
- **復原堆疊**：當 `undo_stack` 為空時呼叫 `undo` 會提示無操作可復原。
- **週期規則**：若 `next_due` 日期格式錯誤（例如手動編輯 JSON），`datetime.strptime` 會拋出例外，主迴圈會捕捉並顯示錯誤，但不會損壞資料（該規則被跳過）。
- **預算報表**：僅對已設定預算的帳戶計算支出，若無任何預算則提示。

---

## 7. 擴展建議

若欲加入新命令，開發者應：
1. 在 `main()` 的 `if/elif` 鏈中加入新分支。
2. 實作對應的處理函數（若需修改狀態，務必先呼叫 `save_state`）。
3. 更新 `show_help()`。
4. 若涉及新資料結構，考慮獨立 JSON 檔案與對應的 `load_*` / `save_*` 函數。

本架構確保**命令解析與業務邏輯分離**，且透過統一的狀態保存機制達成可靠的復原功能。