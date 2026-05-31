# LedgerLogic CLI – 雙式記帳系統

## Proposal Report

### 動機與目標
許多自由工作者、小型商家或個人需要一套**可稽核、符合會計原則**的記帳工具，但市面上的試算表或手機 App 多為單式記帳，無法確保借貸平衡。  
對於開發者而言，一個命令列介面（CLI）的記帳工具能提供快速、鍵盤為中心的操作體驗，不必離開終端機就能管理收支。

本專案的目標是開發一個**命令列雙式記帳系統**，同時作為資料結構效能的實驗平台。使用者能快速記錄交易、使用巨集減少重複輸入，並透過**匯入／匯出**、**自動儲存**確保資料安全。額外實作**復原／重做**與**預算追蹤**，使工具具備基礎的個人財務管理能力。

### 競品比較

| 產品／系統 | 雙式記帳 | CLI 操作 | 內建巨集 | 預算追蹤 | 復原/重做 | 匯入/匯出 | 自動儲存 | 學習曲線 |
|-----------|---------|---------|---------|---------|----------|----------|----------|----------|
| **本專案** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (JSON/CSV) | ✅ | 低 |
| ledger (CLI) | ✅ | ✅ | ❌ (需腳本) | ❌ | ❌ | ✅ (text) | ❌ | 高 |
| hledger | ✅ | ✅ | ❌ | ✅ (基本) | ❌ | ✅ (多格式) | ❌ | 中高 |
| 傳統會計軟體 (ERP) | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | 高 |
| Excel / App | ❌ (單式) | ❌ | ❌ | ❌ | ❌ | ✅ (手動) | ❌ | 低 |

**本專案優勢**：整合多項進階功能於單一輕量 CLI，適合教學、個人記帳與資料結構效能實驗，且程式碼精簡易修改。

### 預期功能
- ✅ 新增交易（借方、貸方、金額、說明、註解）
- ✅ 簡化命令（`misc <amount>` 自動記為 Miscellaneous ↔ Cash）
- ✅ 巨集（午餐、公車、雜支）
- ✅ 查看交易列表（依日期或金額排序）
- ✅ 帳戶餘額報表
- ✅ 刪除交易（自動重新編號）
- ✅ 編輯交易（修改任何欄位）
- ✅ 加入／編輯註解
- ✅ 復原／重做（最多 20 層）
- ✅ 預算追蹤（每月預算 vs 實際支出）
- ✅ 搜尋交易（關鍵字、金額區間、帳戶）
- ✅ 匯出／匯入 JSON / CSV（合併或取代）
- ✅ 效能測試（比較 list 與 dict 操作速度，含記憶體用量）
- ✅ 自動儲存（每次變更即寫入檔案）
- ✅ 事件迴圈命令列介面（help, exit）

### 使用技術
- **語言**：Python 3  
- **資料儲存**：JSON 檔案（交易日誌 `ledger_dict.json`、預算 `budget.json`）  
- **命令列介面**：原生 `input()` 事件迴圈  
- **表格顯示**：`rich` 套件（`rich.table`, `rich.panel`, `rich.console`）  
- **匯入／匯出**：Python 內建 `json` 與 `csv` 模組  
- **日期處理**：`datetime`, `timedelta`  
- **效能測試**：自訂 `perftest` 指令，比較 list (O(n)) vs dict (O(1) 平均)，並使用 `tracemalloc` 記錄記憶體峰值  
- **深拷貝**：`copy.deepcopy` 實現狀態保存，支援復原／重做

### Prototype 預計可驗證內容
1. 能否正確儲存與呈現雙式會計交易（借貸平衡）？
2. 巨集是否有效減少重複輸入？
3. 復原／重做是否正確還原前後狀態？
4. 預算追蹤是否準確計算當月支出並與預算比較？
5. 匯出後的 JSON/CSV 能否完整匯入（含註解）而不遺失資料？
6. 使用 dict 儲存時，刪除與查詢操作是否明顯比 list 版本快？（透過 `perftest` 驗證）
7. 事件迴圈是否能流暢處理多詞參數指令（如 `budget set`）？

---

## Prototype Report

### 目前進度
已完成完整可運作的**事件迴圈雙式記帳 CLI**，核心功能如下：

