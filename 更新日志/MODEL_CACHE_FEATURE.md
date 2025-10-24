# 模型列表缓存功能

## 功能概述

实现了模型列表的本地缓存机制，避免每次页面加载都需要从 API 获取模型列表，提升用户体验并减少不必要的 API 调用。

## 设计思想

> 用户建议：不管任何模型，主模型也好，图像生成模型也好，当用户刷新列表的时候，把模型列表缓存到一个文件，一直到下次用户点击刷新列表的时候再继续缓存。

## 缓存策略

### 页面加载时
- **优先从缓存读取**模型列表
- 如果有缓存，直接显示完整的模型列表（无需等待 API 调用）
- 如果没有缓存，只显示当前保存的模型

### 用户点击"刷新列表"时
- **强制从 API 获取**最新的模型列表
- 更新本地缓存文件
- 显示最新的模型列表

### 优势
1. ✅ **快速加载** - 页面刷新时立即显示完整的模型列表
2. ✅ **离线友好** - 即使暂时无法连接 API，也能看到之前缓存的模型
3. ✅ **减少 API 调用** - 只在用户主动刷新时才调用 API
4. ✅ **用户控制** - 用户决定何时更新模型列表

## 缓存文件结构

### 文件位置
```
项目根目录/models_cache.json
```

### 文件格式
```json
{
  "gemini_models": {
    "last_updated": "2025-10-24T08:15:30.123456",
    "models": [
      {
        "name": "gemini-2.5-pro",
        "display_name": "Gemini 2.5 Pro",
        "description": "..."
      },
      {
        "name": "gemini-2.0-flash",
        "display_name": "Gemini 2.0 Flash",
        "description": "..."
      }
    ]
  },
  "gemini_image_models": {
    "last_updated": "2025-10-24T08:15:35.789012",
    "models": [
      {
        "id": "nano banana",
        "name": "Nano Banana Model",
        "description": "..."
      },
      {
        "id": "gemini-2.5-flash-image-preview",
        "name": "Gemini 2.5 Flash Image Preview",
        "description": "..."
      }
    ]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `last_updated` | string (ISO 8601) | 最后更新时间 |
| `models` | array | 模型列表 |

## 实现细节

### 后端实现

#### 1. 缓存管理模块

**文件：** `app/utils/models_cache.py`

**主要函数：**
```python
def load_cache()
    """加载缓存数据"""

def save_cache(cache_data)
    """保存缓存数据"""

def update_gemini_models_cache(models)
    """更新 Gemini 主模型缓存"""

def update_gemini_image_models_cache(models)
    """更新 Gemini 图像模型缓存"""

def get_gemini_models_cache()
    """获取 Gemini 主模型缓存"""

def get_gemini_image_models_cache()
    """获取 Gemini 图像模型缓存"""

def clear_cache()
    """清空所有缓存"""
```

#### 2. API 端点修改

**文件：** `app/api/config_api.py`

##### `/models` 端点
```python
@config_api_bp.route('/models')
def get_models():
    """获取可用的 Gemini 模型列表（支持缓存）"""
    # 检查是否强制刷新
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'

    # 如果不是强制刷新，先尝试从缓存读取
    if not force_refresh:
        cache_data = get_gemini_models_cache()
        if cache_data['models']:
            return jsonify({
                'models': cache_data['models'],
                'from_cache': True,
                'last_updated': cache_data['last_updated']
            })

    # 从 API 获取最新的模型列表
    model_list = get_available_models(api_key, base_url)

    # 更新缓存
    update_gemini_models_cache(model_list)

    return jsonify({
        'models': model_list,
        'from_cache': False
    })
```

##### `/gemini-image-models` 端点
```python
@config_api_bp.route('/gemini-image-models', methods=['GET'])
def get_gemini_image_model_list():
    """获取 Gemini 图像生成模型列表（支持缓存）"""
    # 类似的实现...
