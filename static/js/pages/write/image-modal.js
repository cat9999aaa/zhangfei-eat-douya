/**
 * 图片设置模态框
 * 负责图片上传、剪贴板粘贴、URL输入等功能
 */

class ImageModal {
    constructor(options = {}) {
        this.stateManager = options.stateManager;
        this.topicManager = options.topicManager;

        // 模态框元素
        this.modal = document.getElementById('imageModal');
        this.modalTopicName = document.getElementById('modalTopicName');
        this.modalClose = this.modal.querySelector('.modal-close');
        this.modalStatus = document.getElementById('modalStatus');

        // 按钮
        this.saveBtn = document.getElementById('saveImageBtn');
        this.clearBtn = document.getElementById('clearImageBtn');
        this.cancelBtn = document.getElementById('cancelImageBtn');

        // Tab
        this.tabBtns = this.modal.querySelectorAll('.tab-btn');
        this.uploadTab = document.getElementById('uploadTab');
        this.clipboardTab = document.getElementById('clipboardTab');
        this.urlTab = document.getElementById('urlTab');

        // 上传相关
        this.selectFileBtn = document.getElementById('selectFileBtn');
        this.fileInput = document.getElementById('imageFileInput');
        this.uploadPreview = document.getElementById('uploadPreview');
        this.uploadPreviewImg = document.getElementById('uploadPreviewImg');
        this.uploadFileName = document.getElementById('uploadFileName');

        // 剪贴板相关
        this.pasteZone = document.getElementById('pasteZone');
        this.clipboardPreview = document.getElementById('clipboardPreview');
        this.clipboardPreviewImg = document.getElementById('clipboardPreviewImg');

        // URL相关
        this.urlInput = document.getElementById('imageUrlInput');
        this.loadUrlBtn = document.getElementById('loadUrlBtn');
        this.urlPreview = document.getElementById('urlPreview');
        this.urlPreviewImg = document.getElementById('urlPreviewImg');
        this.urlStatus = document.getElementById('urlStatus');

        // 状态
        this.currentTopicIndex = null;
        this.currentImageData = null;

        this.init();
    }

