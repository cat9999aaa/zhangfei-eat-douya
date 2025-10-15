# 张飞吃豆芽

`张飞吃豆芽` 是一个基于 Google Gemini API 的智能文章创作工具，可以根据用户提供的标题或内容自动生成文章，并从 Unsplash 下载配图，最终生成包含图片的 Word 文档。

## 功能特性

- **智能文章生成**: 使用 Google Gemini API 根据标题或主题生成高质量文章
- **自动配图**: 自动提取文章关键词，从 Unsplash 搜索并下载最合适的图片
- **批量处理**: 支持一次输入多个标题，批量生成文章
- **模型自选**: 支持选择不同的 Gemini 模型
- **可配置**: 支持自定义 API Base URL 和密钥
- **友好界面**: 简洁美观的 Web 界面，操作简单

## 技术栈

- **后端**: Python + Flask
- **AI 模型**: Google Gemini API
- **图片服务**: Unsplash API
- **文档生成**: python-docx
- **前端**: HTML5 + CSS3 + JavaScript

## 安装步骤

### 1. 克隆或下载项目

```bash
cd write
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

项目运行后，在 Web 界面中点击"显示/隐藏配置"按钮，输入以下信息：

- **Gemini API Key**: (必需) 从 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取
- **Gemini Base URL**: (可选) 默认为 `https://generativelanguage.googleapis.com`
- **Unsplash Access Key**: (可选) 从 [Unsplash Developers](https://unsplash.com/developers) 获取，用于下载文章配图

配置也可以手动创建 `config.json` 文件：

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "gemini_base_url": "https://generativelanguage.googleapis.com",
  "unsplash_access_key": "YOUR_UNSPLASH_ACCESS_KEY",
  "default_model": "gemini-pro"
}
```

## 使用方法

### 1. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

### 2. 打开浏览器

访问 `http://localhost:5000`

### 3. 配置 API

首次使用时，点击"显示/隐藏配置"按钮：
- 输入 Gemini API Key（必需）
- 输入 Unsplash Access Key（可选，不配置则不会添加图片）
- 选择要使用的模型（可点击"刷新模型列表"获取可用模型）
- 点击"保存配置"

### 4. 生成文章

- 在"文章标题/主题"输入框中输入一个或多个标题（每行一个）
- 点击"开始生成"
- 等待生成完成
- 点击"下载 Word 文档"获取生成的文章

## 项目结构

```
write/
├── app.py                 # Flask 应用主文件
├── requirements.txt       # Python 依赖
├── config.example.json    # 配置文件示例
├── config.json           # 实际配置文件（需自己创建）
├── .gitignore            # Git 忽略文件
├── README.md             # 项目说明文档
├── static/               # 静态资源
│   ├── style.css        # 样式文件
│   └── script.js        # JavaScript 文件
├── templates/            # HTML 模板
│   └── index.html       # 主页面
└── output/               # 生成的文档输出目录
```

## API 接口

### 获取配置

```
GET /api/config
```

### 保存配置

```
POST /api/config
Content-Type: application/json

{
  "gemini_api_key": "YOUR_KEY",
  "gemini_base_url": "https://generativelanguage.googleapis.com",
  "unsplash_access_key": "YOUR_KEY",
  "default_model": "gemini-pro"
}
```

### 获取模型列表

```
GET /api/models
```

### 生成文章

```
POST /api/generate
Content-Type: application/json

{
  "topics": ["文章标题1", "文章标题2"],
  "model": "gemini-pro"
}
```

### 下载文件

```
GET /api/download/<filename>
```

## 注意事项

1. **API 配额**: Gemini API 和 Unsplash API 都有使用限制，请注意查看各自的配额政策
2. **文件保存**: 生成的 Word 文档保存在 `output` 目录中
3. **中文支持**: 文章生成默认使用中文，Word 文档支持中文
4. **图片可选**: 如果不配置 Unsplash Key，系统仍然会生成文章，只是没有配图
5. **网络要求**: 需要能够访问 Google API 和 Unsplash API

## 常见问题

### Q: 无法访问 Gemini API？
A: 请检查网络连接，确保可以访问 Google 服务。也可以尝试配置代理或使用自定义 Base URL。

### Q: 生成的文章质量不满意？
A: 可以尝试：
- 更详细地描述标题/主题
- 更换不同的 Gemini 模型
- 在标题中添加更多上下文信息

### Q: 找不到合适的配图？
A: 系统会自动提取文章关键词搜索图片。如果没有配置 Unsplash Key，将不会添加图片，但仍会生成文章。

### Q: 如何获取 API Key？
A:
- Gemini API: https://makersuite.google.com/app/apikey
- Unsplash API: https://unsplash.com/developers (注册开发者账号)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI 模型支持
- [Unsplash](https://unsplash.com/) - 高质量图片资源
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [python-docx](https://python-docx.readthedocs.io/) - Word 文档生成
