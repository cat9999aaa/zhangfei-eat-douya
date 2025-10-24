# 张飞吃豆花 · AI 文章生成器

> 一站式的多模态写作助手，整合 Gemini 大模型、图片素材管线与文档导出能力，让内容生产更高效。

![写作界面预览](screenshot.png)

## 功能特点
- **多模型写作**：接入 Google Gemini 文本能力，可自定义默认模型、提示词与话题批量生成策略。
- **智能配图**：支持 ComfyUI 工作流、Gemini 图像 API、Unsplash/Pexels/Pixabay 以及本地图库、用户上传等多来源自动选图。
- **任务调度**：内置异步任务执行器，允许限制并发数、失败重试与单话题重试，确保批量写作稳定。
- **文档导出**：结合 `python-docx` 生成 Word 文档，可搭配 Pandoc 实现更多格式转换。
- **可视化配置**：提供 `/config` 页面直观管理 API Key、图像风格、目录与工作流设置，一键测试外部服务连通性。
- **历史归档**：自动整理生成结果至 `output/`，并在 `/history` 页面查看与下载已生成文档。

## 技术栈
- **后端**：Flask 3、Flask-CORS、requests
- **大模型**：`google-generativeai`（文本与图像）、自建 ComfyUI Runtime
- **文档处理**：python-docx（可选 Pandoc 增强）
- **前端**：Jinja2 模板、原生 JS/CSS（见 `static/` 与 `templates/`）

## 快速开始

### 1. 准备环境
- Python 3.10 或更高版本
- （可选）Pandoc，用于将 Word 转换到 PDF/Markdown 等格式
- （可选）正在运行的 ComfyUI 服务（默认监听 `http://127.0.0.1:8188`）

### 2. 克隆与安装依赖
```bash
git clone <your-repo-url>
cd zfcdy
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Windows 用户也可以直接双击 `start.bat`，脚本会自动安装依赖并启动服务。

### 3. 初始化配置
1. 复制模板：`cp config.example.json config.json`（Windows 可使用 `copy`）
2. 根据自身需求填写以下信息：
   - Gemini 文本写作：`gemini_api_key`、`default_model`、`default_prompt`
   - 图片来源：Unsplash/Pexels/Pixabay API Key、`image_source_priority` 顺序
   - 本地图片：在 `local_image_directories` 中声明路径与标签
   - ComfyUI：补充 `server_url`、`workflow_path` 等参数
   - Gemini 图像：在 `gemini_image_settings` 中开启并填写独立密钥
3. 如需启用 Word => 其他格式转换，请配置 `pandoc_path`

### 4. 启动应用
```bash
python app.py
```
服务会自动在 5000-5009 端口范围内寻找可用端口，并输出访问地址，例如 `http://localhost:5000`。

也可以使用 `flask --app app.py run` 等传统方式启动（注意保持同样的环境变量与工作目录）。

## 配置说明

### 核心字段
| 字段 | 说明 |
| ---- | ---- |
| `gemini_api_key` | Google AI Studio 生成的 API Key，用于文本写作 |
| `gemini_base_url` | Gemini API 基础地址，默认 `https://generativelanguage.googleapis.com` |
| `default_model` | 默认写作模型（如 `gemini-pro`、`gemini-1.5-flash`） |
| `default_prompt` | 全局提示词模版，可在写作页针对话题再补充细节 |
| `max_concurrent_tasks` | 写作任务并发数，建议依据账号配额谨慎设置 |
| `pandoc_path` | Pandoc 可执行文件路径，留空则跳过格式转换 |

### 图片来源与目录
- `image_source_priority`：决定配图时的查找顺序，支持值包括 `user_uploaded`、`comfyui`、`gemini_image`、`pexels`、`unsplash`、`pixabay`、`local`
- `local_image_directories`：本地图库列表，每项包含 `path` 与标签数组 `tags`，用于分类检索
- `enable_user_upload`、`uploaded_images_dir`：是否允许前端上传图片以及存储目录
- `output_directory`：生成文章的导出目录

