# 张飞吃豆芽 - AI 智能文章生成器

一个功能强大的、基于 Google Gemini API 的智能文章创作工具，支持批量生成文章、自动配图、自定义写作风格，并能直接输出高质量的 Word 文档。

![项目截图](screenshot.png)

## 核心功能

- **🚀 批量与并发**：一次性提交多个主题，利用并发处理，高效完成批量写作任务。
- **🎨 智能配图**：支持多种图片来源，包括 **ComfyUI (Stable Diffusion)** 本地生成、Unsplash、Pexels、Pixabay 等，并可为每个主题单独上传或指定图片。
- **✍️ 风格自定义**：通过自定义提示词（Prompt），轻松定义文章的写作风格、语气和格式。
- **📄 直接输出 Word**：利用 Pandoc，将生成的 Markdown 内容自动转换为 `.docx` 格式，方便后续编辑。
- **⚙️ 强大的配置中心**：提供独立的 Web 界面，用于管理 API 密钥、模型、图片源优先级、ComfyUI 工作流等。
- **📊 任务管理**：实时跟踪生成进度，对失败的任务可单独重试。

---

## 快速启动 (Windows 用户)

我们为 Windows 用户提供了“开箱即用”的一键启动脚本。

#### **环境准备**
1.  安装 [Python 3.10+](https://www.python.org/downloads/) (安装时请勾选 "Add Python to PATH")。
2.  安装 [Pandoc](https://pandoc.org/installing.html) (文档转换工具)。
3.  安装 [Git](https://git-scm.com/downloads/) (代码克隆工具)。

#### **启动步骤**
1.  **克隆项目代码**：
    ```bash
    git clone https://github.com/cat9999aaa/zhangfei-eat-douya.git
    cd zhangfei-eat-douya
    ```

2.  **一键启动**：
    直接双击项目目录中的 `start.bat` 文件。

    脚本会自动完成以下操作：
    - 检查并安装所有必需的 Python 依赖库。
    - 启动 Web 应用服务。
    - 在你的默认浏览器中自动打开 `http://1227.0.0.1:5000`。

---

## 详细使用指南

### 步骤 1：首次配置
应用启动后，请先进行基本配置：

1.  点击页面顶部的 **“配置”** 导航到配置页面。
2.  **填写必需项**：
    -   **Gemini API Key**: 从 [Google AI Studio](https://makersuite.google.com/app/apikey) 免费获取。
    -   **Pandoc 路径**: 填入你系统中 Pandoc 的可执行文件路径。
        -   Windows 默认: `C:\Program Files\Pandoc\pandoc.exe`
        -   macOS/Linux: 可在终端运行 `which pandoc` 查看路径。
3.  **可选配置**：
    -   配置 Unsplash、Pexels 等图片平台的 API Key 以启用它们作为图片源。
    -   配置 ComfyUI 的服务地址和工作流路径，以使用本地 AI 生成图片。
4.  点击页面底部的 **“保存配置”** 按钮。

### 步骤 2：生成文章
1.  返回 **“开始写作”** 页面。
2.  在输入框中输入一个或多个文章主题，每行一个。
3.  （可选）点击每个主题旁边的 **“🖼️ 图片设置”** 按钮，为该主题单独上传或指定图片。
4.  点击 **“开始生成”** 按钮。
5.  系统将开始执行任务，您可以在页面上看到实时进度。
6.  任务完成后，点击每个主题对应的 **“下载 Word 文档”** 按钮即可获取文件。

---

## 高级功能

### ComfyUI 工作流配置
要使用本地 Stable Diffusion (通过 ComfyUI) 生成图片，请按以下步骤操作：
1.  在 ComfyUI 中调试好你的工作流。
2.  在需要动态文本注入的节点（如 `CLIP Text Encode`）的文本框中，使用占位符 `{{positive_prompt}}` 和 `{{negative_prompt}}`。
3.  点击 ComfyUI 右侧的 **“队列提示”**，然后复制 API 格式的 Prompt，并将其保存为一个 `.json` 文件（例如 `workflow.json`）到本项目目录中。
4.  在本应用的配置页面，将 **ComfyUI Workflow 路径** 指向你保存的 `.json` 文件。
5.  点击 **“测试 ComfyUI 工作流”** 按钮，验证配置是否成功。

### API 接口文档
本项目提供了丰富的 API 接口，方便开发者进行二次开发和集成。

<details>
<summary>点击展开 API 详情</summary>

#### **配置管理**
-   `GET /api/config`: 获取当前配置（不含密钥）。
-   `POST /api/config`: 保存配置。

#### **文章生成**
-   `POST /api/generate`: 启动一个生成任务。
-   `GET /api/generate/status/<task_id>`: 查询指定任务的状态。
-   `POST /api/generate/retry`: 重试失败的主题。

#### **图片管理**
-   `POST /api/upload-image`: 上传单张图片。
-   `GET /api/list-local-images`: 列出本地图库中的图片。
-   `GET /api/list-uploaded-images`: 列出用户已上传的图片。

#### **其他**
-   `GET /api/models`: 获取所有可用的 Gemini 模型列表。
-   `GET /api/download/<filename>`: 下载指定的 Word 文档。
-   `GET /api/history`: 获取历史生成记录。

</details>

---

## 常见问题 (FAQ)

**Q: 启动时提示 `Python is not found` 怎么办?**
A: 请确保你已经安装了 Python 3.10 或更高版本，并且在安装时勾选了 "Add Python to PATH" 选项。

**Q: 点击生成后提示 "请先在配置页面设置 Pandoc 路径"？**
A: 这是因为程序找不到 Pandoc。请前往配置页面，填写正确的 Pandoc 可执行文件路径。

**Q: 如何获取各种 API Key？**
-   **Gemini**: 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)。
-   **Unsplash**: 前往 [Unsplash Developers](https://unsplash.com/developers)。
-   **Pexels / Pixabay**: 访问其对应的开发者平台注册并创建应用即可获取。

## 技术栈
- **后端**: Python, Flask, Flask-CORS, Requests
- **前端**: 原生 HTML, CSS, JavaScript
- **AI 核心**: Google Gemini API
- **文档转换**: Pandoc

## 许可证
本项目基于 MIT 许可证开源。