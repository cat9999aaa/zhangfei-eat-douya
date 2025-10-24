# Gemini 图像 API 配置修复说明

## 修复时间
2025-10-24

## 修复内容

### 1. Gemini 图像 API 独立配置支持 ✅

#### 问题描述
之前 Gemini 图像生成功能虽然支持独立的 API Key 和 Base URL 配置，但没有实现回退逻辑，导致如果不配置独立的值就无法使用。

#### 修复方案
**文件: `app/config/loader.py`**

在 `get_gemini_image_settings()` 函数中添加了回退逻辑：

```python
# 如果没有配置独立的 API Key，尝试使用通用的 Gemini API Key
if not merged.get('api_key'):
    merged['api_key'] = config.get('gemini_api_key', '')

# 如果没有配置独立的 Base URL，尝试使用通用的 Gemini Base URL
if not merged.get('base_url'):
    merged['base_url'] = config.get('gemini_base_url', DEFAULT_GEMINI_IMAGE_CONFIG['base_url'])
```

#### 功能特性
- ✅ 支持独立配置 Gemini 图像生成的 API Key 和 Base URL
- ✅ 如果不配置独立值，自动使用"必需配置"标签页中的通用 Gemini 配置
- ✅ 灵活性：可以与文本生成共用配置，也可以使用不同的代理服务

### 2. 配置页面顺序优化 ✅

#### 问题描述
AI 绘图标签页中，摘要模型的配置在页面底部，不够显眼。

#### 修复方案
**文件: `templates/config.html`**

调整了配置卡片的顺序，现在 AI 绘图标签页的配置顺序为：
1. 基础设置（ComfyUI 服务连接）
2. **摘要模型** ⬆️ 提升到第二位
3. 生成参数（图片数量、风格模板等）
4. Gemini 图像生成

#### 优势
- 更符合配置流程：先配置模型，再配置生成参数
- 摘要模型对图片生成质量影响大，提升位置更便于用户注意

### 3. 前端用户体验改进 ✅

#### 改进 1: 更清晰的标签和帮助文本

**文件: `templates/config.html`**

- 将 API Key 和 Base URL 标签改为 "API Key（可选）" 和 "Base URL（可选）"
- 增强了帮助文本，明确说明留空时的回退行为：
  ```
  💡 留空将自动使用"必需配置"标签页中的 Gemini API Key，也可以单独配置专用的 API Key
  💡 留空将自动使用"必需配置"标签页中的 Gemini Base URL，也可以单独配置专用代理服务
  ```

#### 改进 2: 智能 Placeholder

**文件: `static/js/pages/config/config-manager.js`**

在 `applyGeminiImageSettings()` 方法中实现了智能 placeholder：

**API Key Placeholder:**
- 已设置独立 API Key: "已设置独立 API Key（如需更换请重新输入）"
- 未设置独立，但已配置通用: "留空则使用通用 Gemini API Key（已配置）"
- 未设置独立，也未配置通用: "留空则使用通用 Gemini API Key（未配置）"

**Base URL Placeholder:**
- 已设置独立 Base URL: "已设置独立 Base URL"
- 未设置独立，但已配置通用: "留空则使用通用配置（当前：https://xxx）"
- 未设置独立，也未配置通用: "留空则使用通用 Gemini Base URL"

## 使用指南

### 场景 1: 共用配置（推荐）
1. 在"必需配置"标签页配置 Gemini API Key 和 Base URL
2. 在"AI 绘图"标签页启用 Gemini 图像生成
3. API Key 和 Base URL 输入框留空即可

### 场景 2: 独立配置
1. 在"必需配置"标签页配置用于文本生成的 Gemini API
2. 在"AI 绘图"标签页配置专用的图像生成代理服务
3. 填写独立的 API Key 和 Base URL

## 注意事项

⚠️ **Gemini 图像生成功能说明**
- Google Gemini 官方 API 目前不直接支持图像生成
- 此功能需要使用支持 Imagen API 的代理服务
- 如果测试失败，建议使用 ComfyUI 本地生成或图片库 API

## 修改的文件清单

1. `app/config/loader.py` - 后端配置加载逻辑
2. `templates/config.html` - 配置页面 HTML
3. `static/js/pages/config/config-manager.js` - 前端配置管理器

## 测试建议

1. 测试共用配置模式
   - 配置通用 Gemini API
   - 不配置独立的图像 API
   - 验证图像生成是否使用通用配置

2. 测试独立配置模式
   - 配置独立的图像 API
   - 验证使用独立配置生成图像

3. 测试 UI 显示
   - 检查 placeholder 是否正确显示配置状态
   - 验证配置顺序是否符合预期

## 完成状态

- ✅ Gemini 图像 API 独立配置支持
- ✅ 配置页面顺序优化
- ✅ 前端用户体验改进
- ✅ 文档编写完成
