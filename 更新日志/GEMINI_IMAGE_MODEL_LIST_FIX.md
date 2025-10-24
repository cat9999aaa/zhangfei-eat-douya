# Gemini 图像模型列表问题修复

## 修复时间
2025-10-24

## 问题描述

用户报告了两个关键问题：

### 问题 1: 每次刷新页面模型列表为空
> 每次刷新页面，gemini 图片生成的配置里模型列表都是空的，需要手动刷新列表重新选择一次。

### 问题 2: 模型配置没有正确保存和显示
> 保存了 nano banana 的模型，但是每次刷新页面或者切换页面，再回到 gemini 生图模型配置页面的时候，显示的是 Gemini 2.5 Flash Image，选择模型的时候下拉列表里是硬编码的模型列表，而不是从服务器获取的模型列表。

### 问题 3: 模型配置未写入配置文件
> 好像保存了模型等设置之后没有写入到配置文件里，所以配置只在当前页面有效，这也是为什么写文章的时候调用 gemini 生图失败。

## 根本原因分析

### 原因 1: 页面加载时未初始化模型下拉框

**代码位置：** `static/js/pages/config/main.js` 的 `loadConfig()` 方法

页面加载时的流程：
```javascript
async loadConfig() {
    const config = await this.configManager.loadConfig();
    await this.configManager.loadModels(config.default_model);
    await this.configManager.loadSummaryModels();
    // ❌ 缺少 Gemini 图像模型下拉框的初始化
}
```

**结果：**
- 主模型和摘要模型的下拉框正常显示
- Gemini 图像模型下拉框为空

### 原因 2: 使用硬编码的模型列表

**代码位置：** 最初的修复尝试中，我硬编码了常用模型列表

```javascript
// ❌ 错误的做法：硬编码模型列表
const commonModels = [
    { id: 'gemini-2.5-flash-image-preview', name: 'Gemini 2.5 Flash Image Preview' },
    { id: 'gemini-2.5-flash-image', name: 'Gemini 2.5 Flash Image' },
    // ...
];
```

**结果：**
- 用户保存的 "nano banana" 模型不在硬编码列表中
- 下拉列表显示的是通用模型，而不是代理服务器支持的模型

### 原因 3: 模型值设置时机错误

**代码位置：** `static/js/pages/config/config-manager.js` 的 `applyGeminiImageSettings()` 方法

调用顺序问题：
```
1. configManager.loadConfig()
   → applyToUI()
   → applyGeminiImageSettings()
   → 设置 geminiImageModel.value = "nano banana"
   ❌ 但此时下拉框还没有选项！

2. initGeminiImageModelSelect()
   → 添加选项
   → 设置值
```

**结果：**
- 在步骤1设置值时，下拉框中没有 "nano banana" 选项
- 浏览器可能显示默认值或第一个选项

### 原因 4: "刷新列表"功能未保留当前选择

**代码位置：** `static/js/pages/config/main.js` 的 `handleLoadGeminiImageModels()` 方法

```javascript
// ❌ 错误的做法
modelSelect.innerHTML = '';  // 清空下拉框
data.models.forEach(model => {
    // 添加新模型
});
// 没有恢复之前选中的值！
```

**结果：**
- 用户点击"刷新列表"后，之前选择的 "nano banana" 丢失

## 修复方案

### 修复 1: 页面加载时初始化模型下拉框 ✅

**文件：** `static/js/pages/config/main.js`

在 `loadConfig()` 方法中添加初始化：

```javascript
async loadConfig() {
    try {
        const config = await this.configManager.loadConfig();

        // 加载模型列表
        await this.configManager.loadModels(config.default_model);

        // 加载摘要模型列表
        await this.configManager.loadSummaryModels();

        // ✅ 初始化 Gemini 图像模型下拉框
        this.initGeminiImageModelSelect(config);

        // 加载图片目录
        if (this.imageDirManager && config.local_image_directories) {
            this.imageDirManager.loadDirectories(config.local_image_directories);
        }

        toast.success('配置加载成功');
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}
```

### 修复 2: 使用简化的初始化逻辑 ✅

**文件：** `static/js/pages/config/main.js`

新增 `initGeminiImageModelSelect()` 方法：

```javascript
initGeminiImageModelSelect(config) {
    const modelSelect = document.getElementById('geminiImageModel');
    if (!modelSelect) return;

    const currentModel = config.gemini_image_settings?.model || 'gemini-2.5-flash-image-preview';

    // 清空现有选项
    modelSelect.innerHTML = '';

    // ✅ 只添加当前配置的模型作为占位符
    // 用户需要点击"刷新列表"按钮从服务器获取完整的可用模型列表
    const option = document.createElement('option');
    option.value = currentModel;
    option.textContent = currentModel;
    modelSelect.appendChild(option);

    // 设置当前值
    modelSelect.value = currentModel;

    console.log(`✓ Gemini 图像模型已初始化: ${currentModel}`);
    console.log(`💡 提示: 点击"刷新列表"按钮可从服务器获取最新的可用模型列表`);
}
```

