# Gemini 图像生成代理服务使用指南

## 🎉 好消息！

你使用的代理服务（`https://api.dashen.wang`）**支持图像生成功能**！

根据测试日志，API 返回的响应包含了 base64 编码的图像数据，采用 Markdown 格式：
```
![Generated Image](data:image/png;base64,iVBORw0KGgo...)
```

## ✅ 已修复的问题

### 1. 图像数据提取 ✅

**问题：** 代码之前只检查纯 JSON 格式的图像数据，没有处理 Markdown 格式。

**修复：** 现在代码已更新，支持以下格式：
- Markdown 格式：`![...](data:image/...;base64,...)`
- 直接 base64：`{"image": "base64data"}`
- JSON 数组：`{"images": [{"data": "base64data"}]}`

### 2. 优先级列表 ✅

**问题：** 图片源优先级列表中缺少 "Gemini 图像生成" 选项。

**修复：** 已在优先级列表中添加，可以拖动排序。

## 🚀 使用步骤

### 1. 配置 Gemini 图像生成

1. **打开配置页面**
   ```
   配置页面 → AI 绘图 tab → 滚动到 "Gemini 图像生成"
   ```

2. **启用功能**
   - ✅ 勾选"启用 Gemini 图像生成"

3. **配置 API**
   - **API Key**: 留空（使用通用 Gemini API Key）或单独配置
   - **Base URL**: 留空或填写 `https://api.dashen.wang`
   - **模型**: 选择 `gemini-2.5-flash-image-preview` 或其他支持图像的模型

4. **选择风格**
   - 从 8 种预设风格中选择（推荐：写实摄影）
   - 或使用自定义提示词

5. **设置重试参数**
   - 重试次数：3 次（推荐）
   - 超时时间：30 秒（推荐）

6. **测试生成**
   - 点击"测试生成"按钮
   - 应该看到：✓ Gemini 图像生成 API 工作正常

7. **保存配置**

### 2. 调整优先级

1. **进入高级设置**
   ```
   配置页面 → 高级设置 tab
   ```

2. **拖动排序**
   ```
   推荐顺序：
   1. 用户上传
   2. Gemini 图像生成 ⭐（新增）
   3. ComfyUI
   4. Pexels API
   5. Unsplash API
   6. Pixabay API
   7. 本地图库
   ```

3. **保存配置**

### 3. 生成文章测试

1. **返回写作页面**
2. **输入主题**，例如：`人工智能的未来发展`
3. **启动生成**
4. **观察日志**，应该看到：
   ```
   尝试使用 Gemini 生成图像...
   使用模型: gemini-2.5-flash-image-preview
   ✓ 在响应中找到 Markdown 格式的图像数据
   ✓ Gemini 图像生成成功: output/gemini_images/...
   ```

## 📋 支持的模型

根据你的代理服务，以下模型可能支持图像生成：

### 推荐模型 ⭐
- `gemini-2.5-flash-image-preview` - 专门的图像生成预览模型
- `gemini-2.0-flash-exp` - 实验性多模态模型

### 其他可用模型
- `gemini-1.5-pro`
- `gemini-1.5-flash`

**建议：** 使用"刷新列表"按钮加载最新的可用模型。

## 🎨 风格预设

### 8 种预设风格

| 风格 | 适用场景 | 示例提示词前缀 |
|------|---------|--------------|
| **写实摄影** | 新闻、博客、通用 | Highly detailed realistic photography... |
| **插画风格** | 教育、儿童内容 | Beautiful illustration art... |
| **动漫风格** | 游戏、二次元 | Anime style artwork... |
| **赛博朋克** | 科技、未来主题 | Cyberpunk style, neon lights... |
| **商业配图** | 营销、演示文稿 | Professional business illustration... |
| **水彩画** | 艺术、优雅内容 | Watercolor painting style... |
| **极简主义** | 现代、简约设计 | Minimalist design, clean... |
| **奇幻风格** | 小说、创意内容 | Fantasy art, magical atmosphere... |

### 自定义提示词

**前缀示例：**
```
4K ultra HD, professional photography,
```

**后缀示例：**
```
, trending on artstation, award winning, masterpiece
```

## ⚙️ 推荐配置

### 配置文件示例

```json
{
  "gemini_image_settings": {
    "enabled": true,
    "api_key": "",  // 留空使用通用 Key
    "base_url": "https://api.dashen.wang",
    "model": "gemini-2.5-flash-image-preview",
    "style": "realistic",
    "custom_prefix": "",
    "custom_suffix": "",
    "max_retries": 3,
    "timeout": 30
  },
  "image_source_priority": [
    "user_uploaded",
    "gemini_image",  // ⭐ 新增，排在第二位
    "comfyui",
    "pexels",
    "unsplash",
    "pixabay",
    "local"
  ]
}
```

