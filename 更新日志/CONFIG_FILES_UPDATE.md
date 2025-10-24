# 配置文件更新说明

## 更新时间
2025-10-24

## 更新的文件

### 1. config.example.json ✅

**添加的配置项：**

#### gemini_image_settings (新增)
```json
"gemini_image_settings": {
  "enabled": false,           // 默认禁用，需要用户确认后启用
  "api_key": "",             // 独立的 API Key（留空则使用通用 gemini_api_key）
  "base_url": "",            // 独立的 Base URL（留空则使用通用 gemini_base_url）
  "model": "gemini-2.5-flash-image-preview",  // 推荐的图像生成模型
  "style": "realistic",      // 默认风格：写实摄影
  "custom_prefix": "",       // 自定义提示词前缀
  "custom_suffix": "",       // 自定义提示词后缀
  "max_retries": 3,         // 重试次数
  "timeout": 30             // 超时时间（秒）
}
```

#### image_source_priority 更新
```json
"image_source_priority": [
  "user_uploaded",   // 用户上传（优先级最高）
  "comfyui",        // ComfyUI 本地生成
  "gemini_image",   // Gemini 图像生成（新增）
  "pexels",         // Pexels API
  "unsplash",       // Unsplash API
  "pixabay",        // Pixabay API
  "local"           // 本地图库
]
```

### 2. config.json ✅

**修复的配置项：**

#### gemini_image_settings.api_key
- **问题：** 缺少 `api_key` 字段，导致配置不完整
- **修复：** 添加了 `"api_key": ""` 字段
- **效果：** 现在可以正确保存和使用独立的 API Key

**修复前：**
```json
"gemini_image_settings": {
  "enabled": true,
  "base_url": "https://ljl1022.zeabur.app",
  "model": "gemini-2.5-flash-image-preview",
  // 缺少 api_key 字段 ❌
  ...
}
```

**修复后：**
```json
"gemini_image_settings": {
  "enabled": true,
  "api_key": "",  // ✅ 添加了 api_key 字段
  "base_url": "https://ljl1022.zeabur.app",
  "model": "gemini-2.5-flash-image-preview",
  ...
}
```

## 配置字段说明

### gemini_image_settings 完整字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | boolean | `false` | 是否启用 Gemini 图像生成 |
| `api_key` | string | `""` | 独立的 API Key（留空则使用通用配置） |
| `base_url` | string | `""` | 独立的 Base URL（留空则使用通用配置） |
| `model` | string | `"gemini-2.5-flash-image-preview"` | 使用的模型 |
| `style` | string | `"realistic"` | 默认风格（可选：realistic, illustration, anime 等） |
| `custom_prefix` | string | `""` | 自定义提示词前缀 |
| `custom_suffix` | string | `""` | 自定义提示词后缀 |
| `max_retries` | number | `3` | 失败重试次数 |
| `timeout` | number | `30` | 请求超时时间（秒） |

### 配置回退逻辑

**API Key 回退：**
1. 首先检查 `gemini_image_settings.api_key`
2. 如果为空，使用 `gemini_api_key`（通用配置）
3. 如果仍为空，报错提示用户配置

**Base URL 回退：**
1. 首先检查 `gemini_image_settings.base_url`
2. 如果为空，使用 `gemini_base_url`（通用配置）
3. 如果仍为空，使用默认值 `https://generativelanguage.googleapis.com`

## 配置示例

### 示例 1: 共用配置（推荐）

```json
{
  "gemini_api_key": "YOUR_REAL_API_KEY",
  "gemini_base_url": "https://api.dashen.wang",
  "gemini_image_settings": {
    "enabled": true,
    "api_key": "",        // 留空，使用通用 API Key
    "base_url": "",       // 留空，使用通用 Base URL
    "model": "gemini-2.5-flash-image-preview",
    "style": "realistic",
    "max_retries": 3,
    "timeout": 30
  }
}
```

### 示例 2: 独立配置

```json
{
  "gemini_api_key": "MAIN_MODEL_API_KEY",
  "gemini_base_url": "https://generativelanguage.googleapis.com",
  "gemini_image_settings": {
    "enabled": true,
    "api_key": "IMAGE_SPECIFIC_API_KEY",     // 使用独立的 API Key
    "base_url": "https://image-proxy.com",   // 使用独立的代理服务
    "model": "gemini-2.5-flash-image-preview",
    "style": "realistic",
    "max_retries": 3,
    "timeout": 30
  }
}
```

### 示例 3: 部分独立配置

```json
{
  "gemini_api_key": "YOUR_API_KEY",
  "gemini_base_url": "https://api.dashen.wang",
  "gemini_image_settings": {
    "enabled": true,
    "api_key": "",                            // 使用通用 API Key
    "base_url": "https://image-proxy.com",    // 使用独立的代理服务
    "model": "gemini-2.5-flash-image-preview",
    "style": "realistic",
    "max_retries": 3,
    "timeout": 30
  }
}
```

## 迁移指南

如果你的 `config.json` 是旧版本（没有 `gemini_image_settings` 或缺少字段），请按以下步骤更新：

### 步骤 1: 备份现有配置
```bash
copy config.json config.json.backup
```

### 步骤 2: 添加缺失字段

手动编辑 `config.json`，或者直接在 Web 界面的配置页面保存一次配置，系统会自动补全所有字段。

### 步骤 3: 验证配置

重启应用后，在配置页面检查：
- ✅ Gemini 图像生成部分是否正确显示
- ✅ API Key 和 Base URL 的 placeholder 提示是否正确
- ✅ 保存配置后刷新页面，独立配置是否保留

## 常见问题

### Q: 为什么 api_key 字段是空字符串？
**A:** 空字符串表示"留空"，系统会自动使用通用的 `gemini_api_key`。这是推荐的配置方式，避免重复配置。

### Q: 如何配置独立的 API Key？
**A:**
1. 在 Web 界面的"AI 绘图"标签页
2. 在 Gemini 图像生成部分填写独立的 API Key
3. 保存配置
4. 刷新页面验证（应该显示"已设置独立 API Key"）

### Q: 我之前配置的独立 Base URL 为什么丢失了？
**A:** 这是因为旧版本缺少 `api_key` 字段导致的。更新配置文件后，重新在 Web 界面配置一次即可。

### Q: 可以只配置独立的 Base URL，不配置独立的 API Key 吗？
**A:** 可以！你可以：
- `api_key` 留空（使用通用配置）
- `base_url` 填写独立的代理服务地址

## 相关文档

- [GEMINI_IMAGE_CONFIG_FIX.md](./GEMINI_IMAGE_CONFIG_FIX.md) - 配置功能修复说明
- [GEMINI_IMAGE_API_KEY_SAVE_FIX.md](./GEMINI_IMAGE_API_KEY_SAVE_FIX.md) - API Key 保存问题修复
- [GEMINI_IMAGE_TEST_FIX.md](./GEMINI_IMAGE_TEST_FIX.md) - 测试功能修复说明

## 完成状态

- ✅ config.example.json 已更新
- ✅ config.json 已修复（添加了缺失的 api_key 字段）
- ✅ 文档编写完成