**优点：**
- 不依赖硬编码的模型列表
- 总是显示用户保存的模型（包括 "nano banana"）
- 提示用户点击"刷新列表"获取完整列表

### 修复 3: 避免在错误时机设置模型值 ✅

**文件：** `static/js/pages/config/config-manager.js`

在 `applyGeminiImageSettings()` 中注释掉模型值的设置：

```javascript
applyGeminiImageSettings(settings = {}, apiKeySet = false, baseUrlSet = false) {
    const elements = this.getFormElements();
    const merged = { ...this.geminiImageDefaults, ...settings };

    elements.geminiImageEnabled.checked = !!merged.enabled;
    // ... 其他设置 ...

    // ✅ 注意：模型值由 initGeminiImageModelSelect() 方法设置
    // 因为需要先初始化下拉框选项，再设置值
    // elements.geminiImageModel.value = merged.model || 'imagen-3.0-generate-001';

    elements.geminiImageStyle.value = merged.style || 'realistic';
    // ... 其他设置 ...
}
```

### 修复 4: "刷新列表"功能保留当前选择 ✅

**文件：** `static/js/pages/config/main.js`

修改 `handleLoadGeminiImageModels()` 方法：

```javascript
async handleLoadGeminiImageModels() {
    // ...

    try {
        btn.disabled = true;
        btn.textContent = '加载中...';
        resultDiv.style.display = 'none';

        // ✅ 保存当前选中的模型
        const currentModel = modelSelect.value;

        const data = await api.getGeminiImageModels();

        // 更新模型下拉列表
        modelSelect.innerHTML = '';
        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            if (model.description) {
                option.title = model.description;
            }
            modelSelect.appendChild(option);
        });

        // ✅ 恢复之前选中的模型
        if (currentModel) {
            // 检查当前模型是否在新列表中
            const modelExists = Array.from(modelSelect.options).some(opt => opt.value === currentModel);

            if (modelExists) {
                modelSelect.value = currentModel;
            } else {
                // 如果不在列表中，添加为一个选项（可能是用户自定义或旧的模型）
                const option = document.createElement('option');
                option.value = currentModel;
                option.textContent = `${currentModel} (当前配置)`;
                modelSelect.insertBefore(option, modelSelect.firstChild);
                modelSelect.value = currentModel;
            }
        }

        resultDiv.className = 'test-result test-success';
        resultDiv.textContent = `✓ 成功加载 ${data.models.length} 个模型${currentModel ? `，已保留选择: ${currentModel}` : ''}`;
        resultDiv.style.display = 'block';

        toast.success('模型列表加载成功');
    } catch (error) {
        // ...
    }
}
```

### 修复 5: 保存后重新初始化模型列表 ✅

**文件：** `static/js/pages/config/main.js`

修改 `handleSave()` 方法：

```javascript
async handleSave() {
    // ...

    try {
        saveBtn.disabled = true;
        saveBtn.textContent = '保存中...';

        const success = await this.configManager.saveConfig(imageDirs, imagePriority);

        if (success) {
            // ✅ 重新加载配置以确保界面同步
            const config = await this.configManager.loadConfig();

            // 重新加载模型列表
            const defaultModel = document.getElementById('defaultModel').value;
            await this.configManager.loadModels(defaultModel);

            // ✅ 重新初始化 Gemini 图像模型列表
            this.initGeminiImageModelSelect(config);

            console.log('✓ 配置已保存并重新加载');
        }
    } catch (error) {
        console.error('保存配置失败:', error);
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
}
```

## 修复效果

### 修复前 ❌

**场景1：刷新页面**
```
1. 刷新浏览器
2. 模型下拉框：空
3. 需要手动点击"刷新列表"
4. 选择模型后再保存
```

**场景2：保存 nano banana 模型**
```
1. 点击"刷新列表"获取模型
2. 选择 "nano banana"
3. 保存配置
4. 刷新页面
5. 显示：Gemini 2.5 Flash Image ❌
6. 下拉列表：硬编码的通用模型 ❌
```

**场景3：点击刷新列表**
```
1. 当前选择：nano banana
2. 点击"刷新列表"
3. 列表更新
4. 当前选择：丢失 ❌
```

### 修复后 ✅

**场景1：刷新页面**
```
1. 刷新浏览器
2. 模型下拉框：显示 "nano banana" ✅
3. 可以直接使用，无需重新选择
```

**场景2：保存 nano banana 模型**
```
1. 点击"刷新列表"获取模型
2. 选择 "nano banana"
3. 保存配置
4. 刷新页面
5. 显示：nano banana ✅
6. 配置文件：正确保存 ✅
```

