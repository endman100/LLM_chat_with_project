# ChatWithProject

ChatWithProject 是一個基於 AI 的程式碼分析工具，透過 XAI 的 Grok API，根據用戶問題自動掃描專案目錄、推測相關檔案，並生成回答。該工具適用於快速分析程式碼結構並解答與專案相關的問題。

## 功能

- **專案結構掃描**：自動掃描指定目錄，提取常見程式檔案（如 `.py`, `.js`, `.java` 等）。
- **檔案推測**：利用 Grok AI 根據用戶問題，推測需要分析的檔案，最多一次請求 10 個檔案。
- **程式碼分析**：讀取檔案內容並結合用戶問題，生成精準回答。
- **結構化輸出**：使用 Pydantic 確保分析結果以 JSON 格式返回，清晰且易於解析。
- **錯誤處理**：檢查檔案是否存在，並在多次重試後仍無效時返回空結果。

## 系統要求

- **作業系統**：Windows（預設），也支援 macOS 和 Linux。
- **Python 版本**：Python 3.8 或以上。
- **依賴套件**：
  - `openai`：用於與 XAI API 交互。
  - `pydantic`：用於結構化資料驗證。
  - `argparse`：用於處理命令列參數。

## 安裝

1. **複製專案**：

   ```bash
   git clone https://github.com/endman100/LLM_chat_with_project.git
   cd LLM_chat_with_project
   ```

2. **安裝依賴套件**：

   ```bash
   pip install openai pydantic
   ```

3. **設置環境變數**： 將您的 XAI API 金鑰設置為環境變數 `XAI_API_KEY`：

   ```bash
   set XAI_API_KEY=您的金鑰
   ```

   或將其加入您的環境變數設定中（如 `.env` 檔案或系統環境變數）。

## 使用方法

1. **運行程式**： 在命令提示字元（CMD）或終端機中，執行以下命令：

   ```bash
   python main.py 您的專案目錄路徑
   ```

   範例：

   ```bash
   python main.py D:\Projects\MyProject
   ```

2. **輸入問題**： 程式會提示您輸入問題，例如：

   ```
   請輸入您的問題：這個專案的主程式入口rekli
   ```

3. **查看結果**： 程式會掃描專案結構、推測相關檔案、讀取內容並生成回答。輸出範例：

   ```
   掃描專案結構中...
   專案結構掃描完成：共 15 個檔案。
   詢問 LLM 推測需要檔案...
   LLM 回應：['main.py', 'utils/helper.py']
   收集檔案內容...
   回答：主程式入口點位於 main.py 的 main() 函數。
   ```

## 檔案結構

```
CodeAnalyzer/
├── code_analyzer.py  # 主程式檔案
├── README.md         # 本說明檔案
└── requirements.txt  # 依賴套件清單
```

## 注意事項

- **API 金鑰**：確保正確設置 `XAI_API_KEY`，否則無法連接到 XAI API。
- **檔案編碼**：程式假設檔案為 UTF-8 編碼，若遇到非 UTF-8 檔案，可能無法正確讀取。
- **檔案數量限制**：每次推測最多請求 10 個檔案，防止過多檔案處理。
- **支援的檔案類型**：目前僅支援 `.py`, `.js`, `.java`, `.cpp`, `.h`, `.cs`, `.go`, `.rb` 檔案。如需支援其他檔案類型，請修改 `get_project_structure` 函數。