## 🔍 故障排查

### 问题：测试失败

**检查项：**
1. ✅ API Key 是否正确配置
2. ✅ Base URL 是否可访问
3. ✅ 模型名称是否支持图像生成
4. ✅ 网络连接是否正常

**解决方法：**
```
1. 点击"刷新列表"加载最新模型
2. 尝试不同的模型
3. 检查控制台日志了解详细错误
```

### 问题：生成图像失败

**常见原因：**
1. 提示词过长或包含敏感内容
2. API 配额用尽
3. 网络超时

**解决方法：**
```
1. 简化提示词
2. 增加超时时间（60 秒）
3. 增加重试次数（5 次）
4. 检查 API 配额
```

### 问题：图像质量不理想

**优化建议：**
1. 使用更具体的风格预设
2. 添加自定义提示词前后缀
3. 尝试不同的模型
4. 调整提示词描述

## 📊 性能对比

### Gemini 图像生成 vs ComfyUI

| 特性 | Gemini 图像生成 | ComfyUI |
|------|----------------|---------|
| **部署** | ☁️ 云端，无需安装 | 🖥️ 需要本地运行 |
| **硬件** | 无需 GPU | 需要强大 GPU |
| **速度** | 中等（网络延迟） | 快（本地处理） |
| **成本** | 按 API 调用计费 | 免费（硬件成本） |
| **质量** | Google Imagen 高质量 | 取决于模型选择 |
| **可用性** | 需要网络 | 完全离线 |
| **配置** | 简单 | 需要配置 workflow |

### 推荐场景

**使用 Gemini 图像生成：**
- ✅ 没有强大的本地 GPU
- ✅ 需要快速部署
- ✅ 偶尔使用，不频繁
- ✅ 需要高质量图像

**使用 ComfyUI：**
- ✅ 有强大的本地 GPU
- ✅ 频繁使用
- ✅ 需要完全控制
- ✅ 完全离线环境

## 🎯 最佳实践

### 1. 优先级设置

```
推荐顺序（按重要性）：
1. 用户上传          - 用户精心选择的图片
2. Gemini 图像生成   - 云端 AI 高质量生成
3. ComfyUI           - 本地 AI 备用方案
4. 图片 API          - 免费图库备用
5. 本地图库          - 离线备用
```

### 2. 重试策略

**根据内容类型调整：**
- 快速新闻：1-2 次重试，超时 20 秒
- 重要内容：3-5 次重试，超时 60 秒
- 批量生成：2-3 次重试，超时 30 秒

### 3. 风格选择

**内容类型匹配：**
- 新闻报道 → 写实摄影
- 科技文章 → 极简主义 / 赛博朋克
- 营销内容 → 商业配图
- 教育内容 → 插画风格
- 小说创作 → 奇幻风格 / 水彩画
- 游戏相关 → 动漫风格

## 📝 示例配置

### 场景 1：新闻网站

```json
{
  "gemini_image_settings": {
    "enabled": true,
    "model": "gemini-2.5-flash-image-preview",
    "style": "realistic",
    "max_retries": 2,
    "timeout": 20
  },
  "image_source_priority": [
    "gemini_image",
    "pexels",
    "unsplash"
  ]
}
```

### 场景 2：博客作者

```json
{
  "gemini_image_settings": {
    "enabled": true,
    "model": "gemini-2.5-flash-image-preview",
    "style": "illustration",
    "custom_suffix": ", trending on artstation",
    "max_retries": 3,
    "timeout": 30
  },
  "image_source_priority": [
    "user_uploaded",
    "gemini_image",
    "pixabay"
  ]
}
```

### 场景 3：重度使用者

```json
{
  "gemini_image_settings": {
    "enabled": true,
    "model": "gemini-2.5-flash-image-preview",
    "style": "realistic",
    "max_retries": 5,
    "timeout": 60
  },
  "image_source_priority": [
    "user_uploaded",
    "gemini_image",
    "comfyui",
    "pexels",
    "local"
  ]
}
```

## 🆘 获取帮助

如果遇到问题：

1. **查看控制台日志**
   - 详细的错误信息和调试输出

2. **检查生成的图片**
   - 位置：`output/gemini_images/`
   - 文件名格式：`gemini_YYYYMMDDHHMMSS_xxxxx.png`

3. **联系代理服务商**
   - 确认 API 配额和限制
   - 获取最新支持的模型列表
   - 了解特殊配置要求

## 🎊 总结

你的代理服务完美支持图像生成功能！现在你可以：

- ✅ 使用 Gemini 云端 AI 生成高质量图片
- ✅ 配合 8 种预设风格
- ✅ 自定义提示词优化效果
- ✅ 智能降级，确保总能获得配图
- ✅ 灵活的优先级管理

祝使用愉快！🚀