### ComfyUI 设置（`comfyui_settings`）
| 字段 | 说明 |
| ---- | ---- |
| `enabled` | 是否启用 ComfyUI 生成配图 |
| `server_url` | ComfyUI API 地址（默认为本地 8188 端口） |
| `workflow_path` | 工作流 JSON 路径，可使用项目内 `workflow/` 示例 |
| `queue_size` / `timeout_seconds` / `max_attempts` | 控制任务队列、等待时间和重试次数 |
| `seed` | 默认随机种子，`-1` 表示完全随机 |

### Gemini 图像生成（`gemini_image_settings`）
| 字段 | 说明 |
| ---- | ---- |
| `enabled` | 开启后，可调用 Gemini 生成图片 |
| `api_key` / `base_url` | 可与文本写作共用或独立配置 |
| `model` | 推荐使用最新的 `gemini-2.5-flash-image-preview` 等模型 |
| `style` / `custom_prefix` / `custom_suffix` | 控制提示词风格，亦可在前端选择预设 |
| `aspect_ratio` | 输出图像比例（如 `16:9`、`1:1`） |
| `max_retries` / `timeout` | 调用时的容错设置 |

## 目录结构
```
├─app/
│ ├─api/             # 配置与写作相关 REST API
│ ├─config/          # 配置加载、默认值与模板
│ ├─models/          # 数据结构定义（如任务、话题对象）
│ ├─services/        # Gemini、ComfyUI、图像与文档等业务逻辑
│ ├─utils/           # 文件、网络、缓存工具函数
│ └─views/           # 页面路由（写作页、配置页、历史页）
├─static/            # 前端静态资源（JS/CSS）
├─templates/         # Jinja2 模板（主界面、组件、配置页面）
├─uploads/           # 用户上传或下载的临时图片
├─output/            # 生成的文章与文档
├─workflow/          # ComfyUI 工作流示例
├─config.example.json
├─requirements.txt
└─app.py             # 程序入口，负责端口探测与 Flask 启动
```

## 典型工作流程
1. 在 `/config` 页面填写 Gemini、图片服务与 ComfyUI 相关配置，并通过内置测试按钮验证连通性。
2. 切换到 `/` 写作页面，输入或批量导入话题，可为每个话题选择图片来源或上传封面。
3. 点击「开始写作」后，任务将进入后台执行：生成文章 → 可选摘要 → 按优先级获取或生成配图 → 生成 Word 文档。
4. 在 `output/` 目录或 `/history` 页面查看结果，可下载或重新触发失败话题。

## 常用命令
- 启动服务（开发模式）：`python app.py`
- 查看已生成的文档：访问 `/history` 或直接在 `output/` 打开
- 清理上传缓存：删除 `uploads/` 目录中的旧文件

## 故障排查
- **Gemini 调用失败**：确认 `gemini_api_key` 是否有效、是否开启了相应模型的使用权限。
- **图片服务不可达**：使用配置页的「测试连接」按钮，检查网络代理或 API Key 限额。
- **ComfyUI 请求超时**：调小 `comfyui_image_count`、增大 `timeout_seconds`，或保证 ComfyUI 队列空闲。
- **Pandoc 未工作**：确保已安装 Pandoc 并将执行路径填入 `pandoc_path`。

## 贡献与反馈
欢迎提交 Issue 或 Pull Request 以改进功能与体验。请在提交前确保：
- 已使用 `pip install -r requirements.txt` 安装依赖并通过基本功能测试
- 对新增配置、接口或前端交互补充必要的文档说明

## 📄 许可证
本项目基于 MIT 许可证开源。详情请见 `LICENSE` 文件。

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=cat9999aaa/zhangfei-eat-douya&type=date&legend=top-left)](https://www.star-history.com/#cat9999aaa/zhangfei-eat-douya&type=date&legend=top-left)

---

## 📞 联系方式
如有问题或建议，欢迎联系我：
- 微信: `Y2F0OTk5OXNzcw==`