- ✅ **交易管理**：`add`, `list`, `balance`, `delete`, `edit`, `comment`  
- ✅ **簡化命令**：`misc <amount>` 直接記為 Miscellaneous ↔ Cash  
- ✅ **巨集系統**：內建 `lunch` (Food↔Cash)、`bus` (Transport↔EasyCard)  
- ✅ **復原／重做**：每項修改操作前自動推入堆疊，支援 20 層歷史  
- ✅ **預算追蹤**：`budget set/show`，比較當月實際支出與預算  
- ✅ **搜尋**：關鍵字搜尋或互動式多條件篩選  
- ✅ **匯入／匯出**：支援 JSON 與 CSV，可合併或取代  
- ✅ **效能測試**：`perftest` 指令自動產生 10,000 筆測試資料，比較 list 與 dict 在隨機查詢及刪除後重建的執行時間與記憶體用量  
- ✅ **自動儲存**：所有寫入操作立即存檔  
- ✅ **美觀報表**：使用 `rich` 顯示彩色表格，餘額正負以綠／紅標示  
- ✅ **資料完整性**：刪除交易後自動重新編號 ID，匯入時處理型別轉換  

**程式碼結構**：單一檔案約 550 行，包含資料管理、核心功能、巨集、預算、匯出入、效能測試與主迴圈。

### 遇到的困難
1. **CSV 匯入的型別問題**  
   - 問題：CSV 讀取時所有欄位皆為字串，導致金額與 ID 無法計算及排序。  
   - 解決：在 `import_transactions` 中明確將 `id` 轉為 `int`、`amount` 轉為 `float`，並確保 `comment` 欄位存在。

2. **重新編號與復原堆疊的互動**  
   - 問題：刪除交易後重新編號，若使用者復原，舊 ID 會與目前狀態衝突。  
   - 解決：復原／重做時直接覆蓋整個 transactions dict，不依賴 ID 連續性；ID 重整僅在刪除後立即執行，復原時會還原完整的 dict（含原來的 ID）。

3. **預算計算的帳戶範圍**  
   - 問題：所有借方帳戶都會被計入支出，但收入帳戶（如薪資）不應納入預算消耗。  
   - 解決：`budget show` 僅對已經設定預算的帳戶進行統計，未設定預算的借方帳戶忽略。

4. **大量測試資料產生與效能比較的再現性**  
   - 問題：測試資料需隨機但可重複，否則 `perftest` 結果難以比較。  
   - 解決：內建 `gen_transactions()` 可產生測試資料，未來可加入固定隨機種子確保重現性。

### 下一步計畫
- 短期（Final 之前）：
  - 為 `perftest` 加入固定隨機種子，確保測試可重現。
  - 撰寫簡單的單元測試（使用 `unittest`）驗證核心功能。
- 長期（課程結束後擴充）：
  - 圖形化報表（`matplotlib` 支出圓餅圖）
  - 支援週期性交易（recurring）
  - 多使用者／多帳本（切換不同 JSON 檔案）
  - 資料庫後端（SQLite）

---

## Final Report

### 專案說明

本專案實作了一個完整的命令列雙式記帳系統 – **LedgerLogic CLI 2.0**。使用者可以透過終端機快速記錄借貸交易、管理預算、使用巨集減少重複輸入，並支援跨工作階段的復原／重做、匯入／匯出、進階搜尋與自動儲存。

與原始提案和雛型相比，最終版本超越了預期目標：

| 功能 | 提案 | 雛型 | 最終實作 |
|------|------|------|----------|
| 雙式記帳 | ✅ | ✅ | ✅ |
| 交易增刪改查 | ✅ | ✅ | ✅ |
| 分類標籤（註解） | ✅ | ✅ | ✅ |
| 持久化儲存 (JSON) | ✅ | ✅ | ✅ |
| 匯出／匯入 CSV/JSON | ✅ | ✅ | ✅ + 錯誤處理 |
| 依日期／金額排序 | ✅ | ✅ | ✅ |
| 每月收支摘要 | ❌ | ❌ | ✅（預算報告） |
| 復原／重做 | ❌ | ✅ (記憶體) | ✅ 跨工作階段（指令日誌） |
| 巨集（可編輯） | ❌ | ✅ (內建) | ✅ 可動態增刪改查，永久儲存 |
| 預算追蹤 | ❌ | ✅ (每月) | ✅ 支援週／月／年 |
| 互動式 REPL | ❌ | ✅ | ✅ 不因參數錯誤而中斷 |
| 非互動式單行指令 | ❌ | ❌ | ✅ |
| 進階搜尋（多條件） | ❌ | ❌ | ✅ |
| 拼字錯誤建議 | ✅ (野心目標) | ❌ | ✅ (Levenshtein) |
| 指令參數錯誤處理 | ❌ | ❌ | ✅ (提示並重新輸入) |
| 完整單元測試 | ❌ | ❌ | ✅ 40+ 測試 |
| 自動化展示腳本 | ❌ | ❌ | ✅ |
| 打包成 EXE | ✅ | ❌ | ✅ (PyInstaller) |

