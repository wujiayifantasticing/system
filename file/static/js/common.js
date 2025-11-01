// common.js - 通用JavaScript功能

// 导航功能
function navigate(page) {
    window.location.href = '/' + page;
}

// 下拉菜单切换
function toggleDropdown(id) {
    const dropdown = document.getElementById(id);
    const isActive = dropdown.classList.contains('active');
    
    // 关闭其他下拉菜单
    document.querySelectorAll('.dropdown.active').forEach(item => {
        if (item.id !== id) item.classList.remove('active');
    });
    
    // 切换当前下拉菜单
    if (isActive) {
        dropdown.classList.remove('active');
    } else {
        dropdown.classList.add('active');
    }
    event.stopPropagation();
}

// 点击页面其他区域关闭下拉菜单
document.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.active').forEach(item => {
            item.classList.remove('active');
        });
    }
});

// 显示/隐藏加载状态
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'block';
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';
}

// 通用文件上传处理
function handleFileUpload(inputElement, previewElement, fileNameElement, fileType) {
    const file = inputElement.files[0];
    if (!file) return;

    // 显示文件名
    if (fileNameElement) {
        fileNameElement.textContent = file.name;
    }

    // 预览图片
    if (previewElement && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewElement.src = e.target.result;
            previewElement.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    // 上传到服务器
    const formData = new FormData();
    formData.append('fileInput', file);
    formData.append('type', fileType);

    return fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || '上传失败');
        }
        return data;
    });
}

// 拖拽上传功能
function initDragUpload(uploadArea, fileInput, onFileSelect) {
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file) {
                fileInput.files = files;
                if (onFileSelect) onFileSelect(file);
            }
        }
    });
}
// 语音性别年龄识别功能
function initSpeechGenderAge() {
    // 文件选择处理
    document.getElementById('audioFile')?.addEventListener('change', function(e) {
        // ... 文件处理代码
    });
    
    // 拖拽上传功能
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        // ... 拖拽处理代码
    }
    
    // 开始识别函数
    window.startRecognition = function() {
        // ... 识别逻辑
    };
}

// 页面加载时初始化
if (document.getElementById('uploadArea')) {
    initSpeechGenderAge();
}