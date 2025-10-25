# 按钮功能测试指南

## 问题修复说明

我已经修复了以下问题：

### 1. 写作页面 - 图片设置按钮
**问题**：点击没反应
**原因**：索引绑定问题
**修复**：
- 使用闭包正确捕获索引
- 使用 `this.parentElement.dataset.index` 动态获取索引

**测试方法**：
1. 打开写作页面：http://localhost:5000
2. 点击任一主题后的 "🖼️ 图片设置" 按钮
3. 应该弹出图片设置窗口

### 2. 配置页面 - 添加目录按钮
**问题**：点击没反应
**原因**：缺少相关JavaScript代码
**修复**：
- 添加了 `addImageDirectory()` 函数
- 添加了 `loadImageDirectories()` 函数
- 添加了事件监听器
- 添加了CSS样式

**测试方法**：
1. 打开配置页面：http://localhost:5000/config
2. 滚动到"本地图库配置"部分
3. 点击 "+ 添加目录" 按钮
4. 应该看到新增的目录输入表单

## 完整测试步骤

### 测试写作页面图片设置

```
1. 访问 http://localhost:5000
2. 输入一个标题，例如："测试文章"
3. 点击标题后的 "🖼️ 图片设置" 按钮
4. 确认弹出模态框
5. 测试三个选项卡：
   - 上传图片：点击"选择文件"
   - 粘贴图片：点击粘贴区域，按Ctrl+V
   - 图片URL：输入URL，点击"加载预览"
6. 保存后，按钮应变蓝色显示"已设置"
```

### 测试配置页面添加目录

```
1. 访问 http://localhost:5000/config
2. 滚动到"本地图库配置"部分
3. 点击 "+ 添加目录" 按钮
4. 填写目录路径和标签
5. 可以点击"删除"按钮移除
6. 点击"保存配置"保存设置
```

## 如果仍有问题

### 清除浏览器缓存
```
1. 按 Ctrl+Shift+Delete（Windows）或 Cmd+Shift+Delete（Mac）
2. 选择"缓存的图片和文件"
3. 清除数据
4. 刷新页面（Ctrl+F5 或 Cmd+Shift+R）
```

### 检查浏览器控制台
```
1. 按 F12 打开开发者工具
2. 切换到"Console"标签
3. 查看是否有JavaScript错误
4. 如果有错误，请告诉我具体内容
```

### 重启服务器
```
1. 停止当前服务器（Ctrl+C）
2. 重新运行：python app.py
3. 等待服务器启动
4. 刷新浏览器
```

## 调试技巧

### 测试按钮是否存在
在浏览器控制台输入：
```javascript
// 测试图片设置按钮
document.querySelectorAll('.image-set-btn').length

// 测试添加目录按钮
document.getElementById('addImageDir')
```

### 测试事件监听器
```javascript
// 测试图片模态框
const btn = document.querySelector('.image-set-btn');
if (btn) {
    console.log('按钮存在');
    console.log('onclick:', btn.onclick);
} else {
    console.log('按钮不存在');
}

// 测试添加目录按钮
const addBtn = document.getElementById('addImageDir');
if (addBtn) {
    console.log('添加目录按钮存在');
    addBtn.click(); // 手动触发点击
}
```

## 已更新的文件

1. `static/write.js` - 修复图片设置按钮事件绑定
2. `static/config.js` - 添加完整的图片API和目录管理功能
3. `templates/config.html` - 添加CSS样式

## 下一步

如果按钮仍然没反应，请：
1. 查看浏览器控制台的错误信息
2. 确认服务器已重启
3. 确认浏览器缓存已清除
4. 告诉我具体的错误信息或现象
