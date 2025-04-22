import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Dict
import argparse

# 設置 OpenAI API 客戶端
xai_api_key = os.getenv("XAI_API_KEY")
base_url = "https://api.x.ai/v1"
client = OpenAI(
    api_key=xai_api_key,
    base_url=base_url,
)

# Pydantic 模型定義
class FileAnalysisOutput(BaseModel):
    files: List[str]

def get_user_question():
    """接收用戶詢問"""
    return input("請輸入您的問題：")

def get_project_structure(directory):
    """掃描專案目錄並返回結構資訊"""
    structure = []
    for root, _, files in os.walk(directory):
        for file in files:
            # 僅包含常見的程式檔案類型
            if file.endswith(('.py', '.js', '.java', '.cpp', '.h', '.cs', '.go', '.rb')):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                structure.append(relative_path)
    return structure

def analyze_and_guess_files(question, project_structure, files_content: Dict[str, str] = None, project_dir=None):
    """使用 LLM 推測相關檔案或分析現有檔案是否足夠，結構化輸出"""
    structure_text = "\n".join(project_structure)
    content_text = ""
    processed_files = list(files_content.keys()) if files_content else []
    processed_files_text = "\n".join(processed_files) if processed_files else "無"

    # 格式化檔案內容
    for file, content in files_content.items():
        content_text += f"\n--- {file} ---\n{content}"

    # 定義結構化輸出格式
    output_format = """
    返回一個 JSON 物件，格式如下：
    {
        "files": string[]      // 列出需要的檔案路徑；否則為空陣列
    }
    """

    prompt = [
        f"所有專案檔案路徑：\n{structure_text}\n",
        f"已收集的檔案：\n{processed_files_text}\n",
        f"以下是程式檔案的內容：\n{content_text}\n\n" if files_content else "",
        f"目標問題：{question}",
        f"{output_format}",
        f"這些內容是否足夠回答問題？如果不足夠，請僅從 '所有專案檔案路徑' 中選擇還需要的檔案路徑，一次最多請求十個檔案，請猜測與問題最有相關性的檔案，並確保不包含 '已收集的檔案'。返回結構化 JSON 格式的結果。",
    ]
    prompt = "\n".join(prompt)

    messages = [
        {"role": "system", "content": "你是一個程式碼分析助手，根據專案結構和問題推測相關檔案，或檢查檔案內容是否足以回答問題。返回結構化 JSON 結果，包含是否足夠和檔案路徑列表。請確保只從提供的專案檔案路徑中選擇檔案，且不返回已收集的檔案。"},
        {"role": "user", "content": prompt}
    ]

    # 內部迴圈：重試直到檔案有效或達到最大重試次數
    max_retries = 3
    for attempt in range(max_retries):
        response = client.beta.chat.completions.parse(
            model="grok-3-mini-beta",
            messages=messages,
            response_format=FileAnalysisOutput,
        )
        parsed = response.choices[0].message.parsed

        # 檢查檔案是否存在
        exists, error_messages = check_file_existence(project_dir, parsed.files)
        if exists:
            return parsed.files

        # 如果檔案不存在，將錯誤訊息添加到 messages
        error_messages_string = "\n".join(error_messages)
        error_prompt = f"以下檔案路徑無效：\n{error_messages_string}\n請重新生成結果，確保檔案路徑僅從 '所有專案檔案路徑' 中選擇，且不包含已收集的檔案。"
        messages.append({"role": "user", "content": error_prompt})
        print(f"重試 {attempt + 1}/{max_retries}：LLM 返回無效檔案路徑，重新生成...")

    # 如果重試失敗，返回 sufficient=False 和空檔案列表
    print("警告：多次重試後仍無法生成有效檔案路徑，返回空結果。")
    return False, []

def read_file(file_path):
    """讀取檔案內容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        print(f"無法以 UTF-8 編碼讀取檔案 {file_path}，請檢查檔案格式。")
        return ""

def generate_answer(files_content: Dict[str, str], question):
    """使用 LLM 生成回答"""
    content_text = ""
    for file, content in files_content.items():
        content_text += f"\n--- {file} ---\n{content}"

    messages = [
        {"role": "system", "content": "你是一個程式碼分析助手，根據檔案內容回答用戶問題。"},
        {"role": "user", "content": f"根據以下程式檔案的內容：\n{content_text}\n\n回答問題：{question}"}
    ]
    response = client.chat.completions.create(
        model="grok-3-mini-beta",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content.strip()

def check_file_existence(project_dir, files):
    """檢查檔案是否存在"""
    error_messages = []
    if(len(files) > 10):
        error_messages.append("請求的檔案數量超過限制（10個）。")

    for file in files:
        file_path = os.path.join(project_dir, file)
        if not os.path.exists(file_path):
            error_messages.append(f"檔案 {file} 不存在。")
    if error_messages:
        return False, error_messages
    return True, []

def main(project_dir):
    question = get_user_question()
    # 獲取專案結構
    print("掃描專案結構中...")
    project_structure = get_project_structure(project_dir)
    print(f"專案結構掃描完成： 共 {len(project_structure)} 個檔案。")

    files_content = {}  # 使用 dict 儲存檔案內容
    files = []
    max_iterations = 10  # 限制反覆次數

    for _ in range(max_iterations):
        print("詢問 LLM 推測需要檔案...")
        files = analyze_and_guess_files(question, project_structure, files_content, project_dir)
        print("LLM 回應：", files)
        if len(files) == 0:
            break

        print("收集檔案內容...")
        for file in files:
            if file not in files_content:  # 避免重複收集
                file_path = os.path.join(project_dir, file)
                content = read_file(file_path)
                if content:
                    files_content[file] = content
    else:
        print("無法收集足夠的信息來回答問題。")

    if files_content:
        answer = generate_answer(files_content, question)
        print("回答：", answer)
    else:
        print("沒有可用的檔案內容來生成回答。")

if __name__ == "__main__":
    # 使用 argparse 解析命令行參數
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_dir", type=str, help="專案目錄路徑")
    args = parser.parse_args()
    print(f"目標分析專案目錄路徑：{args.project_dir}")

    # 專案目錄路徑
    # project_dir = r'D:\AIGC\AICGCode\AICGCode\SymbolCopy'
    project_dir = args.project_dir
    main(project_dir)