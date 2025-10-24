# Gemini 图像生成功能说明

## 功能概述

本次更新为系统添加了完整的 Google Gemini 图像生成（Imagen）功能，支持云端 AI 绘图、自动重试和降级机制。

## 主要特性

### ✨ 核心功能

1. **Google Imagen API 集成**
   - 支持使用 Google Gemini API 生成高质量图片
   - 基于 Imagen 3.0 等先进图像生成模型
   - 完全云端处理，无需本地 GPU

2. **8 种预设风格**
   - 写实摄影 (realistic)
   - 插画风格 (illustration)
   - 动漫风格 (anime)
   - 赛博朋克 (cyberpunk)
   - 商业配图 (business)
   - 水彩画 (watercolor)
   - 极简主义 (minimalist)
   - 奇幻风格 (fantasy)

3. **自定义提示词系统**
   - 用户可添加自定义提示词前缀
   - 用户可添加自定义提示词后缀
   - 自动与风格预设结合

4. **智能重试和降级机制**
   - 默认重试 3 次（可自定义 1-5 次）
   - 单次请求超时时间可配置（10-120 秒）
   - 失败后自动降级到其他图片源（ComfyUI、图片库 API 等）

5. **灵活配置**
   - 可与文本生成共用 API Key，也可单独配置
   - 支持自定义 Base URL（适配代理或私有部署）
   - 从服务器获取可用模型列表
   - 可启用/禁用此功能

## 文件变更

### 新增文件

1. `app/services/gemini_image_service.py` - Gemini 图像生成核心服务
   - 图像生成函数
   - 风格预设定义
   - API 测试功能
   - 模型列表获取

### 修改文件

#### 后端

1. `app/config/defaults.py`
   - 添加 `DEFAULT_GEMINI_IMAGE_CONFIG` 默认配置

2. `app/config/loader.py`
   - 添加 `get_gemini_image_settings()` 配置加载函数

3. `app/services/task_service.py`
   - 在 `resolve_image_with_priority()` 中集成 Gemini 图像生成
   - 支持作为优先图片源使用

4. `app/api/config_api.py`
   - 添加 `/api/gemini-image-models` - 获取模型列表
   - 添加 `/api/test-gemini-image` - 测试 API
   - 添加 `/api/gemini-image-styles` - 获取风格列表
   - 在 `/api/config` 中添加 Gemini 图像配置的读写

#### 前端

1. `templates/config.html`
   - 在 AI 绘图 tab 中添加完整的 Gemini 图像配置界面
   - 包含启用开关、API 配置、模型选择、风格选择、重试设置等

2. `static/js/pages/config/config-manager.js`
   - 添加 Gemini 图像配置的加载和保存逻辑
   - 添加 `applyGeminiImageSettings()` 方法
   - 添加 `collectGeminiImageSettings()` 方法

3. `static/js/pages/config/main.js`
   - 添加 `handleLoadGeminiImageModels()` - 加载模型列表
   - 添加 `handleTestGeminiImage()` - 测试 API 连接

4. `static/js/common/api.js`
   - 添加 `testGeminiImage()` API 方法
   - 添加 `getGeminiImageModels()` API 方法
   - 添加 `getGeminiImageStyles()` API 方法

## 配置说明

### JSON 配置结构

```json
{
  "gemini_image_settings": {
    "enabled": true,
    "api_key": "",  // 留空则使用通用 Gemini API Key
    "base_url": "",  // 留空则使用通用 Gemini Base URL
    "model": "imagen-3.0-generate-001",
    "style": "realistic",
    "custom_prefix": "",  // 自定义提示词前缀
    "custom_suffix": "",  // 自定义提示词后缀
    "max_retries": 3,  // 重试次数
    "timeout": 30  // 超时时间（秒）
  }
}
```

### 图片源优先级

在 `image_source_priority` 中添加 `"gemini_image"`：

```json
{
  "image_source_priority": [
    "gemini_image",  // 新增
    "comfyui",
    "user_uploaded",
    "pexels",
    "unsplash",
    "pixabay",
    "local"
  ]
}
```

## 使用流程

### 1. 配置 Gemini 图像生成

1. 进入 **配置页面** → **AI 绘图** tab
2. 滚动到 **Gemini 图像生成** 区域
3. 配置以下内容：
   - **启用开关**：启用 Gemini 图像生成
   - **API Key**：可留空使用通用 API Key，或单独配置
   - **Base URL**：可留空使用通用配置
   - **模型选择**：点击"加载模型列表"获取可用模型
   - **默认风格**：选择 8 种预设风格之一
   - **自定义提示词**：可选，添加前缀和后缀
   - **重试次数**：建议 3 次
   - **超时时间**：建议 30 秒

4. 点击 **测试生成** 按钮测试 API 连接
5. 点击 **保存配置**

### 2. 调整图片源优先级

1. 进入 **配置页面** → **高级设置** tab
2. 在 **图片源优先级** 中拖动 `Gemini 图像生成` 到合适位置
3. 建议放在 ComfyUI 之前或之后，作为备用方案

