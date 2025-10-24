/**
 * 写作页面状态管理
 * 负责管理主题、图片设置、任务进度等状态
 */

class WriteStateManager {
    constructor() {
        this.topicImages = new Map(); // 主题图片映射
        this.currentTaskId = null;
        this.STATE_KEY = 'writePageState';
        this.TASK_KEY = 'currentTask';
        this.STATE_EXPIRY = 24 * 60 * 60 * 1000; // 24小时
    }

    /**
     * 保存页面状态
     */
    savePageState(topics, enableImage) {
        // 保存图片设置
        const imageSettings = {};
        this.topicImages.forEach((imageData, index) => {
            // 只保存关键信息，不保存 File 对象
            imageSettings[index] = {
                type: imageData.type,
                filename: imageData.filename,
                uploadedPath: imageData.uploadedPath,
                url: imageData.url,
                preview: imageData.preview
            };
        });

        const state = {
            topics,
            enableImage,
            imageSettings,
            timestamp: Date.now()
        };

        storage.set(this.STATE_KEY, state, this.STATE_EXPIRY);
    }

    /**
     * 恢复页面状态
     */
    restorePageState() {
        const state = storage.get(this.STATE_KEY);

        if (!state) {
            return null;
        }

        // 恢复图片设置
        if (state.imageSettings) {
            Object.entries(state.imageSettings).forEach(([index, imageData]) => {
                this.topicImages.set(parseInt(index), imageData);
            });
        }

        return {
            topics: state.topics || [],
            enableImage: state.enableImage || false
        };
    }

    /**
     * 清除页面状态
     */
    clearPageState() {
        storage.remove(this.STATE_KEY);
        this.topicImages.clear();
    }

    /**
     * 保存任务进度
     */
    saveTaskProgress(taskId) {
        this.currentTaskId = taskId;
        storage.set(this.TASK_KEY, {
            taskId,
            timestamp: Date.now()
        });
    }

    /**
     * 获取保存的任务
     */
    getSavedTask() {
        return storage.get(this.TASK_KEY);
    }

    /**
     * 清除任务进度
     */
    clearTaskProgress() {
        this.currentTaskId = null;
        storage.remove(this.TASK_KEY);
    }

    /**
     * 设置主题图片
     */
    setTopicImage(topicIndex, imageData) {
        this.topicImages.set(topicIndex, imageData);
    }

    /**
     * 获取主题图片
     */
    getTopicImage(topicIndex) {
        return this.topicImages.get(topicIndex);
    }

    /**
     * 删除主题图片
     */
    deleteTopicImage(topicIndex) {
        this.topicImages.delete(topicIndex);
    }

    /**
     * 检查主题是否有图片
     */
    hasTopicImage(topicIndex) {
        return this.topicImages.has(topicIndex);
    }

    /**
     * 清空所有图片设置
     */
    clearAllImages() {
        this.topicImages.clear();
    }

    /**
     * 构建主题图片映射（用于API请求）
     */
    buildTopicImageMap(topics) {
        const topicImageMap = {};

        topics.forEach((topic, index) => {
            if (this.topicImages.has(index)) {
                const imageData = this.topicImages.get(index);
                if (imageData.type === 'url') {
                    topicImageMap[topic] = {
                        type: 'url',
                        url: imageData.url
                    };
                } else if (imageData.uploadedPath) {
                    topicImageMap[topic] = {
                        type: 'uploaded',
                        path: imageData.uploadedPath
                    };
                }
            }
        });

        return topicImageMap;
    }
}

// 导出全局实例
window.writeStateManager = new WriteStateManager();
