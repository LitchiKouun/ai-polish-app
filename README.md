# AI 文章润色助手

基于 Streamlit + DeepSeek 的中文文章润色 Web 应用。左侧逐段展示润色结果，右侧通过对话调整润色风格。

## 功能特点

- 左右分栏布局（60% / 40%），类似编辑器 + AI 助手
- 按段落拆分文章，逐段展示原文、润色版与修改理由
- 支持逐段「接受润色」或「保留原文」
- 右侧多轮对话，根据对话历史重新生成全部段落润色
- 导出最终文章（复制或下载 `.txt`）

## 环境要求

- Python 3.10+
- DeepSeek API Key（[获取地址](https://platform.deepseek.com/)）

## 快速开始

### 1. 创建并激活虚拟环境（推荐）

**Windows (PowerShell):**

```powershell
cd f:\Pyproject\ai-polish-app
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

若激活时报「无法加载脚本」错误，可先执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux / macOS:**

```bash
cd ai-polish-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置 API Key

**Windows (PowerShell):**

```powershell
$env:DEEPSEEK_API_KEY = "your-api-key-here"
```

**Linux / macOS:**

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

### 3. 启动应用

确保虚拟环境已激活，然后运行：

```bash
streamlit run app.py
```

浏览器将自动打开 `http://localhost:8501`。

## 使用说明

1. 在左侧文本框粘贴文章（段落之间用空行分隔）
2. 点击 **开始润色**，等待 AI 生成各段润色建议
3. 对每段点击 **接受润色** 或 **保留原文**
4. 在右侧输入额外要求（如「改为学术风格」），点击 **发送** 重新润色
5. 完成后点击 **导出最终文章**，复制或下载结果

## 项目结构

```
ai-polish-app/
├── app.py               # Streamlit 主应用
├── utils.py             # 文本分段、合并等工具函数
├── deepseek_client.py   # DeepSeek API 调用封装
├── prompts.py           # System prompt 及消息构建
├── requirements.txt     # 项目依赖
└── README.md            # 运行说明
```

## 注意事项

- 首次润色及每次右侧发送消息都会调用 DeepSeek API，请注意用量
- 请确保网络可访问 `https://api.deepseek.com`
- 对话历史与段落选择在会话期间保留，刷新页面将重置
