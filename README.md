# 张飞吃豆芽 - AI 智能文章生成器

一个功能强大的基于 Google Gemini API 的智能文章创作工具，支持批量生成文章、自动配图、自定义写作风格，并输出高质量的 Word 文档。

<img width="1519" height="750" alt="image" src="https://github.com/user-attachments/assets/6d66baf5-e8e6-44aa-aaee-361eae27ebfe" />


## 功能特性

### 📝 智能文章创作
- **AI 驱动**: 使用 Google Gemini API 生成高质量文章
- **批量生成**: 一次最多可处理 50 个标题，并发执行提高效率
- **自定义提示词**: 支持自定义写作风格和要求，使用 `{topic}` 作为标题占位符
- **模型选择**: 支持多种 Gemini 模型（gemini-pro、gemini-2.5-pro 等）
- **自动标题提取**: 智能提取文章标题作为文件名

### 🖼️ 灵活的图片配图
- **多种图片来源**:
  - Unsplash API - 高质量专业摄影图片
  - Pexels API - 免费商用图片库
  - Pixabay API - 多样化图片资源
  - 本地图库 - 使用本地图片目录
  - 用户上传 - 支持为每个标题单独上传图片
- **图片来源优先级**: 可自定义图片获取的优先级顺序（拖拽排序）
- **智能关键词提取**: 自动从文章中提取适合的英文关键词搜索配图
- **多种上传方式**:
  - 本地文件上传
  - 剪贴板粘贴
  - 图片 URL 导入
- **图片设置持久化**: 设置的图片会保存在浏览器中，刷新页面不会丢失

### 📄 Word 文档生成
- **Pandoc 转换**: 使用 Pandoc 将 Markdown 转换为 Word 文档
- **无时间戳文件名**: 文档名称直接使用文章标题，便于识别和管理
- **自定义输出目录**: 可在后台配置文档保存位置
- **图片自动插入**: 配图自动插入到文章第一段后
- **格式优化**: 支持 Markdown 格式，包括标题、粗体、段落等

### ⚙️ 完善的配置管理
- **独立配置页面**: 专门的配置管理界面
- **API 配置**:
  - Gemini API Key 和 Base URL
  - Unsplash、Pexels、Pixabay API Key
  - API 测试功能，验证配置是否正确
- **本地图库配置**: 支持配置多个本地图片目录及标签
- **输出目录配置**: 自定义文档输出位置
- **并发任务控制**: 设置同时生成文章的数量（1-10）

### 📊 任务管理与状态
- **实时进度显示**: 显示生成进度条和完成百分比
- **任务持久化**: 任务状态保存在浏览器中，刷新页面后可继续查看进度
- **错误重试**: 生成失败的文章可以单独重试
- **批量下载**: 生成完成后可逐个下载 Word 文档

### 📚 历史记录
- **历史记录页面**: 查看所有已生成的文档
- **文件信息**: 显示文件名、大小、创建时间
- **快速下载**: 一键下载历史文档

### 🎨 用户体验
- **美观界面**: 简洁现代的 Web 界面，渐变色设计
- **响应式设计**: 支持桌面和移动设备
- **状态保存**: 输入的标题和配置会自动保存（24小时有效期）
- **清空/删除操作**: 第一个输入框支持清空，其他输入框支持删除
- **导航栏**: 快速切换写作、配置、历史记录页面

## 技术栈

**后端**:
- Python 3.x
- Flask - Web 框架
- Flask-CORS - 跨域支持
- Requests - HTTP 请求
- Threading - 多线程并发处理

**AI 与服务**:
- Google Gemini API - AI 文章生成
- Unsplash API - 图片服务
- Pexels API - 图片服务
- Pixabay API - 图片服务
- Pandoc - Markdown 到 Word 转换

**前端**:
- HTML5 + CSS3
- JavaScript (原生)
- LocalStorage - 本地数据持久化
- Fetch API - 异步请求

## 安装步骤

### 1. 环境要求

- Python 3.7+
- Pandoc (必需，用于生成 Word 文档)

### 2. 安装 Pandoc

