# 迷宮生成與路徑規劃視覺化工具 (Maze Algorithm Visualizer)

## Proposal Report

### 動機與目標
筆者對圖論 (Graph) 演算法充滿興趣。我希望透過實作一個視覺化工具，將這些演算法（如 DFS、BFS、Prim's）具象化，觀察它們在處理空間搜尋與生成時的特性差異。目標是建立一個互動式平台，讓使用者能切換不同演算法生成迷宮，並觀察自動尋路機器人（Particle）如何尋找出口。

### 預期功能
* **多種迷宮生成演算法**：支援 Binary Tree、Randomized Prim's 以及 Recursive Backtracking (DFS)。
* **漸進式生成視覺化**：每一幀生成固定數量的儲存格（20 cells/frame），讓過程清晰可見。
* **路徑搜尋動畫**：提供 BFS 與 DFS 兩種尋路模式。
* **動態軌跡紀錄**：即時顯示尋路演算法的走訪範圍（Exploration Trajectory）與最終最短路徑。
* **互動控制**：支援鍵盤切換演算法、重置地圖與啟動求解器。

### 使用技術
* **程式語言**：Python 3.10+
* **圖形函式庫**：Pygame (用於實作視窗、繪製網格與處理輸入事件)
* **開發環境**：VS Code (搭配 Python 擴充功能)
* **版本控制**：GitHub (利用 Release 功能進行階段繳交)

### 時程規劃
* **Week 7**：完成 Proposal Report 並建立基礎 Pygame 視窗架構。
* **Week 8-9**：實作三種迷宮生成演算法之 Generator 邏輯。
* **Week 10-11**：完成 Prototype Report，並實作基礎 BFS 求解器。
* **Week 12-13**：優化視覺化效果（20 cells/frame 限制）與新增 DFS 求解器。
* **Week 14**：除錯、效能優化與錄製 Demo 影片。
* **Week 15**：繳交 Final Report 與 GitHub Release。

### 與課程的關聯
本專題深度結合了「資料結構」與「進階程式設計」的核心概念：
1.  **非線性資料結構 (Graphs)**：將迷宮網格視為圖形節點，牆壁為邊，實作圖形走訪。
2.  **堆疊與遞迴 (Stack & Recursion)**：Recursive Backtracking 演算法本質上是深度優先搜尋 (DFS)，需要利用 Stack 來追蹤回溯路徑。
3.  **佇列 (Queue)**：BFS 求解器利用 Queue 實作層序走訪，以確保找到最短路徑，體現 FIFO 特性。
4.  **隨機演算法與 MST**：Prim's 演算法用於生成最小生成樹 (Minimum Spanning Tree)，在此轉化為隨機化版本以生成自然迷宮。
5.  **進階程式設計技巧**：利用 Python 的 `yield` (Generator) 實作非同步的動畫效果，將演算法邏輯與渲染循環分離。