**核心架構亮點：**

1. **指令模式 (Command Pattern)** – 每一筆修改封裝成指令物件，寫入 `journal.json`。復原／重做不僅限於記憶體，程式重啟後仍可還原先前操作。
2. **檢查點機制 (Checkpointing)** – 每 50 個指令自動儲存完整狀態至 `ledger_dict.json`，並清空日誌，兼顧效能與資料安全。
3. **可編輯巨集** – 儲存於 `macros.json`，使用者可隨時新增、移除、列出、執行巨集，無須修改程式碼。
4. **預算追蹤** – 支援 `weekly` / `monthly` / `yearly` 週期，報告當月實際支出與預算差異。
5. **拼字錯誤偵測** – 使用 `difflib.get_close_matches()` 計算編輯距離，在互動模式與單行模式中提供「是否是指 'add'？」等建議。
6. **參數錯誤不中斷** – 互動模式下，若輸入錯誤的旗標（如 `--amoun`）或缺少必要參數，程式會印出錯誤訊息並重新回到提示號，不會意外結束。
7. **匯出錯誤處理** – 當匯出時未指定檔名、副檔名錯誤或給予過多參數時，會給予清楚提示，不會崩潰。
8. **完整測試涵蓋** – 使用 `pytest` 編寫 40+ 個單元與整合測試，涵蓋核心邏輯、CLI 解析、錯誤處理、Windows 編碼相容性及邊界條件。
9. **跨平台相容** – 設定環境變數 `PYTHONIOENCODING=utf-8`、`TERM=dumb` 等，避開 Windows `cp950` 的 Unicode 錯誤。

### 使用方式

#### 環境需求
- Python 3.9 或以上
- 安裝 `rich` 套件：`pip install rich`
- （選擇性）安裝 `pytest` 以執行測試

#### 執行模式

您可以選擇以下三種方式之一執行 LedgerLogic：

| 方式 | 適用對象 | 說明 |
|------|----------|------|
| 🐍 Python 原始碼 | 開發者、有 Python 環境者 | 執行 `python ledger.py`，需先安裝 `rich` |
| 📦 獨立執行檔 (.exe) | 一般使用者 | 下載 `ledger.exe`，直接雙擊或於 cmd 執行 |
| 🧪 測試與腳本 | 驗證功能、自動化 | 使用 `test.bat` 或 `demo_extended.py` |

**1. 互動模式（REPL）**  
```bash
python ledger.py
```
出現 `>>` 提示號後，直接輸入指令（不加 `ledger` 前綴），例如：
```
>> add --desc "咖啡" --amount 3.5 --dr 飲食 --cr 現金
>> list
>> budget set 飲食 500 --period monthly
>> budget show
>> undo
>> q
```
互動模式下，即使輸入錯誤參數（如 `add --desk ...`）程式也不會退出，只會顯示錯誤並重新提示。

**2. 單行指令模式**  
```bash
python ledger.py add --desc "午餐" --amount 12 --dr 飲食 --cr 現金
python ledger.py list --sort amount
python ledger.py balance
```

#### 主要指令一覽

| 指令 | 說明 | 範例 |
|------|------|------|
| `add --desc ... --amount ... --dr ... --cr ...` | 新增交易 | `add --desc "咖啡" --amount 3.5 --dr 飲食 --cr 現金` |
| `list [--sort date\|amount]` | 列出交易 | `list --sort amount` |
| `balance [--date ...]` | 帳戶餘額 | `balance --date "2025-01-01 00:00:00"` |
| `search --keyword ... --min-amount ...` | 多條件搜尋 | `search --keyword 咖啡 --min-amount 2` |
| `edit <id> <field> <new>` | 編輯交易 | `edit 3 amount 49.99` |
| `delete <id>` | 刪除交易 | `delete 5` |
| `undo` / `redo` | 復原／重做 | `undo` |
| `macro add <name> --dr ... --cr ...` | 新增巨集 | `macro add uber --dr 交通 --cr 現金` |
| `macro run <name> <amount>` | 執行巨集 | `macro run uber 15.5` |
| `budget set <帳戶> <金額> [--period ...]` | 設定預算 | `budget set 飲食 500 --period monthly` |
| `budget show` | 顯示預算報告 | `budget show` |
| `export <檔名>` | 匯出資料 (JSON/CSV) | `export backup.json` |
| `import <檔名> [--replace]` | 匯入資料 | `import data.csv --replace` |
| `benchmark [--num N]` | 效能比較（list vs dict） | `benchmark --num 5000` |
| `rebuild-ids` | 重新編號交易 ID | `rebuild-ids` |

