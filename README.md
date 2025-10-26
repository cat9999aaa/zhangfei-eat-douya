# 张飞吃豆芽 · 智能长文生产线

张飞吃豆芽是一个面向中文内容团队的全自动文章生产平台：一行标题即可批量生成 Word 文档、自动配图、同步归档。它将「写作 + 配图 + 排版 + 下载」整合到 Browser + Flask 的轻量体系里，非常适合新媒体编辑部、AI 剧本孵化团队、以及需要高频产出的自由撰稿人。

---

## 目录

1. [核心能力概览](#核心能力概览)
2. [一分钟上手](#一分钟上手)
3. [界面速览](#界面速览)
4. [功能亮点](#功能亮点)
5. [系统架构](#系统架构)
6. [REST API 接入指南](#rest-api-接入指南)
7. [参数配置说明](#参数配置说明)
8. [常用工作流](#常用工作流)
9. [疑难排查](#疑难排查)
10. [常见问题](#常见问题)
11. [Roadmap](#roadmap)
12. [贡献指南](#贡献指南)
13. [许可证](#许可证)

---

## 核心能力概览

| 模块 | 能力 | 说明 |
| ---- | ---- | ---- |
| AI 写作 | 批量生成长文 | 同时提交 50 个标题，自动并发、断点续写 |
| 图片管线 | 多源混合配图 | 支持 Gemini 图生图、ComfyUI、Unsplash、Pexels、Pixabay、本地图库、用户上传 |
| 文档输出 | 一键生成 Word | 通过 Pandoc 将 Markdown 转成 docx，保留章节结构与图片 |
| 任务调度 | 可视化仪表盘 | 轮询状态、进度条、重试、批量忽略、任务恢复 |
| 历史归档 | 快速检索 | 自动列出 docx，支持一键下载和打开所在目录 |
| 配置中心 | 图形化配置 | API 密钥、工作流、输出目录、风格模板全部可视化管理 |

---

## 一分钟上手

```bash
# 1. 克隆代码
git clone https://github.com/your-org/zhangfeichidouya.git
cd zhangfeichidouya

# 2. 安装依赖
python -m venv .venv
. .venv/Scripts/activate   # Windows
# 或 . .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt

# 3. 安装 Pandoc
# Windows: https://pandoc.org/installing.html
# macOS: brew install pandoc
# Ubuntu: sudo apt-get install pandoc

# 4. 启动服务
python app.py

# 5. 浏览器访问
http://localhost:5000
```

首登进入“配置中心”，填入 Gemini API Key、选择 Pandoc 路径，保存即可开始生成。

---

## 界面速览

```
├─ 写作面板
│  ├─ 批量标题输入 + 批量导入（支持 Excel/Notion 粘贴）
│  ├─ 配图开关、任务进度条
│  └─ 实时结果输出 + 单条/批量重试
│
├─ 配图设置对话框
│  ├─ 本地上传 / 剪贴板粘贴 / 图片 URL
│  └─ 每篇文章独立配置并持久化存储
│
├─ 配置中心
│  ├─ Gemini 文本 + 图像 + 自定义 Base URL
│  ├─ Unsplash / Pexels / Pixabay / ComfyUI 全量开关
│  ├─ 输出目录、并发任务数、图片风格模板
│  └─ 一键测试各项 API
│
└─ 历史记录
   ├─ 自动列出 docx，展示大小与时间
   ├─ 一键下载
   └─ 一键打开所在目录（Toast 提示最终路径）
```

---

## 功能亮点

### 写作引擎

- Gemini-2.5 文本模型驱动，系统默认提示词包含标题校验、章节结构、风格守护。
- 支持自定义 Prompt 模板，用 `{topic}` 占位符注入标题。
- 失联保护：任务信息持久化在浏览器，刷新后可继续查看进度。
- 重试策略：失败项可单独重试，或创建新任务批量重跑。

### 图片中台

- “优先级排序”机制，支持自定义图片来源顺序。
- 本地、上传、API、ComfyUI/Gemini 图生图混合，保证每篇文章配齐。
- 段落摘要自动生成英文描述，提升图像语义匹配。
- 图片持久化：配图设置保存在 LocalStorage，二次编辑无需重复上传。

### 文档交付

- Pandoc 转换，docx 中保留 Markdown 标题、粗体、列表、图片。
- 输出文件名即文章标题，减少后期手工整理。
- 支持自定义输出目录，后端打开目录时返回绝对路径，前端 Toast 告知用户。

### 运维体验

- 所有配置写入 `config.json`，可直接备份迁移。
- `/api/open-output-directory` 针对无图形界面的服务器给出友好错误。
- 下载接口发送 `Cache-Control: no-store`，避免浏览器缓存旧文档。

---

## 系统架构

```
┌──────────────┐        ┌──────────────┐
│  Browser UI   │ <----> │ Flask Backend │
└──────────────┘        └───────┬──────┘
      ▲   │                      │
      │   │ fetch                │ 调度
      │   ▼                      │
┌──────────────┐        ┌──────────────┐
│ LocalStorage  │        │ Task Service │
└──────────────┘        └───────┬──────┘
                                 │
                                 ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Gemini Text  │   │ Gemini Image │   │ ComfyUI / API│
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          │                  │                  │
          ▼                  ▼                  ▼
                   ┌────────────────────────┐
                   │ Pandoc (Markdown->Docx)│
                   └──────────┬────────────┘
                              ▼
                        Output Directory
```

---

## 参数配置说明

### 必填

| 配置项 | 示例 | 说明 |
| ------ | ---- | ---- |
| `gemini_api_key` | `sk-xxxxx` | Gemini 文本模型密钥 |
| `pandoc_path` | `C:\Program Files\Pandoc\pandoc.exe` | Pandoc 可执行文件 |

### 推荐

| 配置项 | 默认 | 作用 |
| ------ | ---- | ---- |
| `default_model` | `gemini-2.5-pro` | 主写作模型 |
| `default_prompt` | 详见配置页 | 定义写作结构、风格和自检 |
| `output_directory` | `output` | Word 文档输出目录 |
| `max_concurrent_tasks` | 3 | 同时运行的写作任务数 |

### 图片相关

| 配置项 | 类型 | 说明 |
| ------ | ---- | ---- |
| `image_source_priority` | array | 图片来源优先级，例如 `["user_uploaded","gemini_image","comfyui","unsplash"]` |
| `local_image_directories` | array | 本地图库目录及标签，支持多个 path/tags |
| `comfyui_settings` | object | Workflow 地址、超时时间、并发数等 |
| `gemini_image_settings` | object | 图生图模型、风格、重试次数 |

修改配置后点击“保存所有配置”，再执行“重新测试”以保证所有源可用。

---

## REST API 接入指南

张飞吃豆芽的全部能力都暴露在 `/api` 路径下，可用于自建排班系统、脚本化调用或与第三方平台集成。以下为最常用接口。

> 基础约定  
> - 所有接口默认返回 JSON（除文件下载外）。  
> - 出错时返回形如 `{ "error": "...", "success": false }` 的结构，并附带 HTTP 状态码。  
> - 建议在调用前确保已在配置中心完成 Pandoc 与 API Key 的设置。

### 1. 创建写作任务

```
POST /api/generate
Content-Type: application/json

{
  "topics": ["如何提高工作效率", "AI 对未来的影响"],
  "topic_images": {
    "如何提高工作效率": {
      "type": "upload",
      "uploadedPath": "uploads/image_xxx.png"
    }
  }
}
```

响应：

```json
{
  "success": true,
  "task_id": "20250115-143012-9f83c2"
}
```

### 2. 轮询任务状态

```
GET /api/generate/status/<task_id>
```

示例响应：

```json
{
  "status": "running",               // running / completed
  "progress": 40,
  "results": [
    {
      "topic": "如何提高工作效率",
      "article_title": "XX 是如何提升效率的 7 个关键动作",
      "filename": "XX 是如何提升效率的 7 个关键动作.docx",
      "has_image": true,
      "image_count": 3
    }
  ],
  "errors": [
    {
      "topic": "AI 对未来的影响",
      "error": "Gemini API rate limit",
      "retry_count": 1
    }
  ]
}
```

### 3. 重试失败条目

```
POST /api/generate/retry

{
  "task_id": "20250115-143012-9f83c2",
  "topics": ["AI 对未来的影响"]
}
```

如原任务已失效，接口会返回 `{"success": true, "new_task": true, "task_id": "..."}`，可继续用新的 `task_id` 轮询。

### 4. 下载生成的 Word 文档

```
GET /api/download/<filename>
```

示例：

```
GET /api/download/%E5%A6%82%E4%BD%95%E6%8F%90%E9%AB%98%E5%B7%A5%E4%BD%9C%E6%95%88%E7%8E%87.docx
```

响应为二进制流，支持 `download` 属性，也可直接写入文件。

### 5. 获取历史文档

```
GET /api/history
```

响应：

```json
{
  "files": [
    {
      "filename": "如何提高工作效率.docx",
      "size": 4312456,
      "created": "2025-01-15 14:32:10",
      "title": "如何提高工作效率"
    }
  ]
}
```

### 6. 打开输出目录

```
POST /api/open-output-directory

{
  "filename": "如何提高工作效率.docx"
}
```

- 桌面环境会直接唤起文件管理器，并返回实际目录路径。
- 无 GUI 环境会返回提示，建议只在本地/桌面部署时调用。

### 7. 运行前检查

还可以通过以下接口了解环境状态：

| 接口 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/api/check-pandoc` | GET | 返回 `{ "pandoc_configured": true/false }` |
| `/api/test-model` | POST | 测试 Gemini 文本模型是否可用 |
| `/api/test-unsplash` / `/api/test-pexels` / `/api/test-pixabay` | POST | 验证图片 API |
| `/api/test-comfyui` | POST | 检查 ComfyUI 工作流连通性 |

在自动化脚本中，可以先调用 `/api/check-pandoc` 与 `/api/test-model` 确认环境，再发起写作任务。

---

## 常用工作流

### 1. 快速选题批量生成
1. 复制 Excel 中的标题列。
2. 写作页点击“批量导入”，粘贴，确认展示数量。
3. 开启“生成文章配图”开关。
4. 点击“开始生成”，等待任务完成。
5. 在结果列表中逐一下载 Word 文档或直接打开输出目录。

### 2. 指定图片资源
1. 在写作页添加标题后，点击对应的“图片设置”按钮。
2. 上传本地文件或粘贴剪贴板截图。
3. 保存设置后图标变为高亮。
4. 生成文档时该图片优先使用，其余缺口自动由 API 填充。

### 3. 二次编辑与归档
1. 生成完毕后前往“历史记录”页面。
2. 按时间排序查看 docx 列表。
3. 点击“打开目录”查看 Toast 提示，确认已弹出的文件夹位置。
4. 将 docx 拖入团队共享盘或知识库。

---

## 疑难排查

| 现象 | 可能原因 | 处理建议 |
| ---- | -------- | -------- |
| 提示“请先在配置页面设置 Pandoc 路径” | 未安装或路径错误 | 安装 Pandoc，填写绝对路径，保存配置再重试 |
| 生成卡在“等待写作服务响应” | API 限频或网络波动 | 降低并发任务数，或更换网络代理 |
| 配图全部失败 | 图像源未配置正确 | 逐个点击“测试”按钮，确认 API Key、Workflow、代理可用 |
| Word 文档打不开 | Pandoc 转换失败 | 检查 `app/services/document_service.py` 日志，确认 Markdown 是否含非法字符 |
| 打开目录无反应 | 服务器无桌面环境 | 接口会返回错误信息，请在历史记录或结果列表中复制输出路径，手动打开 |

---

## 常见问题

**Q: 可以自定义写作风格吗？**  
A: 可以。在配置中心的“默认提示词”里编辑 Markdown 提示模板，使用 `{topic}` 代表标题，还可以引导模型输出特定章节、语气、长度。

**Q: 任务刷新后还能继续吗？**  
A: 浏览器会缓存任务 ID 与标题列表，刷新后自动恢复轮询。若后台任务已完成，会直接显示最终结果。

**Q: 如何接入第三方中转服务？**  
A: 将 `gemini_base_url` 改为你的中转地址，文本与图像模块均会使用该 Base URL。务必确保兼容 Google Gemini API 协议。

**Q: 可以和企业知识库联动吗？**  
A: 当前版本聚焦生产 Word 文档。如需扩展，可在生成后通过脚本上传到 Notion / Confluence / 飞书，欢迎提交 PR。

---

## Roadmap

- [ ] 增加 Markdown + HTML 多格式导出
- [ ] 支持自定义模板（题图、封面、版权信息）
- [ ] 引入账号权限体系，支持团队协作
- [ ] 任务结果统计与仪表盘
- [ ] 多语言写作模式（英文、日文等）

想要的功能不在列表中？欢迎提 Issue 告诉我们。

---

## 贡献指南

1. Fork 仓库，创建特性分支：
   ```bash
   git checkout -b feature/awesome
   ```
2. 完成开发后运行自测（启动 Flask，试跑写作和配图）。
3. 提交 PR 时请包含：
   - 变更说明
   - 复现与测试步骤
   - 截图或命令行输出（如适用）

我们欢迎任何改进：UI 优化、性能调优、接入更多数据源、改写提示词等。

---

## 许可证

本项目基于 MIT License 开源。你可以自由修改、分发，但请保留原始许可证与署名。

---

如果张飞吃豆芽帮到了你，欢迎 Star 支持，也欢迎在 Issues 留言分享你的生产力案例。让我们把“AI 写稿 + 配图 + 分发”变成真正的一键流程。