**Windows**:
下载并安装 Pandoc [<sup>2</sup>](https://pandoc.org/installing.html)，默认安装路径为 `C:\Program Files\Pandoc\pandoc.exe`

**macOS**:
```bash
brew install pandoc
```

**Linux**:
```bash
sudo apt-get install pandoc  # Debian/Ubuntu
sudo yum install pandoc      # CentOS/RHEL
```

### 3. 克隆项目

```bash
git clone <repository-url>
cd zfcdy-ziyong
```

### 4. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 5. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 使用指南

### 首次配置

1. 访问 `http://localhost:5000`
2. 点击导航栏的"配置"进入配置页面
3. 配置必需项：
   - **Gemini API Key**: 从 Google AI Studio [<sup>3</sup>](https://makersuite.google.com/app/apikey) 获取
   - **Pandoc 路径**: 设置 Pandoc 可执行文件路径
4. 可选配置：
   - 图片 API Keys (Unsplash/Pexels/Pixabay)
   - 本地图库目录
   - 输出目录
   - 默认提示词
5. 点击"保存配置"

### 生成文章

1. 在主页面输入文章标题（可添加多个）
2. 点击"图片设置"为特定标题配置专属图片（可选）
3. 点击"开始生成"
4. 实时查看生成进度
5. 完成后点击"下载 Word 文档"

### 图片设置

**为单个标题设置专属图片**:
1. 点击标题后的"🖼️ 图片设置"按钮
2. 选择图片来源：
   - **上传图片**: 选择本地文件
   - **剪贴板**: 复制图片后粘贴（Ctrl+V）
   - **URL**: 输入图片链接
3. 点击"保存设置"

**全局图片策略**:
在配置页面设置图片源优先级，系统会按顺序尝试获取图片。

### 自定义写作风格

在配置页面的"写作提示词配置"中：
1. 输入自定义提示词
2. 使用 `{topic}` 作为标题占位符
3. 示例：
```
请根据标题「{topic}」写一篇800字的科技文章，要求：
1. 语言专业且易懂
2. 包含实际案例
3. 结构清晰，有小标题
```

## 项目结构

```
zfcdy-ziyong/
├── app.py                      # Flask 主应用
├── requirements.txt            # Python 依赖
├── config.json                 # 配置文件（运行时生成）
├── config.example.json         # 配置示例
├── README.md                   # 项目文档
├── static/                     # 静态资源
│   ├── style.css              # 全局样式
│   ├── script.js              # 主页 JS（已弃用）
│   ├── write.js               # 写作页面 JS
│   ├── config.js              # 配置页面 JS
│   └── history.js             # 历史记录 JS
├── templates/                  # HTML 模板
│   ├── layout.html            # 基础布局模板
│   ├── write.html             # 写作页面
│   ├── config.html            # 配置页面
│   └── history.html           # 历史记录页面
├── output/                     # 生成的文档（默认）
├── uploads/                    # 用户上传的图片
└── pic/                        # 本地图库（示例）
```

## API 接口文档

### 配置管理

**获取配置**
```
GET /api/config
```

**保存配置**
```
POST /api/config
Content-Type: application/json

{
  "gemini_api_key": "YOUR_KEY",
  "gemini_base_url": "https://generativelanguage.googleapis.com",
  "pandoc_path": "C:\\Program Files\\Pandoc\\pandoc.exe",
  "output_directory": "output",
  "default_model": "gemini-2.5-pro",
  "default_prompt": "自定义提示词",
  "max_concurrent_tasks": 3,
  "unsplash_access_key": "YOUR_KEY",
  "pexels_api_key": "YOUR_KEY",
  "pixabay_api_key": "YOUR_KEY",
  "image_source_priority": ["user_uploaded", "unsplash", "local", "pexels", "pixabay"],
  "local_image_directories": [
    {"path": "pic", "tags": ["default"]}
  ]
}
```

### 文章生成

**启动生成任务**
```
POST /api/generate
Content-Type: application/json

{
  "topics": ["标题1", "标题2"],
  "topic_images": {
    "标题1": {"type": "uploaded", "path": "uploads/image.jpg"},
    "标题2": {"type": "url", "url": "https://example.com/image.jpg"}
  }
}

Response: {"success": true, "task_id": "uuid"}
```

**查询任务状态**
```
GET /api/generate/status/<task_id>

Response: {
  "status": "running",
  "progress": 50.0,
  "total": 2,
  "results": [...],
  "errors": [...]
}
```

**重试失败任务**
```
POST /api/generate/retry

{
  "task_id": "uuid",
  "topics": ["失败的标题"]
}
```

### 图片管理

**上传图片**
```
POST /api/upload-image
Content-Type: multipart/form-data

Form Data: image=<file>

Response: {
  "success": true,
  "filename": "image_20251016_123456.jpg",
  "path": "uploads/image_20251016_123456.jpg"
}
```

**列出本地图库图片**
```
GET /api/list-local-images
```

**列出上传的图片**
```
GET /api/list-uploaded-images
```

### 其他接口

**获取模型列表**
```
GET /api/models
```

**下载文档**
```
GET /api/download/<filename>
```

**获取历史记录**
```
GET /api/history
```

**检查 Pandoc 配置**
```
GET /api/check-pandoc
```

**测试图片 API**
```
POST /api/test-unsplash
POST /api/test-pexels
POST /api/test-pixabay

{
  "access_key": "YOUR_KEY"  // 或 api_key
}
```

## 配置说明

### config.json 配置项

| 配置项 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `gemini_api_key` | string | ✅ | Gemini API 密钥 |
| `pandoc_path` | string | ✅ | Pandoc 可执行文件路径 |
| `gemini_base_url` | string | ❌ | Gemini API 地址（默认官方地址） |
| `output_directory` | string | ❌ | 文档输出目录（默认 output） |
| `default_model` | string | ❌ | 默认模型（默认 gemini-pro） |
| `default_prompt` | string | ❌ | 自定义提示词 |
| `max_concurrent_tasks` | int | ❌ | 并发任务数（1-10，默认 3） |
| `unsplash_access_key` | string | ❌ | Unsplash API 密钥 |
| `pexels_api_key` | string | ❌ | Pexels API 密钥 |
| `pixabay_api_key` | string | ❌ | Pixabay API 密钥 |
| `image_source_priority` | array | ❌ | 图片来源优先级 |
| `local_image_directories` | array | ❌ | 本地图库配置 |
| `uploaded_images_dir` | string | ❌ | 上传图片保存目录 |

## 常见问题

### Q: 如何获取 API Key？

**Gemini API**:
1. 访问 Google AI Studio [<sup>3</sup>](https://makersuite.google.com/app/apikey)
2. 登录 Google 账号
3. 点击"Create API Key"
4. 复制密钥

**Unsplash API**:
1. 访问 Unsplash Developers [<sup>4</sup>](https://unsplash.com/developers)
2. 注册开发者账号
3. 创建应用
4. 获取 Access Key

**Pexels / Pixabay**: 类似流程，访问对应的开发者平台

### Q: 生成文章时出现 "请先在配置页面设置 Pandoc 路径" 错误？

确保已正确安装 Pandoc，并在配置页面设置正确的路径：
- Windows: `C:\Program Files\Pandoc\pandoc.exe`
- macOS/Linux: 通常是 `/usr/local/bin/pandoc` 或 `/usr/bin/pandoc`

可以在终端运行 `which pandoc`（Linux/Mac）或 `where pandoc`（Windows）查看路径。

### Q: 文档名称太长或包含特殊字符？

系统会自动清理文件名中的非法字符（如 `\ / : * ? " < > |`），并限制长度为 50 个字符。

### Q: 如何修改文档输出位置？

在配置页面的"输出目录配置"中设置，支持相对路径和绝对路径：
- 相对路径: `output` 或 `documents/articles`
- 绝对路径: `D:\Documents\Articles` 或 `/home/user/documents`

### Q: 图片设置后刷新页面就丢失了？

新版本已支持图片设置持久化，设置的图片会保存在浏览器 LocalStorage 中，有效期 24 小时。

### Q: 如何使用本地图片库？

1. 在配置页面的"本地图库配置"中添加图片目录
2. 设置目录路径和标签（如 `path: pic/nature`, `tags: nature, landscape`）
3. 系统会根据文章主题匹配标签，随机选择图片
4. 在"图片源优先级"中调整 "本地图库" 的位置

### Q: 并发任务数量应该设置多少？

建议设置为 3-5。设置过大可能触发 API 频率限制，设置过小会降低批量生成效率。

### Q: 无法访问 Gemini API？

- 检查网络连接
- 确认 API Key 是否正确
- 如果在中国大陆，可能需要使用代理或第三方中转服务
- 可以在配置中修改 `gemini_base_url` 使用代理地址

## 注意事项

1. **API 配额限制**: Gemini 和图片 API 都有使用限制，注意查看配额政策
2. **文件覆盖**: 如果生成同名文档，会覆盖原有文件
3. **临时文件**: 从 API 下载的图片会作为临时文件保存，生成文档后自动删除
4. **浏览器兼容性**: 建议使用现代浏览器（Chrome、Firefox、Edge）
5. **数据安全**: API Key 保存在本地 config.json 文件中，请勿泄露

## 更新日志

### v2.0.0 (2025-01)
- ✨ 新增多图片源支持（Pexels、Pixabay、本地图库）
- ✨ 新增图片设置功能（上传、剪贴板、URL）
- ✨ 图片设置持久化
- ✨ 可自定义输出目录
- ✨ 独立配置页面
- ✨ 历史记录页面
- ✨ 任务状态持久化
- 🔧 移除文件名时间戳
- 🔧 第一个输入框改为"清空"按钮
- 🎨 界面优化和响应式设计

### v1.0.0
- 🎉 初始版本发布
- ✨ 基于 Gemini API 的文章生成
- ✨ Unsplash 自动配图
- ✨ Word 文档输出

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- Google Gemini [<sup>5</sup>](https://deepmind.google/technologies/gemini/) - AI 文章生成
- Unsplash [<sup>6</sup>](https://unsplash.com/) - 高质量图片
- Pexels [<sup>7</sup>](https://www.pexels.com/) - 免费图片资源
- Pixabay [<sup>8</sup>](https://pixabay.com/) - 免费图片资源
- Flask [<sup>9</sup>](https://flask.palletsprojects.com/) - Web 框架
- Pandoc [<sup>10</sup>](https://pandoc.org/) - 文档转换工具

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 Issue [<sup>11</sup>](https://github.com/your-repo/issues)
- 发送邮件到: your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给一个 Star！
