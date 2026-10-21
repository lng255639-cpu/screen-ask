# screen-ask：螢幕框選問答

在螢幕上框出一塊區域，Claude 會辨識裡面的文字，並回答其中的問題，例如考題、選擇題、計算題、錯誤訊息或外文段落。

有兩種用法：

| 用法 | 怎麼啟動 | 適合 |
|------|----------|------|
| Claude Code skill | 對話中輸入 `/screen-ask` | 已經開著 Claude Code，順手問一題 |
| 背景熱鍵版 | 執行 `screen_ask.py` 後按 `Ctrl+Alt+Q` | 不開 Claude Code，隨時框選隨時問 |

## 需求

- **Windows 10 / 11**（截圖、熱鍵、DPI 處理用到 Windows API，Mac / Linux 不支援）
- **Python 3.8 以上**，並安裝 Pillow（tkinter 是 Python 內建的）
- 下面兩者擇一：
  - **[Claude Code](https://claude.com/claude-code)**，已安裝並登入（使用既有訂閱，不另外收費）
  - **Anthropic API key**：設定環境變數 `ANTHROPIC_API_KEY`，並安裝 `anthropic` 套件（依 API 用量計費，回答速度較快）

## 安裝

1. 安裝 Pillow：

   ```bash
   pip install pillow
   ```

   如果要走 API，再加裝：

   ```bash
   pip install anthropic
   ```

2. 把這個 repo clone 到 Claude Code 的 skills 資料夾：

   ```bash
   git clone https://github.com/lng255639-cpu/screen-ask.git "%USERPROFILE%\.claude\skills\screen-ask"
   ```

   沒有 git 的話，也可以在 GitHub 頁面按 **Code → Download ZIP**，解壓縮後把資料夾改名為 `screen-ask`，放到 `%USERPROFILE%\.claude\skills\` 底下。

3. 測試截圖功能：

   ```bash
   python "%USERPROFILE%\.claude\skills\screen-ask\scripts\snip.py"
   ```

   畫面會變暗並凍結。拖曳框選一塊區域，終端機印出 PNG 檔案路徑就代表安裝成功。

## 用法一：在 Claude Code 裡使用

1. 在 Claude Code 對話中輸入 `/screen-ask`，或直接說「框選螢幕問問題」。
2. 3 秒後畫面會凍結，請在這段時間內先切到要問的視窗。
3. 用滑鼠拖曳框出要辨識的區域。按 `Esc` 或滑鼠右鍵可以取消。
4. Claude 會先列出「辨識文字」，再逐題「回答」：
   - 選擇題：給出答案和簡短理由
   - 計算題：列出算式
   - 錯誤訊息：說明原因和修法
   - 沒有問題：整理重點摘要或翻譯

觸發時可以附上你的問題，例如「`/screen-ask` 這段翻成中文」，Claude 會照你的問題回答。

## 用法二：背景熱鍵版

啟動（用 `pythonw` 不會多開一個黑色視窗）：

```bash
pythonw "%USERPROFILE%\.claude\skills\screen-ask\scripts\screen_ask.py"
```

啟動後，右上角會短暫顯示「螢幕問答已啟動」。

1. 在任何畫面按 `Ctrl+Alt+Q`
2. 拖曳框選區域（`Esc` 或右鍵取消）
3. 右上角跳出答案視窗，先顯示「Claude 思考中…」，完成後換成答案

答案視窗的按鈕：

| 按鈕 | 作用 |
|------|------|
| 複製 | 把答案複製到剪貼簿 |
| 再框一次 | 重新框選（答案視窗會暫時隱藏，不會被截進去） |
| 關閉 | 關閉這個答案視窗（`Esc` 也可以） |
| 結束程式 | 關掉整個背景程式 |

### 參數

| 參數 | 說明 | 範例 |
|------|------|------|
| `--key` | 換熱鍵字母（固定搭配 `Ctrl+Alt`） | `--key W` → `Ctrl+Alt+W` |
| `--model` | 指定模型 | `--model sonnet`、`--model opus` |
| `--prompt` | 自訂送給 Claude 的指令 | `--prompt "把圖中文字翻成英文"` |

### 回答速度

- 沒設定 `ANTHROPIC_API_KEY`：呼叫 `claude -p`，每題約 10 到 20 秒（大部分時間花在啟動 Claude Code）
- 有設定 `ANTHROPIC_API_KEY`：直接呼叫 API，通常幾秒內完成

### 開機自動啟動

1. 按 `Win+R`，輸入 `shell:startup`，按 Enter
2. 在開啟的資料夾裡按右鍵 → **新增 → 捷徑**
3. 項目位置填入：

   ```
   pythonw "%USERPROFILE%\.claude\skills\screen-ask\scripts\screen_ask.py"
   ```

4. 名稱隨意，例如「螢幕問答」

## 單獨使用截圖工具

`snip.py` 也可以單獨使用，只截圖不問 Claude：

```bash
python snip.py                     # 存到 %TEMP%\screen-ask\snip_時間.png
python snip.py --out D:\shot.png   # 指定存檔位置
python snip.py --delay 3           # 等 3 秒再凍結畫面
```

框選成功時，最後一行輸出圖片路徑。取消時 exit code 為 1。

## 疑難排解

| 狀況 | 解法 |
|------|------|
| 啟動時跳出「熱鍵已被占用」 | 程式已經在背景執行，或其他軟體用了 `Ctrl+Alt+Q`。用 `--key` 換一個字母，或在工作管理員結束 `pythonw.exe` |
| 答案顯示「找不到 claude 指令」 | 沒裝 Claude Code，或 `claude` 不在 PATH。安裝並登入 Claude Code，或改設 `ANTHROPIC_API_KEY` |
| 框選位置和實際截到的範圍對不上 | 回報你的螢幕配置（幾個螢幕、各自的縮放比例） |
| 文字太小辨識錯 | 框選時範圍抓緊一點，或先把畫面放大再框 |

## 檔案說明

```
screen-ask/
├── SKILL.md              # Claude Code skill 定義（/screen-ask）
├── README.md             # 本說明
└── scripts/
    ├── snip.py           # 全螢幕凍結 + 拖曳框選 + 存 PNG
    └── screen_ask.py     # 背景熱鍵版（Ctrl+Alt+Q）
```

## 隱私

框選的圖片會暫存在 `%TEMP%\screen-ask\`，並傳給 Claude 辨識。請避免框選密碼、個資等敏感內容。暫存圖片不會自動刪除，需要時可以手動清除該資料夾。
