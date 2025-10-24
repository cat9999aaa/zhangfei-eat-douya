# 图片配置使用指南

## 概述

本系统现已支持多种图片来源，并提供灵活的优先级策略。你可以根据需要配置以下图片源：

1. **Unsplash** - 高质量免费图片库
2. **Pexels** - 免费图片和视频资源
3. **Pixabay** - 免费图片和插画
4. **本地图库** - 从本地目录选择图片
5. **用户上传** - 手动上传指定图片

## 功能特性

### 1. 多图片源支持

系统会按照配置的优先级依次尝试从不同来源获取图片，如果某个来源失败，会自动降级到下一个来源。

### 2. 本地图库管理

- 支持配置多个本地图片目录
- 为每个目录设置标签（如：nature, technology, business）
- 系统会根据文章关键词智能匹配标签

### 3. 用户上传功能

- 支持手动上传图片用于特定文章
- 支持的格式：png, jpg, jpeg, gif, webp, bmp

## 配置步骤

### 1. API 密钥配置

#### Unsplash API
1. 访问 [Unsplash Developers](https://unsplash.com/developers)
2. 创建应用获取 Access Key
3. 在配置页面填入 Access Key

#### Pexels API
1. 访问 [Pexels API](https://www.pexels.com/api/)
2. 注册并获取 API Key
3. 在配置页面填入 API Key

#### Pixabay API
1. 访问 [Pixabay API](https://pixabay.com/api/docs/)
2. 注册账号后在个人设置中获取 API Key
3. 在配置页面填入 API Key

### 2. 图片源优先级设置

在配置页面的"图片源优先级"部分，你可以拖拽排序来设置优先级。

**推荐配置：**
```
1. user_uploaded (用户上传) - 如果用户手动选择了图片，优先使用
2. unsplash - 质量最高
3. pexels - 备选方案
4. pixabay - 第二备选
5. local - 本地兜底
```

### 3. 本地图库配置

在 `config.json` 中配置本地图片目录：

```json
{
  "local_image_directories": [
    {
      "path": "pic",
      "tags": ["default", "general"]
    },
    {
      "path": "images/nature",
      "tags": ["nature", "landscape", "outdoor"]
    },
    {
      "path": "images/tech",
      "tags": ["technology", "business", "computer", "innovation"]
    }
  ]
}
```

**标签匹配规则：**
- 系统会从文章中提取关键词
- 将关键词与目录标签匹配
- 优先从匹配标签的目录中随机选择图片
- 如果没有匹配的标签，则从所有本地目录随机选择

### 4. 配置文件示例

完整的 `config.json` 示例：

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "gemini_base_url": "https://generativelanguage.googleapis.com",
  "unsplash_access_key": "YOUR_UNSPLASH_KEY",
  "pexels_api_key": "YOUR_PEXELS_KEY",
  "pixabay_api_key": "YOUR_PIXABAY_KEY",
  "default_model": "gemini-pro",
  "pandoc_path": "pandoc",
  "max_concurrent_tasks": 3,
  "image_source_priority": [
    "user_uploaded",
    "unsplash",
    "pexels",
    "pixabay",
    "local"
  ],
  "local_image_directories": [
    {
      "path": "pic",
      "tags": ["default"]
    },
    {
      "path": "images/nature",
      "tags": ["nature", "landscape"]
    }
  ],
  "enable_user_upload": true,
  "uploaded_images_dir": "uploads"
}
```

## 使用场景

### 场景 1：完全自动化
只配置 API 密钥，系统自动从在线图库获取配图。

### 场景 2：离线使用
不配置任何 API，只使用本地图库，适合没有网络或希望完全控制配图的场景。

### 场景 3：混合模式（推荐）
配置多个 API 和本地图库，实现多级降级保障：
- 优先尝试高质量在线图库
- 失败后使用其他在线图库
- 最后使用本地图库兜底

### 场景 4：手动控制
为特定主题的文章手动上传精选图片，确保配图完美匹配。

## 故障排查

### 图片下载失败
1. 检查 API Key 是否正确
2. 使用"测试 API"按钮验证连接
3. 检查网络连接
4. 查看 API 配额是否用完

### 本地图库无法使用
1. 确认目录路径正确
2. 确认目录中有图片文件
3. 确认图片格式被支持

### 优先级不生效
1. 保存配置后重启应用
2. 查看控制台日志确认图片源尝试顺序

## API 配额说明

| 服务 | 免费配额 | 限制 |
|------|---------|------|
| Unsplash | 50次/小时 | Demo 应用 |
| Pexels | 200次/小时 | 免费层 |
| Pixabay | 100次/分钟 | 免费层 |

**建议：** 设置合理的优先级顺序，避免快速耗尽单个服务的配额。

## 高级用法

### 按主题分类本地图库

创建主题目录结构：
```
images/
├── nature/
│   ├── forest.jpg
│   └── mountain.jpg
├── tech/
│   ├── computer.jpg
│   └── innovation.jpg
└── business/
    ├── meeting.jpg
    └── office.jpg
```

在配置中为每个目录设置精确的标签，系统会智能匹配最相关的图片。

### 用户上传工作流

1. 在写作界面，点击"上传图片"按钮
2. 选择本地图片文件
3. 图片上传成功后会显示在列表中
4. 生成文章时，系统会优先使用已上传的图片

## 注意事项

1. **版权问题**：所有 API 图片都是免费可用的，但请遵守各平台的使用条款
2. **存储空间**：从 API 下载的图片会临时存储，生成文档后自动删除
3. **图片质量**：优先级越高的图片源通常质量越好
4. **性能考虑**：API 请求有网络延迟，本地图库响应最快

## 技术支持

如遇问题，请查看：
1. 控制台日志输出
2. 配置文件是否正确
3. API 服务状态

更多信息请参考各图片服务的官方文档。
