# Gemini 图像 API Key 独立保存问题修复

## 修复时间
2025-10-24

## 问题描述

用户报告：
> Gemini 生图单独设置的 api key 会继承主模型的 api key，没有独立保存。每次刷新完界面测试的时候都会用主模型的 api key，但是 api base url 是正确的。

**问题根源：**
1. 后端保存配置时，如果前端没有传入新的 API Key（输入框为空），旧的独立 API Key 会丢失
2. 后端返回配置时，`gemini_image_api_key_set` 字段逻辑有误，会把主模型的 API Key 也算进去
3. 前端显示逻辑无法区分独立配置和回退配置

## 修复内容

### 1. 后端保存逻辑修复 ✅

**文件: `app/api/config_api.py`** (第 105-120 行)

#### 问题
原来的代码直接使用前端传来的配置，不保留旧的 API Key：
```python
# 旧代码（有问题）
gemini_image_settings_payload = new_config.get('gemini_image_settings')
if gemini_image_settings_payload is None:
    gemini_image_settings_payload = old_config.get('gemini_image_settings', {})
final_config['gemini_image_settings'] = gemini_image_settings_payload
```

#### 修复
现在会合并新旧配置，特别处理 API Key 和 Base URL：
```python
# 新代码（已修复）
gemini_image_settings_payload = new_config.get('gemini_image_settings', {})
old_gemini_image_settings = old_config.get('gemini_image_settings', {})

# 合并新旧配置，保留旧的 API Key 和 Base URL（如果新配置中没有提供）
merged_gemini_image_settings = {**old_gemini_image_settings, **gemini_image_settings_payload}

# 特殊处理 API Key：只有在新配置中明确提供了才覆盖，否则保留旧值
if 'api_key' not in gemini_image_settings_payload and 'api_key' in old_gemini_image_settings:
    merged_gemini_image_settings['api_key'] = old_gemini_image_settings['api_key']

# 特殊处理 Base URL：只有在新配置中明确提供了才覆盖，否则保留旧值
if 'base_url' not in gemini_image_settings_payload and 'base_url' in old_gemini_image_settings:
    merged_gemini_image_settings['base_url'] = old_gemini_image_settings['base_url']

final_config['gemini_image_settings'] = merged_gemini_image_settings
```

### 2. 后端状态字段修复 ✅

**文件: `app/api/config_api.py`** (第 47-55 行)

#### 问题
`gemini_image_api_key_set` 使用了包含回退值的配置，无法区分独立配置：
```python
# 旧代码（有问题）
'gemini_image_api_key_set': bool(get_gemini_image_settings(config).get('api_key'))
```

#### 修复
现在直接检查原始的独立配置：
```python
# 新代码（已修复）
'gemini_image_settings': get_gemini_image_settings(config),
# 检查是否配置了独立的 Gemini 图像 API Key（不包括回退的主模型 API Key）
'gemini_image_api_key_set': bool(config.get('gemini_image_settings', {}).get('api_key')),
# 检查是否配置了独立的 Gemini 图像 Base URL（不包括回退的主模型 Base URL）
'gemini_image_base_url_set': bool(config.get('gemini_image_settings', {}).get('base_url'))
```

### 3. 前端显示逻辑修复 ✅

**文件: `static/js/pages/config/config-manager.js`**

#### 修改点 1: 传递状态字段 (第 118-122 行)
```javascript
// Gemini 图像生成配置
this.applyGeminiImageSettings(
    config.gemini_image_settings,
    config.gemini_image_api_key_set,
    config.gemini_image_base_url_set  // 新增参数
);
```

#### 修改点 2: 更新 applyGeminiImageSettings 函数 (第 154-192 行)

**函数签名更新：**
```javascript
applyGeminiImageSettings(settings = {}, apiKeySet = false, baseUrlSet = false)
```

**Base URL 显示逻辑：**
```javascript
// Base URL 显示逻辑
// 如果有独立配置，显示独立配置的值；否则留空（让 placeholder 显示提示）
if (baseUrlSet && merged.base_url) {
    elements.geminiImageBaseUrl.value = merged.base_url;
} else {
    elements.geminiImageBaseUrl.value = '';
}

// Base URL placeholder 显示逻辑
if (baseUrlSet) {
    elements.geminiImageBaseUrl.placeholder = '已设置独立 Base URL（如需更换请重新输入）';
} else if (this.currentConfig && this.currentConfig.gemini_base_url) {
    elements.geminiImageBaseUrl.placeholder = `留空则使用通用配置（当前：${this.currentConfig.gemini_base_url}）`;
} else {
    elements.geminiImageBaseUrl.placeholder = '留空则使用通用 Gemini Base URL';
}
```