#### 獨立執行檔 (Standalone Executable)

若您不想安裝 Python 或設定任何環境，可以直接下載預先打包好的 **`ledger.exe`** 執行檔。

- **下載位置**：本專案的 [GitHub Releases](https://github.com/yourusername/LedgerLogic/releases) 頁面（請替換為實際網址）
- **檔案大小**：約 **50 MB**（因內含 Python 直譯器、`rich` 顯示套件及所有依賴，且採用 `--onefile` 模式打包）
- **為何檔案較大？**  
  PyInstaller 將 Python 執行環境與所有函式庫打包成單一檔案，雖然體積較大，但使用者無需安裝任何額外軟體，雙擊或於命令列即可執行。若需更小的檔案，可使用虛擬環境或 Nuitka 重新打包。
- **使用方式**：
  1. 下載 `ledger.exe` 至任一資料夾。
  2. 開啟命令提示字元 (cmd)，切換到該資料夾。
  3. 執行單行指令，例如：
     ```cmd
     ledger.exe add --desc "咖啡" --amount 3.5 --dr 飲食 --cr 現金
     ```
  4. 或直接執行 `ledger.exe` 進入互動模式 (REPL)，輸入指令後按 Enter，輸入 `q` 離開。
- **注意事項**：
  - 執行檔為 Windows 版本（64 位元）。若需其他平台，請自行使用 `wrap_to_exe.bat` 打包。
  - 首次執行可能被防毒軟體誤判（因 PyInstaller 打包特性），請加入排除清單。
  - 所有資料檔案（`ledger_dict.json` 等）會產生在 **執行檔所在的同一資料夾**。

#### 輔助腳本與檔案說明

為方便使用者快速上手，專案內附帶了以下輔助檔案：

| 檔案 | 用途 | 使用方式 |
|------|------|----------|
| `setup.bat` | 自動檢查 Python 環境、更新 pip、安裝必要套件（rich, pytest, pyinstaller）。 | 雙擊執行，完成一次即可。 |
| `start.bat` | 直接啟動互動式記帳程式（無需手動輸入 `python ledger.py`）。 | 雙擊即可進入 `>> ` 提示號。 |
| `test.bat` | 執行全部測試（等同 `pytest -v`），並在結束後暫停，方便觀看結果。 | 雙擊執行，所有測試通過即顯示綠色。 |
| `wrap_to_exe.bat` | 自動安裝 PyInstaller 並將 `ledger.py` 打包成單一 `ledger.exe` 執行檔。 | 雙擊執行，完成後 `dist/ledger.exe` 即可獨立使用。 |
| `test.json` | 範例交易資料檔案，可用於匯入測試（例如 `import test.json --replace`）。 | 僅供測試，可自由修改。 |

> 💡 **建議流程**：
> 1. 下載專案後，先執行 `setup.bat` 安裝依賴。
> 2. 執行 `start.bat` 體驗互動式記帳。
> 3. 執行 `test.bat` 驗證程式正確性。
> 4. （選擇性）執行 `wrap_to_exe.bat` 打包成 `.exe` 以便分享。

#### 示範自動化腳本

提供 `demo_extended.py`，執行後會自動演示所有主要功能（新增、列表、預算、巨集、復原/重做、搜尋、匯出），並展示拼字錯誤建議。執行方式：
```bash
python demo_extended.py
```

#### 執行測試

```bash
pip install pytest
pytest -v
```
預期所有 40+ 個測試皆通過。

#### 打包成單一執行檔 (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --name ledger ledger.py
```
產生的 `ledger.exe` 可獨立執行，無須安裝 Python。

#### 資料檔案說明

| 檔案 | 用途 |
|------|------|
| `ledger_dict.json` | 主要交易資料庫（檢查點） |
| `journal.json` | 指令日誌（用於復原／重做） |
| `macros.json` | 使用者自訂巨集（永久儲存） |
| `budget.json` | 預算設定 |

所有檔案皆為純文字 JSON，可手動備份或轉移到其他裝置。