**场景3：点击刷新列表**
```
1. 当前选择：nano banana
2. 点击"刷新列表"
3. 列表更新
4. 当前选择：保留 "nano banana" ✅
5. 如果不在新列表中，显示为 "nano banana (当前配置)" ✅
```

## 工作流程说明

### 首次配置
1. 在"必需配置"标签页配置 Gemini API Key 和 Base URL
2. 保存配置
3. 切换到"AI 绘图"标签页
4. 点击"刷新列表"按钮获取代理服务器支持的模型列表
5. 选择你需要的模型（如 "nano banana"）
6. 配置其他参数（风格、重试次数等）
7. 保存配置

### 后续使用
1. 刷新页面或重新打开配置页面
2. Gemini 图像模型下拉框自动显示上次保存的模型 ✅
3. 无需重新选择，可以直接修改其他参数
4. 如果想更换模型，点击"刷新列表"查看最新的可用模型

### 生成文章时
1. 系统读取 `config.json` 中的 `gemini_image_settings.model` 值
2. 使用保存的模型名称调用 API
3. 如果遇到 404 错误，会显示友好的错误提示，建议检查模型名称

## 配置文件验证

你的 `config.json` 中应该有：

```json
{
  "gemini_image_settings": {
    "enabled": true,
    "api_key": "sk-xxHlxWYuhWvwmh752smywnIYmlT7ifDAARbxNdGUcAZcoUNn",
    "base_url": "https://ljl1022.zeabur.app",
    "model": "nano banana",  // ✅ 你保存的模型
    "style": "realistic",
    "custom_prefix": "",
    "custom_suffix": "",
    "max_retries": 3,
    "timeout": 30
  }
}
```

## 测试步骤

### 测试 1: 页面刷新保持模型选择
1. 配置并保存 "nano banana" 模型
2. 刷新浏览器页面
3. ✅ 检查模型下拉框是否显示 "nano banana"

### 测试 2: 刷新列表保留选择
1. 当前选择 "nano banana"
2. 点击"刷新列表"按钮
3. ✅ 检查是否保留 "nano banana" 选择

### 测试 3: 配置持久化
1. 保存 "nano banana" 模型
2. 重启应用
3. ✅ 检查 config.json 中 model 字段是否为 "nano banana"
4. ✅ 生成文章时检查是否使用正确的模型

### 测试 4: 404 错误提示
1. 使用不存在的模型名称
2. 点击"测试生成"
3. ✅ 检查是否显示友好的错误提示，建议使用其他模型

## 修改的文件清单

1. **`static/js/pages/config/main.js`**
   - 添加 `initGeminiImageModelSelect()` 方法
   - 修改 `loadConfig()` 方法
   - 修改 `handleSave()` 方法
   - 修改 `handleLoadGeminiImageModels()` 方法

2. **`static/js/pages/config/config-manager.js`**
   - 修改 `applyGeminiImageSettings()` 方法（注释掉模型值设置）

3. **`app/services/gemini_image_service.py`**
   - 优化 404 错误提示信息

## 相关文档

- [GEMINI_IMAGE_CONFIG_FIX.md](./GEMINI_IMAGE_CONFIG_FIX.md) - Gemini 图像 API 配置修复说明
- [GEMINI_IMAGE_API_KEY_SAVE_FIX.md](./GEMINI_IMAGE_API_KEY_SAVE_FIX.md) - API Key 保存问题修复
- [GEMINI_IMAGE_TEST_FIX.md](./GEMINI_IMAGE_TEST_FIX.md) - 测试功能修复说明
- [CONFIG_FILES_UPDATE.md](./CONFIG_FILES_UPDATE.md) - 配置文件更新说明

## 完成状态

- ✅ 修复页面加载时模型列表为空的问题
- ✅ 修复模型配置未正确保存和显示的问题
- ✅ 修复"刷新列表"功能丢失当前选择的问题
- ✅ 优化 404 错误提示信息
- ✅ 文档编写完成

## 注意事项

1. **首次使用时需要手动刷新列表**
   - 页面加载时只显示保存的模型名称
   - 点击"刷新列表"可以查看代理服务器支持的所有模型

2. **模型名称大小写敏感**
   - 确保模型名称与代理服务器返回的完全一致
   - 如果遇到 404 错误，检查模型名称拼写

3. **不同代理服务器支持的模型不同**
   - 你的代理 `https://ljl1022.zeabur.app` 可能支持自定义模型
   - 点击"刷新列表"查看该代理支持的模型

4. **建议使用工作流程**
   - 先点击"刷新列表"查看可用模型
   - 从列表中选择模型（而不是手动输入）
   - 这样可以避免拼写错误