    init() {
        // Tab切换
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        // 上传相关
        this.selectFileBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // 剪贴板相关
        this.setupPasteZone();

        // URL相关
        this.loadUrlBtn.addEventListener('click', () => this.handleUrlLoad());

        // 按钮事件
        this.saveBtn.addEventListener('click', () => this.handleSave());
        this.clearBtn.addEventListener('click', () => this.handleClear());
        this.cancelBtn.addEventListener('click', () => this.close());
        this.modalClose.addEventListener('click', () => this.close());

        // 点击模态框外部关闭
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    /**
     * 打开模态框
     */
    open(topicIndex) {
        const wrapper = document.querySelector(`.topic-input-wrapper[data-index="${topicIndex}"]`);
        if (!wrapper) return;

        const input = wrapper.querySelector('.topic-input');
        const topicText = input.value.trim() || `标题 ${topicIndex + 1}`;

        this.currentTopicIndex = topicIndex;
        this.modalTopicName.textContent = topicText;

        this.reset();

        // 如果已有图片设置，显示预览
        if (this.stateManager.hasTopicImage(topicIndex)) {
            const imageData = this.stateManager.getTopicImage(topicIndex);
            this.loadExistingImage(imageData);
        }

        this.modal.style.display = 'flex';
        this.modal.classList.add('fade-in');
    }

    /**
     * 关闭模态框
     */
    close() {
        this.modal.classList.add('fade-out');
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.modal.classList.remove('fade-in', 'fade-out');
            this.currentTopicIndex = null;
            this.currentImageData = null;
        }, 300);
    }

    /**
     * 重置模态框
     */
    reset() {
        this.switchTab('upload');

        // 清空所有预览
        this.uploadPreview.style.display = 'none';
        this.uploadPreviewImg.src = '';
        this.uploadFileName.textContent = '';
        this.fileInput.value = '';

        this.clipboardPreview.style.display = 'none';
        this.clipboardPreviewImg.src = '';

        this.urlPreview.style.display = 'none';
        this.urlPreviewImg.src = '';
        this.urlInput.value = '';
        this.urlStatus.textContent = '';

        this.hideStatus();
        this.currentImageData = null;
    }

    /**
     * 加载已存在的图片
     */
    loadExistingImage(imageData) {
        switch (imageData.type) {
            case 'upload':
            case 'clipboard':
                this.switchTab('upload');
                this.uploadPreview.style.display = 'block';
                this.uploadPreviewImg.src = imageData.preview;
                this.uploadFileName.textContent = imageData.filename || '已设置图片';
                this.currentImageData = imageData;
                break;
            case 'url':
                this.switchTab('url');
                this.urlInput.value = imageData.url;
                this.urlPreview.style.display = 'block';
                this.urlPreviewImg.src = imageData.preview;
                this.urlStatus.textContent = '✓ URL已加载';
                this.urlStatus.style.color = 'var(--success-color)';
                this.currentImageData = imageData;
                break;
        }
    }

    /**
     * 切换Tab
     */
    switchTab(tab) {
        // 更新按钮状态
        this.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        // 更新内容显示
        this.uploadTab.classList.toggle('active', tab === 'upload');
        this.clipboardTab.classList.toggle('active', tab === 'clipboard');
        this.urlTab.classList.toggle('active', tab === 'url');
    }

    /**
     * 处理文件选择
     */
    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            this.showStatus('请选择图片文件', 'error');
            return;
        }

        // 预览图片
        const reader = new FileReader();
        reader.onload = (e) => {
            this.uploadPreviewImg.src = e.target.result;
            this.uploadFileName.textContent = file.name;
            this.uploadPreview.style.display = 'block';

            this.currentImageData = {
                type: 'upload',
                file: file,
                preview: e.target.result,
                filename: file.name
            };

            this.showStatus('✓ 文件已选择', 'success');
        };
        reader.readAsDataURL(file);
    }

    /**
     * 设置剪贴板粘贴区域
     */
    setupPasteZone() {
        this.pasteZone.setAttribute('tabindex', '0');

        this.pasteZone.addEventListener('click', () => {
            this.pasteZone.focus();
        });

        this.pasteZone.addEventListener('focus', () => {
            this.pasteZone.classList.add('active');
        });

        this.pasteZone.addEventListener('blur', () => {
            this.pasteZone.classList.remove('active');
        });

        this.pasteZone.addEventListener('paste', async (e) => {
            e.preventDefault();

            const items = e.clipboardData.items;
            let imageFile = null;

            for (let item of items) {
                if (item.type.startsWith('image/')) {
                    imageFile = item.getAsFile();
                    break;
                }
            }

            if (imageFile) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.clipboardPreviewImg.src = e.target.result;
                    this.clipboardPreview.style.display = 'block';

                    this.currentImageData = {
                        type: 'clipboard',
                        file: imageFile,
                        preview: e.target.result,
                        filename: `clipboard_${Date.now()}.png`
                    };

                    this.showStatus('✓ 图片粘贴成功！', 'success');
                };
                reader.readAsDataURL(imageFile);
            } else {
                this.showStatus('剪贴板中没有图片', 'error');
            }
        });
    }

    /**
     * 处理URL加载
     */
    async handleUrlLoad() {
        const url = this.urlInput.value.trim();

        if (!url) {
            this.showStatus('请输入图片URL', 'error');
            return;
        }

        // 验证URL格式
        if (!Utils.isValidURL(url)) {
            this.showStatus('URL格式不正确', 'error');
            return;
        }

        // 尝试加载图片
        const img = new Image();
        img.crossOrigin = 'anonymous';

        img.onload = () => {
            this.urlPreviewImg.src = url;
            this.urlPreview.style.display = 'block';
            this.urlStatus.textContent = '✓ 图片加载成功';
            this.urlStatus.style.color = 'var(--success-color)';

            this.currentImageData = {
                type: 'url',
                url: url,
                preview: url
            };

            this.showStatus('✓ URL图片加载成功', 'success');
        };

        img.onerror = () => {
            this.urlPreview.style.display = 'none';
            this.urlStatus.textContent = '✗ 图片加载失败，请检查URL';
            this.urlStatus.style.color = 'var(--error-color)';
            this.showStatus('图片加载失败，请检查URL是否正确', 'error');
        };

        img.src = url;
    }

    /**
     * 保存图片设置
     */
    async handleSave() {
        if (!this.currentImageData) {
            this.showStatus('请先选择或上传图片', 'error');
            return;
        }

        // 如果是文件上传或剪贴板，先上传到服务器
        if (this.currentImageData.type === 'upload' || this.currentImageData.type === 'clipboard') {
            this.saveBtn.disabled = true;
            this.saveBtn.textContent = '上传中...';

            try {
                const data = await api.uploadImage(this.currentImageData.file);

                this.currentImageData.uploadedPath = data.path;
                this.currentImageData.filename = data.filename;

                this.stateManager.setTopicImage(this.currentTopicIndex, this.currentImageData);
                this.topicManager.updateImageButtonStatus(this.currentTopicIndex, true);
                this.topicManager.saveState();

                this.showStatus('✓ 图片设置成功！', 'success');
                toast.success('图片上传成功！');

                setTimeout(() => this.close(), 1000);
            } catch (error) {
                this.showStatus('上传失败: ' + error.message, 'error');
                toast.error('图片上传失败');
            } finally {
                this.saveBtn.disabled = false;
                this.saveBtn.textContent = '保存设置';
            }
        } else if (this.currentImageData.type === 'url') {
            // URL类型直接保存
            this.stateManager.setTopicImage(this.currentTopicIndex, this.currentImageData);
            this.topicManager.updateImageButtonStatus(this.currentTopicIndex, true);
            this.topicManager.saveState();

            this.showStatus('✓ 图片设置成功！', 'success');
            toast.success('图片设置成功！');

            setTimeout(() => this.close(), 1000);
        }
    }

    /**
     * 清除图片设置
     */
    handleClear() {
        if (this.currentTopicIndex !== null) {
            this.stateManager.deleteTopicImage(this.currentTopicIndex);
            this.topicManager.updateImageButtonStatus(this.currentTopicIndex, false);
            this.topicManager.saveState();
            toast.info('已清除图片设置');
        }
        this.close();
    }

    /**
     * 显示状态消息
     */
    showStatus(message, type) {
        this.modalStatus.textContent = message;
        this.modalStatus.className = 'modal-status ' + type;
        this.modalStatus.style.display = 'block';

        setTimeout(() => {
            this.hideStatus();
        }, 3000);
    }

    /**
     * 隐藏状态消息
     */
    hideStatus() {
        this.modalStatus.style.display = 'none';
    }
}

// 导出到全局
window.ImageModal = ImageModal;
