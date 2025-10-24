// DOM 元素
const refreshHistoryBtn = document.getElementById('refreshHistory');
const clearHistoryBtn = document.getElementById('clearHistory');
const historyList = document.getElementById('historyList');

// 页面加载时加载历史记录
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});

// 加载历史记录
async function loadHistory() {
    historyList.innerHTML = '<p class="loading-text">加载中...</p>';

    try {
        const response = await fetch('/api/history');
        if (response.ok) {
            const data = await response.json();
            displayHistory(data.files);
        } else {
            historyList.innerHTML = '<p class="loading-text">加载失败</p>';
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        historyList.innerHTML = '<p class="loading-text">加载失败</p>';
    }
}

// 显示历史记录
function displayHistory(files) {
    if (files.length === 0) {
        historyList.innerHTML = '<p class="loading-text">暂无历史记录</p>';
        return;
    }

    historyList.innerHTML = '';

    files.forEach(file => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';

        const sizeKB = (file.size / 1024).toFixed(2);

        historyItem.innerHTML = `
            <div class="history-item-header">
                <div class="history-item-title">${file.title}</div>
                <div class="history-item-date">${file.created}</div>
            </div>
            <div class="result-info">文件名: ${file.filename}</div>
            <div class="result-info">大小: ${sizeKB} KB</div>
            <a href="/api/download/${file.filename}" class="download-btn" download>下载</a>
        `;

        historyList.appendChild(historyItem);
    });
}

// 刷新历史记录
refreshHistoryBtn.addEventListener('click', () => {
    loadHistory();
});

// 清空历史记录
clearHistoryBtn.addEventListener('click', async () => {
    if (!confirm('确定要清空所有历史记录吗？此操作无法撤销！')) {
        return;
    }

    alert('清空历史功能需要手动删除 output 目录下的文件');
});

// 格式化文件大小
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
