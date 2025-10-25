/**
 * 图片源优先级排序器
 * 负责拖拽排序图片源优先级
 */

class PrioritySorter {
    constructor(listElement) {
        this.list = listElement;
        this.draggedItem = null;

        if (this.list) {
            this.initializeDragAndDrop();
        }
    }

    /**
     * 初始化拖拽功能
     */
    initializeDragAndDrop() {
        const items = this.list.querySelectorAll('li');

        items.forEach(item => {
            item.draggable = true;
            item.addEventListener('dragstart', (e) => this.handleDragStart(e));
            item.addEventListener('dragover', (e) => this.handleDragOver(e));
            item.addEventListener('drop', (e) => this.handleDrop(e));
            item.addEventListener('dragend', (e) => this.handleDragEnd(e));
            item.addEventListener('dragenter', (e) => this.handleDragEnter(e));
            item.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        });
    }

    /**
     * 拖拽开始
     */
    handleDragStart(e) {
        this.draggedItem = e.target;
        e.target.style.opacity = '0.4';
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.innerHTML);
    }

    /**
     * 拖拽经过
     */
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        return false;
    }

    /**
     * 拖拽进入
     */
    handleDragEnter(e) {
        if (e.target !== this.draggedItem && e.target.tagName === 'LI') {
            e.target.style.borderTop = '3px solid var(--primary-color)';
        }
    }

    /**
     * 拖拽离开
     */
    handleDragLeave(e) {
        if (e.target.tagName === 'LI') {
            e.target.style.borderTop = '';
        }
    }

    /**
     * 放置
     */
    handleDrop(e) {
        e.stopPropagation();
        e.preventDefault();

        if (this.draggedItem !== e.target && e.target.tagName === 'LI') {
            // 获取所有项
            const allItems = Array.from(this.list.children);
            const draggedIndex = allItems.indexOf(this.draggedItem);
            const targetIndex = allItems.indexOf(e.target);

            // 重新排序
            if (draggedIndex < targetIndex) {
                e.target.parentNode.insertBefore(this.draggedItem, e.target.nextSibling);
            } else {
                e.target.parentNode.insertBefore(this.draggedItem, e.target);
            }
        }

        if (e.target.tagName === 'LI') {
            e.target.style.borderTop = '';
        }
        return false;
    }

    /**
     * 拖拽结束
     */
    handleDragEnd(e) {
        e.target.style.opacity = '1';

        // 移除所有项的边框
        const items = this.list.querySelectorAll('li');
        items.forEach(item => {
            item.style.borderTop = '';
        });
    }

    /**
     * 加载优先级配置
     */
    async loadPriority() {
        try {
            const config = await api.getConfig();
            if (config.image_source_priority && config.image_source_priority.length > 0) {
                this.reorderList(config.image_source_priority);
            }
        } catch (error) {
            console.error('加载图片优先级失败:', error);
        }
    }

    /**
     * 重新排序列表
     */
    reorderList(priority) {
        const items = Array.from(this.list.children);
        const orderedItems = [];

        // 按照优先级顺序重新排列
        priority.forEach(source => {
            const item = items.find(i => i.dataset.source === source);
            if (item) {
                orderedItems.push(item);
            }
        });

        // 添加配置中没有的项
        items.forEach(item => {
            if (!orderedItems.includes(item)) {
                orderedItems.push(item);
            }
        });

        // 重新插入到列表中
        this.list.innerHTML = '';
        orderedItems.forEach(item => {
            this.list.appendChild(item);
        });

        // 重新初始化拖拽功能
        this.initializeDragAndDrop();
    }

    /**
     * 获取当前优先级顺序
     */
    getPriority() {
        const items = this.list.querySelectorAll('li');
        const priority = [];

        items.forEach(item => {
            const source = item.dataset.source;
            if (source) {
                priority.push(source);
            }
        });

        return priority;
    }
}

// 导出到全局
window.PrioritySorter = PrioritySorter;