```

**请求参数：**
- `refresh=true` - 强制从 API 刷新
- `refresh=false` 或不传 - 从缓存读取（默认）

**响应格式：**
```json
{
  "models": [...],
  "from_cache": true,
  "last_updated": "2025-10-24T08:15:30.123456"
}
```

### 前端实现

#### 1. API 调用修改

**文件：** `static/js/common/api.js`

```javascript
async getModels(forceRefresh = false) {
    return this.get('/models', { refresh: forceRefresh });
}

async getGeminiImageModels(forceRefresh = false) {
    return this.get('/gemini-image-models', { refresh: forceRefresh });
}
```

#### 2. 主模型列表加载

**文件：** `static/js/pages/config/config-manager.js`

```javascript
async loadModels(preferredModel = null, forceRefresh = false) {
    // 从缓存或 API 获取模型列表
    const data = await api.getModels(forceRefresh);

    // 填充下拉框
    elements.defaultModel.innerHTML = '';
    data.models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.name;
        option.textContent = model.display_name || model.name;
        elements.defaultModel.appendChild(option);
    });

    // 显示缓存状态
    if (data.from_cache) {
        console.log(`✓ 主模型列表已从缓存加载 (${data.models.length} 个模型, 上次更新: ${data.last_updated})`);
    }
}
```

#### 3. Gemini 图像模型初始化

**文件：** `static/js/pages/config/main.js`

```javascript
async initGeminiImageModelSelect(config) {
    const modelSelect = document.getElementById('geminiImageModel');
    const currentModel = config.gemini_image_settings?.model;

    try {
        // 从缓存加载模型列表（不强制刷新）
        const data = await api.getGeminiImageModels(false);

        if (data.models && data.models.length > 0) {
            // 有缓存数据，加载完整的模型列表
            modelSelect.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });

            modelSelect.value = currentModel;

            if (data.from_cache) {
                console.log(`✓ Gemini 图像模型已从缓存加载 (${data.models.length} 个模型)`);
            }
        }
    } catch (error) {
        // 加载失败，只显示当前模型
        console.warn('加载缓存失败:', error);
    }
}
```

#### 4. "刷新列表"按钮

**文件：** `static/js/pages/config/main.js`

```javascript
async handleLoadGeminiImageModels() {
    // 强制刷新，从 API 获取最新的模型列表
    const data = await api.getGeminiImageModels(true);

    // 更新下拉列表...
}
```

## 使用流程

### 首次使用
1. 打开配置页面
2. 模型下拉框只显示当前保存的模型
3. 点击"刷新列表"按钮
4. 从 API 获取完整的模型列表
5. **自动保存到缓存文件** `models_cache.json`
6. 显示完整的模型列表

### 后续使用
1. 刷新页面或重新打开配置页面
2. **自动从缓存加载**完整的模型列表 ✅
3. 无需等待 API 调用
4. 如果想更新列表，点击"刷新列表"

### 控制台日志示例

**从缓存加载：**
```
✓ 主模型列表已从缓存加载 (15 个模型, 上次更新: 2025-10-24T08:15:30.123456)
✓ Gemini 图像模型已从缓存加载 (8 个模型, 上次更新: 2025-10-24T08:15:35.789012)
```

**强制刷新：**
```
🔄 从 API 获取 Gemini 主模型列表...
✓ Gemini 主模型列表已缓存 (15 个模型)
```

## 缓存管理

### 自动管理
- 缓存文件由系统自动创建和更新
- 用户无需手动管理

### 手动清除缓存
如果需要清除缓存，可以：
1. 删除 `models_cache.json` 文件
2. 或调用后端 API（如果实现了清除端点）

### 缓存失效
缓存不会自动过期，只在以下情况更新：
- 用户点击"刷新列表"按钮
- 手动删除缓存文件

## 版本控制

缓存文件已添加到 `.gitignore`：
```gitignore
# 配置和缓存文件
config.json
models_cache.json
```

## 性能对比

### 修复前（无缓存）
```
1. 用户打开配置页面
2. 主模型下拉框：空 (需要点击某个按钮加载)
3. Gemini 图像模型下拉框：只显示1个选项
4. 用户点击"刷新列表"
5. 调用 API (可能需要 1-3 秒)
6. 显示完整列表
7. 用户刷新页面
8. 重复步骤 2-6 ❌
```

### 修复后（有缓存）
```
1. 用户打开配置页面
2. 主模型下拉框：立即显示完整列表 (从缓存，<100ms) ✅
3. Gemini 图像模型下拉框：立即显示完整列表 ✅
4. 用户可以直接使用，无需等待
5. 如需更新，点击"刷新列表"
6. 用户刷新页面
7. 立即显示完整列表（仍然来自缓存）✅
```

## 错误处理

### 缓存文件损坏
```python
try:
    with open(cache_path, 'r', encoding='utf-8') as f:
        return json.load(f)