### 3. 生成文章

1. 进入 **写作页面**
2. 输入主题并配置参数
3. 系统会按照优先级使用 Gemini 图像生成
4. 如果失败会自动重试，超过重试次数后降级到下一个图片源

## 工作原理

### 图像生成流程

```
用户配置 Gemini 图像生成
  ↓
生成文章时，按优先级尝试图片源
  ↓
轮到 Gemini 图像生成
  ↓
1. 从段落提取提示词（由 Gemini 文本模型生成）
2. 应用选定的风格预设
3. 添加自定义前缀和后缀
4. 调用 Imagen API 生成图片
5. 如果失败，重试（最多 3 次）
6. 如果全部失败，降级到下一个图片源
  ↓
生成成功 → 保存到 output/gemini_images/
```

### 提示词构建

```python
最终提示词 = 自定义前缀 + 风格前缀 + 用户提示词 + 风格后缀 + 自定义后缀
```

例如：
- 用户提示词：`一个现代化的办公室`
- 选择风格：`写实摄影`
- 自定义前缀：`4K ultra HD, `
- 最终提示词：
  ```
  4K ultra HD, Highly detailed realistic photography, natural lighting, sharp focus, professional camera, 一个现代化的办公室, photorealistic, 8k resolution, high quality
  ```

## API 端点

### 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/gemini-image-models` | GET | 获取可用的 Imagen 模型列表 |
| `/api/test-gemini-image` | POST | 测试 API 连接，生成测试图片 |
| `/api/gemini-image-styles` | GET | 获取风格预设列表 |

### 请求示例

#### 测试 API

```bash
POST /api/test-gemini-image
Content-Type: application/json

{
  "api_key": "your-api-key",
  "base_url": "https://generativelanguage.googleapis.com",
  "model": "imagen-3.0-generate-001"
}
```

#### 响应

```json
{
  "success": true,
  "message": "Gemini 图像生成 API 工作正常",
  "image_path": "output/gemini_images/gemini_20251024120000_abc123.png"
}
```

## 优势特点

### 与 ComfyUI 对比

| 特性 | Gemini 图像生成 | ComfyUI |
|------|----------------|---------|
| **部署方式** | 云端，无需本地安装 | 需要本地运行 |
| **硬件要求** | 无需 GPU | 需要强大的 GPU |
| **速度** | 较快（取决于 API） | 取决于本地硬件 |
| **配置复杂度** | 简单，只需 API Key | 需要配置 workflow |
| **成本** | 按 API 调用付费 | 免费但需硬件投资 |
| **可用性** | 需要网络连接 | 完全离线 |
| **质量** | Google Imagen 高质量 | 取决于模型选择 |

### 最佳实践

1. **优先级设置**
   ```json
   [
     "user_uploaded",     // 优先使用用户上传
     "gemini_image",      // 云端 AI 生成
     "comfyui",           // 本地 AI 生成（备用）
     "pexels",            // 免费图库
     "unsplash",
     "pixabay",
     "local"
   ]
   ```

2. **重试策略**
   - 快速主题（新闻、简讯）：1-2 次重试
   - 重要内容（营销、宣传）：3-5 次重试

3. **风格选择建议**
   - 新闻文章 → 写实摄影
   - 科技博客 → 极简主义 / 赛博朋克
   - 营销内容 → 商业配图
   - 儿童内容 → 插画风格 / 水彩画
   - 游戏相关 → 动漫风格 / 奇幻风格

## 故障排除

### 常见问题

1. **API Key 无效**
   - 检查是否正确配置了 Gemini API Key
   - 确认 API Key 有图像生成权限
   - 尝试使用"测试生成"按钮验证

2. **请求超时**
   - 增加超时时间（建议 30-60 秒）
   - 检查网络连接
   - 使用自定义 Base URL（代理）

3. **生成失败**
   - 查看控制台日志了解具体错误
   - 确认提示词符合 API 限制
   - 检查是否触发了内容安全过滤

4. **模型列表加载失败**
   - 确认 API Key 配置正确
   - 检查 Base URL 是否可访问
   - 尝试使用默认模型

## 性能优化

1. **并发控制**：Gemini 图像生成不占用本地资源，可以与其他任务并行
2. **缓存机制**：生成的图片保存在 `output/gemini_images/` 目录
3. **降级策略**：失败后自动切换到其他图片源，确保文章生成流程不中断

## 未来扩展

可能的改进方向：

1. 支持更多宽高比选项（当前默认 16:9）
2. 图片缓存和复用机制
3. 批量生成优化
4. 更多风格预设
5. 图片质量和尺寸可配置

## 总结

Gemini 图像生成功能为系统提供了强大的云端 AI 绘图能力，与现有的 ComfyUI 本地生成和图片库下载形成完美互补。用户可以根据需求灵活选择图片来源，确保文章配图的质量和可用性。
