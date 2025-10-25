/**
 * 图片目录管理器
 * 负责本地图片目录的添加、删除、获取
 */

class ImageDirectoryManager {
    constructor(container) {
        this.container = container;
        this.dirCount = 0;
        this.init();
    }

    init() {
        const addBtn = document.getElementById('addImageDir');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.addDirectory());
        }
    }

    /**
     * 添加图片目录
     */
    addDirectory(path = '', tags = []) {
        const dirItem = document.createElement('div');
        dirItem.className = 'image-dir-item slide-in-left';
        dirItem.dataset.index = this.dirCount++;

        dirItem.innerHTML = `
            <div class="form-group-inline">
                <div style="flex: 1;">
                    <label>目录路径:</label>
                    <input type="text" class="dir-path" value="${path}" placeholder="例如: images/nature">
                </div>
                <div style="flex: 1;">
                    <label>标签（逗号分隔）:</label>
                    <input type="text" class="dir-tags" value="${tags.join(', ')}" placeholder="例如: nature, landscape">
                </div>
                <button type="button" class="btn btn-secondary btn-small remove-dir-btn">删除</button>
            </div>
        `;

        const removeBtn = dirItem.querySelector('.remove-dir-btn');
        removeBtn.addEventListener('click', () => {
            dirItem.classList.add('fade-out');
            setTimeout(() => dirItem.remove(), 300);
        });

        this.container.appendChild(dirItem);
    }

    /**
     * 加载图片目录列表
     */
    loadDirectories(directories) {
        this.container.innerHTML = '';
        this.dirCount = 0;

        if (directories && directories.length > 0) {
            directories.forEach(dir => {
                this.addDirectory(dir.path, dir.tags || []);
            });
        } else {
            // 默认添加一个
            this.addDirectory('pic', ['default']);
        }
    }

    /**
     * 获取所有图片目录
     */
    getDirectories() {
        const dirItems = this.container.querySelectorAll('.image-dir-item');
        const directories = [];

        dirItems.forEach(item => {
            const path = item.querySelector('.dir-path').value.trim();
            const tagsStr = item.querySelector('.dir-tags').value.trim();
            const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];

            if (path) {
                directories.push({ path, tags });
            }
        });

        return directories;
    }
}

// 导出到全局
window.ImageDirectoryManager = ImageDirectoryManager;
