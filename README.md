# 张飞吃豆芽 - AI 智能文章生成器

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> 一款功能强大的、运行于本地的 AI 智能文章创作工具。它深度集成 Google Gemini API，支持批量生成、自动配图、风格自定义，并能一键输出高质量的 Word 文档。

![项目截图](screenshot.png)

---

## 目录
- [核心功能](#-核心功能)
- [快速启动-windows-用户](#-快速启动-windows-用户)
- [详细使用指南](#-详细使用指南)
- [高级功能](#-高级功能)
  - [ComfyUI-工作流配置](#comfyui-工作流配置)
  - [api-接口文档](#api-接口文档)
- [项目结构](#-项目结构)
- [贡献指南](#-贡献指南)
- [未来路线图](#-未来路线图)
- [常见问题-faq](#-常见问题-faq)
- [致谢](#-致谢)
- [许可证](#-许可证)
- [联系方式](#-联系方式)

---

## ✨ 核心功能

- **🚀 批量与并发**：一次性提交多个主题，利用并发处理，高效完成批量写作任务。
- **🎨 智能配图**：支持多种图片来源，包括 **ComfyUI (Stable Diffusion)** 本地生成、Unsplash、Pexels、Pixabay 等，并可为每个主题单独上传或指定图片。
- **✍️ 风格自定义**：通过自定义提示词（Prompt），轻松定义文章的写作风格、语气和格式。
- **📄 直接输出 Word**：利用 Pandoc，将生成的 Markdown 内容自动转换为 `.docx` 格式，方便后续编辑。
- **⚙️ 强大的配置中心**：提供独立的 Web 界面，用于管理 API 密钥、模型、图片源优先级、ComfyUI 工作流等。
- **📊 任务管理**：实时跟踪生成进度，对失败的任务可单独重试。

---

## 🚀 快速启动 (Windows 用户)

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
    - 在你的默认浏览器中自动打开 `http://127.0.0.1:5000`。

---

## 📖 详细使用指南

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

## 🛠️ 高级功能

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

## 📁 项目结构
```
.
├── app.py              # Flask 主应用
├── start.bat           # Windows 一键启动脚本
├── requirements.txt    # Python 依赖
├── config.json         # 配置文件 (首次运行后生成)
├── README.md           # 本文档
├── templates/          # HTML 页面模板
│   ├── layout.html
│   ├── write.html
│   ├── config.html
│   └── history.html
├── static/             # CSS, JavaScript 等静态资源
│   ├── style.css
│   ├── write.js
│   ├── config.js
│   └── history.js
├── output/             # 生成的 Word 文档默认存放目录
├── uploads/            # 用户上传的图片默认存放目录
└── pic/                # 本地图库示例目录
```

---

## 🤝 贡献指南
我们欢迎任何形式的贡献！无论是报告 Bug、提出功能建议还是提交代码，都对项目有巨大帮助。
1.  **报告问题**: 请通过 [Issues](https://github.com/cat9999aaa/zhangfei-eat-douya/issues) 提交您遇到的问题。
2.  **提交代码**:
    -   Fork 本仓库。
    -   创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
    -   提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
    -   将分支推送到远程 (`git push origin feature/AmazingFeature`)。
    -   开启一个 Pull Request。

---

## 🗺️ 未来路线图
- [ ] **支持更多大语言模型**：集成如 Claude、Kimi 等更多优秀的 LLM。
- [ ] **文章内容优化**：增加 SEO 关键词密度分析、自动摘要等功能。
- [ ] **图片后期处理**：为生成的图片增加自动添加水印的功能。
- [ ] **UI/UX 改进**：持续优化前端界面，提升用户体验。
- [ ] **Docker 支持**：提供 Dockerfile，实现一键部署。

---

## ❓ 常见问题 (FAQ)

**Q: 启动时提示 `Python is not found` 怎么办?**
A: 请确保你已经安装了 Python 3.10 或更高版本，并且在安装时勾选了 "Add Python to PATH" 选项。

**Q: 点击生成后提示 "请先在配置页面设置 Pandoc 路径"？**
A: 这是因为程序找不到 Pandoc。请前往配置页面，填写正确的 Pandoc 可执行文件路径。

**Q: 如何获取各种 API Key？**
-   **Gemini**: 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)。
-   **Unsplash**: 前往 [Unsplash Developers](https://unsplash.com/developers)。
-   **Pexels / Pixabay**: 访问其对应的开发者平台注册并创建应用即可获取。

---

## 🙏 致谢
- [Google Gemini](https://deepmind.google/technologies/gemini/) - 提供强大的 AI 内容生成能力。
- [Pandoc](https://pandoc.org/) - 强大的文档格式转换工具。
- [Flask](https://flask.palletsprojects.com/) - 轻量而强大的 Python Web 框架。
- [Shields.io](https://shields.io/) - 提供美观的徽章。

---

## 📄 许可证
本项目基于 MIT 许可证开源。详情请见 `LICENSE` 文件。

---
## 📞 联系方式
如有问题或建议，欢迎联系我：
- 微信: `Y2F0OTk5OXNzcw==`