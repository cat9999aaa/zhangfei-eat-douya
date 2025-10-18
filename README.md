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

## 快速启动 (Windows)

本项目提供了为 Windows 用户定制的一键启动脚本。

1.  **确保环境**：
    *   已安装 [Python 3.10+](https://www.python.org/downloads/)。
    *   已安装 [Pandoc](https://pandoc.org/installing.html) 并记住其安装路径。
    *   已安装 [Git](https://git-scm.com/downloads/)。

2.  **克隆项目**：
    ```bash
    git clone https://github.com/cat9999aaa/zhangfei-eat-douya.git
    cd zhangfei-eat-douya
    ```

3.  **一键启动**：
    *   直接双击运行项目根目录下的 `start.bat` 文件。
    *   脚本会自动检查并安装所需的 Python 依赖库，然后启动应用。
    *   启动成功后，它会自动在您的默认浏览器中打开 `http://127.0.0.1:5000`。

## 如何使用

### 1. 首次配置

应用启动后，浏览器会自动打开。请先进行基本配置：

1.  点击页面顶部的 **“配置”** 导航到配置页面。
2.  **填写必需项**：
    *   **Gemini API Key**: 从 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取。
    *   **Pandoc 路径**: 填入您系统中 Pandoc 的可执行文件路径（例如 `C:\Program Files\Pandoc\pandoc.exe`）。
3.  **可选配置**：
    *   配置 Unsplash、Pexels 等图片平台的 API Key 以启用它们作为图片源。
    *   配置 ComfyUI 的服务地址和工作流路径，以使用本地 AI 生成图片。
4.  点击页面底部的 **“保存配置”** 按钮。

### 2. 生成文章

1.  返回 **“开始写作”** 页面。
2.  在输入框中输入一个或多个文章主题，每行一个。
3.  （可选）点击每个主题旁边的 **“🖼️ 图片设置”** 按钮，为该主题单独上传或指定图片。
4.  点击 **“开始生成”** 按钮。
5.  系统将开始执行任务，您可以在页面上看到实时进度。
6.  任务完成后，点击每个主题对应的 **“下载 Word 文档”** 按钮即可获取文件。

## 技术栈

- **后端**: Python, Flask
- **前端**: HTML, CSS, JavaScript
- **AI核心**: Google Gemini API
- **文档转换**: Pandoc

## 许可证

本项目基于 MIT 许可证开源。