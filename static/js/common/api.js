/**
 * API 请求封装
 * 提供统一的HTTP请求接口和错误处理
 */

class API {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * 通用请求方法
     */
    async request(url, options = {}) {
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(this.baseURL + url, config);
            const data = await response.json();

            if (!response.ok) {
                throw {
                    status: response.status,
                    message: data.error || data.message || '请求失败',
                    data
                };
            }

            return data;
        } catch (error) {
            // 网络错误或其他异常
            if (!error.status) {
                throw {
                    status: 0,
                    message: '网络连接失败，请检查网络设置',
                    data: null
                };
            }
            throw error;
        }
    }

    /**
     * GET 请求
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullURL = queryString ? `${url}?${queryString}` : url;
        return this.request(fullURL, { method: 'GET' });
    }

    /**
     * POST 请求
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT 请求
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE 请求
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    /**
     * 上传文件
     */
    async upload(url, file, onProgress = null) {
        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch(this.baseURL + url, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw {
                    status: response.status,
                    message: data.error || '上传失败',
                    data
                };
            }

            return data;
        } catch (error) {
            if (!error.status) {
                throw {
                    status: 0,
                    message: '网络连接失败',
                    data: null
                };
            }
            throw error;
        }
    }

    // ==================== 具体API方法 ====================

    // 配置相关
    async getConfig() {
        return this.get('/config');
    }

    async saveConfig(config) {
        return this.post('/config', config);
    }

    async getModels(forceRefresh = false) {
        return this.get('/models', { refresh: forceRefresh });
    }

    // 测试API
    async testModel(modelName, apiKey, baseUrl) {
        return this.post('/test-model', { model_name: modelName, api_key: apiKey, base_url: baseUrl });
    }

    async testUnsplash(accessKey) {
        return this.post('/test-unsplash', { access_key: accessKey });
    }

    async testPexels(apiKey) {
        return this.post('/test-pexels', { api_key: apiKey });
    }

    async testPixabay(apiKey) {
        return this.post('/test-pixabay', { api_key: apiKey });
    }

    async testComfyUI(settings) {
        return this.post('/test-comfyui', settings);
    }

    async testGeminiImage(apiKey, baseUrl, model) {
        return this.post('/test-gemini-image', { api_key: apiKey, base_url: baseUrl, model });
    }

    async getGeminiImageModels(forceRefresh = false) {
        return this.get('/gemini-image-models', { refresh: forceRefresh });
    }

    async getGeminiImageStyles() {
        return this.get('/gemini-image-styles');
    }

    // 图片相关
    async uploadImage(file) {
        return this.upload('/upload-image', file);
    }

    async downloadImageFromURL(url) {
        return this.post('/download-image-from-url', { url });
    }

    async listLocalImages() {
        return this.get('/list-local-images');
    }

    async listUploadedImages() {
        return this.get('/list-uploaded-images');
    }

    // 生成相关
    async generateArticles(topics, topicImages) {
        return this.post('/generate', { topics, topic_images: topicImages });
    }

    async getGenerationStatus(taskId) {
        return this.get(`/generate/status/${taskId}`);
    }

    async retryFailedTopics(taskId, topics) {
        return this.post('/generate/retry', { task_id: taskId, topics });
    }

    // 历史记录
    async getHistory() {
        return this.get('/history');
    }

    // Pandoc检查
    async checkPandoc() {
        return this.get('/check-pandoc');
    }
}

// 创建全局API实例
window.api = new API();

// 也可以作为模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}