## 修复效果

### 修复前的问题流程
1. 用户配置独立的 Gemini 图像 API Key
2. 保存配置 ✅
3. 刷新页面
4. 输入框显示 placeholder "已设置独立 API Key"（但实际已丢失）
5. 修改其他配置并保存
6. **独立 API Key 丢失** ❌ - 回退到主模型的 API Key

### 修复后的正确流程
1. 用户配置独立的 Gemini 图像 API Key
2. 保存配置 ✅
3. 刷新页面
4. 输入框显示 placeholder "已设置独立 API Key" ✅
5. 修改其他配置并保存
6. **独立 API Key 保留** ✅ - 继续使用独立的 API Key

## 配置状态说明

### API Key 状态显示

| 场景 | Placeholder 提示 | 输入框值 |
|------|-----------------|---------|
| 已配置独立 API Key | "已设置独立 API Key（如需更换请重新输入）" | 空 |
| 未配置独立，但已配置通用 | "留空则使用通用 Gemini API Key（已配置）" | 空 |
| 未配置独立，也未配置通用 | "留空则使用通用 Gemini API Key（未配置）" | 空 |

### Base URL 状态显示

| 场景 | Placeholder 提示 | 输入框值 |
|------|-----------------|---------|
| 已配置独立 Base URL | "已设置独立 Base URL（如需更换请重新输入）" | 独立的 URL |
| 未配置独立，但已配置通用 | "留空则使用通用配置（当前：https://xxx）" | 空 |
| 未配置独立，也未配置通用 | "留空则使用通用 Gemini Base URL" | 空 |

## 测试步骤

### 测试 1: 独立配置保存
1. 在"AI 绘图"标签页配置独立的 API Key 和 Base URL
2. 保存配置
3. 刷新页面
4. ✅ 输入框应该显示独立的 Base URL
5. ✅ Placeholder 应该显示"已设置独立 API Key"
6. 修改其他配置并保存
7. 刷新页面
8. ✅ 独立配置应该保留

### 测试 2: 共用配置
1. 在"必需配置"标签页配置 Gemini API Key 和 Base URL
2. 在"AI 绘图"标签页不配置（留空）
3. 保存配置
4. 刷新页面
5. ✅ Placeholder 应该显示"留空则使用通用配置（当前：xxx）"
6. 测试图像生成
7. ✅ 应该使用主模型的配置

### 测试 3: 从共用切换到独立
1. 先使用共用配置（留空）
2. 保存配置
3. 然后配置独立的 API Key 和 Base URL
4. 保存配置
5. 刷新页面
6. ✅ 应该显示独立配置

### 测试 4: 从独立切换回共用
1. 先配置独立的 API Key 和 Base URL
2. 保存配置
3. 想要切换回共用配置？
4. **重要：** 目前需要手动清空输入框后保存
5. **改进建议：** 可以添加一个"清除独立配置"按钮

## 已知限制和改进建议

### 限制 1: 无法直接清除独立配置
**问题：** 如果用户配置了独立的 API Key，想要切换回使用通用配置，需要知道输入框虽然是空的，但独立配置还存在。

**解决方案：**
- 方案 A（简单）：在文档中说明，要切换回共用配置，需要在输入框中输入一个空格然后删除，触发保存空值
- 方案 B（推荐）：添加一个"清除独立配置"按钮，点击后清空独立的 API Key 和 Base URL

### 限制 2: API Key 输入框不显示值
**问题：** 为了安全，API Key 输入框不显示已保存的值，只显示 placeholder。

**优点：** 安全性好
**缺点：** 用户不知道当前配置的值是什么

**改进建议：** 可以添加一个"显示配置信息"按钮，点击后显示当前使用的 API Key 的前几位和后几位（如 `AIza...xyz123`）

## 修改的文件清单

1. `app/api/config_api.py` - 后端配置保存和返回逻辑
2. `static/js/pages/config/config-manager.js` - 前端配置管理器

## 相关文档

- [GEMINI_IMAGE_CONFIG_FIX.md](./GEMINI_IMAGE_CONFIG_FIX.md) - Gemini 图像 API 配置修复说明
- [GEMINI_IMAGE_TEST_FIX.md](./GEMINI_IMAGE_TEST_FIX.md) - 测试功能修复说明

## 完成状态

- ✅ 后端保存逻辑修复
- ✅ 后端状态字段修复
- ✅ 前端显示逻辑修复
- ✅ 文档编写完成
- 🔄 建议添加"清除独立配置"按钮（可选）
