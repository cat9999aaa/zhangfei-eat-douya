# Gemini 图像生成功能重要说明

## ⚠️ 重要提示

**Google Gemini API 官方目前不直接支持图像生成功能。**

### 当前状况

1. **Gemini API 的官方能力**
   - Gemini 模型主要用于**文本生成**和**多模态理解**（理解图片、视频）
   - 目前 Gemini API **不包含图像生成功能**
   - Google 的图像生成服务是 **Imagen**，但它是独立的产品，目前没有公开 API

2. **为什么会出现 404 错误**
   ```
   404 NOT_FOUND - Requested entity was not found
   ```
   这是因为我们尝试调用的 endpoint（`/v1/models/{model}:generateImage`）在官方 Gemini API 中不存在。

### 解决方案

有以下几种方式可以实现图像生成：

#### 方案 1：使用 ComfyUI（推荐）✅

ComfyUI 是一个强大的本地 AI 图像生成工具：

**优点：**
- ✅ 完全本地运行，无 API 限制
- ✅ 可使用 Stable Diffusion 等开源模型
- ✅ 完全免费，生成质量高
- ✅ 本项目已完美支持

**配置步骤：**
1. 下载安装 ComfyUI：https://github.com/comfyanonymous/ComfyUI
2. 配置 workflow JSON 文件
3. 在本系统的配置页面填写 ComfyUI 服务器地址
4. 设置图片源优先级，将 ComfyUI 排在前面

#### 方案 2：使用第三方图片 API ✅

本系统已集成多个免费图片 API：

- **Unsplash**：高质量摄影图片
- **Pexels**：免费素材图片
- **Pixabay**：海量免费图片

**优点：**
- ✅ 无需本地硬件
- ✅ 配置简单，只需 API Key
- ✅ 图片质量有保障

#### 方案 3：使用代理服务（需要特殊配置）

某些第三方 API 代理服务可能提供 Imagen 或类似功能的接口，例如：

- 你使用的 `https://api.dashen.wang` 可能支持某些图像生成功能
- 但需要确认其具体支持的 API 格式

**如果想使用代理的图像生成：**
1. 联系代理服务商确认是否支持图像生成
2. 获取正确的 endpoint 和请求格式
3. 可能需要使用不同的模型名称

#### 方案 4：使用本地图库 ✅

直接使用本地存储的图片：

**优点：**
- ✅ 完全离线
- ✅ 可精确控制图片内容
- ✅ 响应速度快

### 当前代码的适配

我已经修改了代码以：

1. **更好的错误处理**
   - 详细的错误信息
   - 识别 404 错误并给出提示
   - 不会无限重试配置错误

2. **灵活的模型选择**
   - 支持从服务器加载可用模型列表
   - 提供推荐的 Gemini 模型作为默认选项
   - 允许用户自行配置

3. **智能降级机制**
   - Gemini 生成失败后自动切换到其他图片源
   - 不会影响文章生成流程

### 推荐配置

#### 最佳配置方案

```json
{
  "image_source_priority": [
    "user_uploaded",     // 1. 优先使用用户上传的图片
    "comfyui",           // 2. ComfyUI 本地 AI 生成（推荐）
    "pexels",            // 3. Pexels 免费图库
    "unsplash",          // 4. Unsplash 图库
    "pixabay",           // 5. Pixabay 图库
    "local"              // 6. 本地图库
  ]
}
```

**不建议启用 Gemini 图像生成**，除非：
- 你使用的代理服务明确支持 Imagen API
- 你已经测试成功

### 测试建议

1. **测试 ComfyUI**
   ```
   配置页面 → AI 绘图 → ComfyUI 设置 → 测试工作流
   ```

2. **测试图片 API**
   ```
   配置页面 → 图片 API → 测试各个 API 连接
   ```

3. **暂时禁用 Gemini 图像生成**
   ```
   配置页面 → AI 绘图 → Gemini 图像生成 → 取消勾选"启用"
   ```

### 常见问题

**Q: 为什么添加这个功能但又不能用？**

A: 这个功能是为了未来可能的支持而设计的：
- Google 可能在未来开放 Imagen API
- 第三方代理可能已经或将会支持
- 代码架构上为图像生成功能预留了接口

**Q: 有没有其他 AI 图像生成的选择？**

A: 有！推荐使用：
1. **ComfyUI**（本地，免费，强大）
2. **Stable Diffusion Web UI**（类似 ComfyUI）
3. **Midjourney**（需要订阅）
4. **DALL-E**（OpenAI 的服务）

**Q: 我的代理支持 Imagen，如何配置？**

A: 请联系你的代理服务商：
1. 确认支持的 API endpoint 格式
2. 确认支持的模型名称
3. 获取示例请求和响应
4. 然后我可以帮你调整代码以适配

### 总结

- ✅ **推荐使用 ComfyUI** 进行本地 AI 图像生成
- ✅ **推荐使用免费图片 API**（Unsplash/Pexels/Pixabay）
- ⚠️ **Gemini 图像生成**目前不可用，建议禁用
- 🔄 **未来更新**：如果 Google 开放 Imagen API，会第一时间适配

如有任何问题，欢迎随时询问！
