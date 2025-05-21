# 数字人自动问卷填写系统

这是一个高级自动化系统，能够使用AI驱动的数字人自动填写在线问卷。系统从数据库获取数字人详细信息，生成优化的提示词，然后指导AI代理按照数字人的身份特征填写问卷。

## 主要特点

- **数据库集成**：从MySQL数据库获取完整的数字人信息
- **智能提示词生成**：自动整合数字人属性生成结构化提示词
- **高级元素定位策略**：优先使用文本内容而非索引定位元素
- **完整的任务指南**：包括滚动策略、错误处理和交互方法
- **可配置的模型参数**：支持调整模型、温度等参数

## 使用方法

```bash
# 基本用法 - 使用ID为12的数字人填写问卷
python testWenjuanFinal.py 12

# 指定不同的问卷URL
python testWenjuanFinal.py 12 --url "https://www.example-survey.com/survey"

# 调整模型参数
python testWenjuanFinal.py 12 --model "gemini-2.0-pro" --temperature 0.7

# 自动关闭浏览器
python testWenjuanFinal.py 12 --auto-close

# 仅显示提示词，不执行任务
python testWenjuanFinal.py 12 --show-prompt

# 查看所有数字人列表
python testWenjuanFinal.py --list

# 测试数据库连接
python testWenjuanFinal.py --test-db
```

## 可调整参数

| 参数 | 描述 | 默认值 |
|------|------|-------|
| `--url` | 要访问的问卷URL | https://wjx.cn/vm/w4e8hc9.aspx |
| `--api-key` | Gemini API密钥 | AIzaSyAfmaTObVEiq6R_c62T4jeEpyf6yp4WCP8 |
| `--model` | 使用的Gemini模型 | gemini-2.0-flash |
| `--temperature` | 模型温度参数 (0-1) | 0.5 |
| `--auto-close` | 任务完成后自动关闭浏览器 | False |
| `--show-prompt` | 只显示提示词，不执行任务 | False |

## 温度参数影响

temperature参数控制模型的创造性和随机性：

- **低温度** (0.1-0.4): 更确定、可预测的响应，适合严格遵循指示的场景
- **中等温度** (0.5-0.7): 平衡创造性和一致性，适合大多数问卷填写任务
- **高温度** (0.8-1.0): 更具创造性和多样性的回答，适合需要个性化回答的场景

## 提示词结构

系统生成的提示词由三个主要部分组成：

1. **人物描述**：从数据库获取的数字人详细信息，包括基本信息和属性
2. **URL指示**：要访问的问卷地址
3. **任务指导**：详细的作答要求和技术指导，包括元素定位策略

## 数据库配置

系统连接到MySQL数据库获取数字人信息：

- **服务器**: 192.168.50.137:3306
- **用户名**: root
- **密码**: 123456
- **数据库**: wenjuan
- **主表**: digital_humans

<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>

[![GitHub stars](https://img.shields.io/github/stars/browser-use/web-ui?style=social)](https://github.com/browser-use/web-ui/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![WarmShao](https://img.shields.io/twitter/follow/warmshao?style=social)](https://x.com/warmshao)

This project builds upon the foundation of the [browser-use](https://github.com/browser-use/browser-use), which is designed to make websites accessible for AI agents.

We would like to officially thank [WarmShao](https://github.com/warmshao) for his contribution to this project.

**WebUI:** is built on Gradio and supports most of `browser-use` functionalities. This UI is designed to be user-friendly and enables easy interaction with the browser agent.

**Expanded LLM Support:** We've integrated support for various Large Language Models (LLMs), including: Google, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama etc. And we plan to add support for even more models in the future.

**Custom Browser Support:** You can use your own browser with our tool, eliminating the need to re-login to sites or deal with other authentication challenges. This feature also supports high-definition screen recording.

**Persistent Browser Sessions:** You can choose to keep the browser window open between AI tasks, allowing you to see the complete history and state of AI interactions.

<video src="https://github.com/user-attachments/assets/56bc7080-f2e3-4367-af22-6bf2245ff6cb" controls="controls">Your browser does not support playing this video!</video>

## Installation Guide

### Option 1: Local Installation

Read the [quickstart guide](https://docs.browser-use.com/quickstart#prepare-the-environment) or follow the steps below to get started.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Set Up Python Environment
We recommend using [uv](https://docs.astral.sh/uv/) for managing the Python environment.

Using uv (recommended):
```bash
uv venv --python 3.11
```

Activate the virtual environment:
- Windows (Command Prompt):
```cmd
.venv\Scripts\activate
```
- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

#### Step 3: Install Dependencies
Install Python packages:
```bash
uv pip install -r requirements.txt
```

Install Browsers in playwright. 
```bash
playwright install --with-deps
```
Or you can install specific browsers by running:
```bash
playwright install chromium --with-deps
```

#### Step 4: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 5: Enjoy the web-ui
1.  **Run the WebUI:**
    ```bash
    python webui.py --ip 127.0.0.1 --port 7788
    ```
2. **Access the WebUI:** Open your web browser and navigate to `http://127.0.0.1:7788`.
3. **Using Your Own Browser(Optional):**
    - Set `BROWSER_PATH` to the executable path of your browser and `BROWSER_USER_DATA` to the user data directory of your browser. Leave `BROWSER_USER_DATA` empty if you want to use local user data.
      - Windows
        ```env
         BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
         BROWSER_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"
        ```
        > Note: Replace `YourUsername` with your actual Windows username for Windows systems.
      - Mac
        ```env
         BROWSER_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
         BROWSER_USER_DATA="/Users/YourUsername/Library/Application Support/Google/Chrome"
        ```
    - Close all Chrome windows
    - Open the WebUI in a non-Chrome browser, such as Firefox or Edge. This is important because the persistent browser context will use the Chrome data when running the agent.
    - Check the "Use Own Browser" option within the Browser Settings.

### Option 2: Docker Installation

#### Prerequisites
- Docker and Docker Compose installed
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (For Windows/macOS)
  - [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) (For Linux)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 3: Docker Build and Run
```bash
docker compose up --build
```
For ARM64 systems (e.g., Apple Silicon Macs), please run follow command:
```bash
TARGETPLATFORM=linux/arm64 docker compose up --build
```

#### Step 4: Enjoy the web-ui and vnc
- Web-UI: Open `http://localhost:7788` in your browser
- VNC Viewer (for watching browser interactions): Open `http://localhost:6080/vnc.html`
  - Default VNC password: "youvncpassword"
  - Can be changed by setting `VNC_PASSWORD` in your `.env` file

## Changelog
- [x] **2025/01/26:** Thanks to @vvincent1234. Now browser-use-webui can combine with DeepSeek-r1 to engage in deep thinking!
- [x] **2025/01/10:** Thanks to @casistack. Now we have Docker Setup option and also Support keep browser open between tasks.[Video tutorial demo](https://github.com/browser-use/web-ui/issues/1#issuecomment-2582511750).
- [x] **2025/01/06:** Thanks to @richard-devbot. A New and Well-Designed WebUI is released. [Video tutorial demo](https://github.com/warmshao/browser-use-webui/issues/1#issuecomment-2573393113).