except Exception as e:
    print(f"加载模型缓存失败: {e}")
    # 返回空缓存
    return {'gemini_models': {...}, 'gemini_image_models': {...}}
```

### API 调用失败
- 如果有缓存，继续使用缓存
- 如果没有缓存，显示默认模型或错误提示

### 网络离线
- 完全依赖缓存
- 用户仍然可以看到之前缓存的模型列表

## 兼容性

### 向后兼容
- 如果缓存文件不存在，自动创建
- 旧版本升级后，首次使用时自动创建缓存

### 多环境
- 开发环境和生产环境各自维护独立的缓存
- 缓存文件不会被提交到版本控制

## 未来改进

### 可选的改进方向

1. **缓存过期时间**
   - 添加 TTL（Time To Live）机制
   - 例如：缓存7天后自动失效

2. **自动后台刷新**
   - 页面加载时在后台异步刷新缓存
   - 不影响用户体验

3. **缓存版本控制**
   - 添加缓存格式版本号
   - 支持平滑升级

4. **多缓存策略**
   - 按 API Key 分别缓存
   - 支持多个账号的模型列表

## 测试建议

### 测试步骤

1. **首次加载测试**
   ```
   - 删除 models_cache.json
   - 打开配置页面
   - 检查模型列表是否只显示当前保存的模型
   - 点击"刷新列表"
   - 检查 models_cache.json 是否创建
   - 检查模型列表是否显示完整
   ```

2. **缓存加载测试**
   ```
   - 确保 models_cache.json 存在
   - 刷新页面
   - 检查模型列表是否立即显示完整列表
   - 检查控制台日志是否显示"从缓存加载"
   ```

3. **强制刷新测试**
   ```
   - 点击"刷新列表"
   - 检查控制台日志是否显示"从 API 获取"
   - 检查 models_cache.json 是否更新（时间戳）
   ```

4. **网络故障测试**
   ```
   - 断开网络
   - 打开配置页面
   - 检查模型列表是否仍然显示（来自缓存）
   ```

5. **多模型类型测试**
   ```
   - 测试主模型列表
   - 测试 Gemini 图像模型列表
   - 检查两者是否独立缓存
   ```

## 修改的文件清单

### 新增文件
1. `models_cache.json` - 缓存文件（自动生成）
2. `app/utils/models_cache.py` - 缓存管理模块
3. `MODEL_CACHE_FEATURE.md` - 功能文档

### 修改文件
1. `app/api/config_api.py` - 添加缓存支持
2. `static/js/common/api.js` - 添加 forceRefresh 参数
3. `static/js/pages/config/config-manager.js` - 主模型列表使用缓存
4. `static/js/pages/config/main.js` - Gemini 图像模型使用缓存
5. `.gitignore` - 添加缓存文件

## 完成状态

- ✅ 后端缓存管理模块
- ✅ 后端 API 缓存支持
- ✅ 前端主模型列表缓存
- ✅ 前端 Gemini 图像模型缓存
- ✅ .gitignore 配置
- ✅ 功能文档

## 相关文档

- [GEMINI_IMAGE_MODEL_LIST_FIX.md](./GEMINI_IMAGE_MODEL_LIST_FIX.md) - 模型列表显示问题修复
- [GEMINI_IMAGE_CONFIG_FIX.md](./GEMINI_IMAGE_CONFIG_FIX.md) - Gemini 图像 API 配置修复
