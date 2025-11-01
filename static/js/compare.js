// compare.js - 人脸比对功能实现
// 全局变量，用于跟踪两个文件的上传状态
let file1Uploaded = false;
let file2Uploaded = false;
let file1Path = '';
let file2Path = '';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('人脸比对页面已加载');
    
    // 绑定文件选择事件
    document.getElementById('file').addEventListener('change', function() {
        handleFileChange(this, 'compare1', 'img', 'file1-status');
    });
    
    document.getElementById('file2').addEventListener('change', function() {
        handleFileChange(this, 'compare2', 'img2', 'file2-status');
    });
    
    // 绑定比对按钮点击事件
    document.querySelector('.identifybutton').addEventListener('click', compareFaces);
    
    // 初始化拖放功能
    setupDragAndDrop();
});

// 处理文件选择和预览
function handleFileChange(input, fileType, previewImgId, statusId) {
    const file = input.files[0];
    const statusElement = document.getElementById(statusId);
    
    if (file) {
        // 文件类型验证
        const validImageTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp'];
        if (!validImageTypes.includes(file.type)) {
            alert('请上传JPG, PNG或BMP格式的图片');
            input.value = '';
            statusElement.innerHTML = '<i class="fas fa-times-circle" style="color: red;"></i> 文件格式不支持';
            return;
        }

        // 文件大小验证 (最大限制2MB)
        const maxSize = 2 * 1024 * 1024; // 2MB
        if (file.size > maxSize) {
            alert('文件大小不能超过2MB');
            input.value = '';
            statusElement.innerHTML = '<i class="fas fa-times-circle" style="color: red;"></i> 文件过大';
            return;
        }

        // 更新状态
        statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在上传...';

        // 显示预览图片
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewImage = document.getElementById(previewImgId);
            previewImage.src = e.target.result;
            previewImage.style.maxWidth = '100%';
            previewImage.style.maxHeight = '300px';
        };
        reader.readAsDataURL(file);

        // 上传文件到服务器
        uploadFile(file, fileType, previewImgId, statusId);
    } else {
        // 没有选择文件，重置状态
        statusElement.innerHTML = '<i class="fas fa-info-circle"></i> 等待上传图片...';
    }
}

// 上传文件到服务器
function uploadFile(file, fileType, previewImgId, statusId) {
    const formData = new FormData();
    formData.append('fileInput', file);
    formData.append('type', fileType);
    
    // 显示上传状态
    const previewImage = document.getElementById(previewImgId);
    const statusElement = document.getElementById(statusId);
    previewImage.style.opacity = '0.7';
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        previewImage.style.opacity = '1';
        
        if (data.success) {
            console.log(`${fileType} 文件上传成功:`, data.path);
            statusElement.innerHTML = '<i class="fas fa-check-circle" style="color: green;"></i> 上传成功';
            
            // 更新上传状态
            if (fileType === 'compare1') {
                file1Uploaded = true;
                file1Path = data.path;
            } else if (fileType === 'compare2') {
                file2Uploaded = true;
                file2Path = data.path;
            }
            
            // 检查是否可以启用比对按钮
            updateCompareButtonState();
        } else {
            statusElement.innerHTML = '<i class="fas fa-times-circle" style="color: red;"></i> 上传失败';
            alert(`${fileType} 文件上传失败: ` + data.error);
            // 重置文件输入
            if (fileType === 'compare1') {
                document.getElementById('file').value = '';
                document.getElementById('img').src = '../static/images/default_face_compare.jpg';
            } else {
                document.getElementById('file2').value = '';
                document.getElementById('img2').src = '../static/images/default_face_compare.jpg';
            }
        }
    })
    .catch(error => {
    // 隐藏加载提示
    loadingDiv.style.display = 'none';
    
    // 恢复按钮状态
    compareButton.disabled = false;
    compareButton.innerHTML = '<i class="fas fa-people-arrows"></i> 人脸比对';
    compareButton.style.opacity = '1';
    
    console.error('比对请求失败:', error);
    
    // 显示更友好的错误信息
    if (error.message.includes('网络错误')) {
        alert('网络连接失败，请检查网络连接后重试');
    } else {
        alert('比对失败: ' + error.message);
    }
});
}

// 更新比对按钮状态
function updateCompareButtonState() {
    const compareButton = document.querySelector('.identifybutton');
    
    if (file1Uploaded && file2Uploaded) {
        compareButton.disabled = false;
        compareButton.style.opacity = '1';
        compareButton.style.cursor = 'pointer';
        compareButton.innerHTML = '<i class="fas fa-people-arrows"></i> 人脸比对';
    } else {
        compareButton.disabled = true;
        compareButton.style.opacity = '0.5';
        compareButton.style.cursor = 'not-allowed';
        compareButton.innerHTML = '<i class="fas fa-people-arrows"></i> 人脸比对';
    }
}

// 人脸比对函数
function compareFaces() {
    const compareButton = document.querySelector('.identifybutton');
    const resultDiv = document.getElementById('divAdd');
    const loadingDiv = document.getElementById('loading');
    
    // 检查文件是否已上传
    if (!file1Uploaded || !file2Uploaded) {
        alert('请先上传两张图片');
        return;
    }
    
    // 更新按钮状态为加载中
    compareButton.disabled = true;
    compareButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 比对中...';
    compareButton.style.opacity = '0.7';
    
    // 显示加载提示
    loadingDiv.style.display = 'block';
    
    // 清空之前的结果
    const resultItems = resultDiv.querySelectorAll('.list-group-item');
    resultItems[0].querySelector('.badge').textContent = '--';
    resultItems[1].querySelector('.badge').textContent = '--';
    
    // 重置结果样式
    resultItems[0].className = 'list-group-item list-group-item-info';
    resultItems[1].className = 'list-group-item list-group-item-info';
    
    // 发送比对请求
    fetch('/compare', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络错误，无法获取数据');
        }
        return response.json();
    })
    .then(data => {
        // 隐藏加载提示
        loadingDiv.style.display = 'none';
        
        // 恢复按钮状态
        compareButton.disabled = false;
        compareButton.innerHTML = '<i class="fas fa-people-arrows"></i> 人脸比对';
        compareButton.style.opacity = '1';
        
        if (data.flag === 'true' && data.data) {
            // 显示比对结果
            const score = (data.data.score * 100).toFixed(2) + '%';
            const desc = data.data.desc;
            
            resultItems[0].querySelector('.badge').textContent = score;
            resultItems[1].querySelector('.badge').textContent = desc;
            
            // 根据结果设置不同的颜色
            if (data.data.score > 0.67) {
                resultItems[0].className = 'list-group-item list-group-item-success';
                resultItems[1].className = 'list-group-item list-group-item-success';
            } else {
                resultItems[0].className = 'list-group-item list-group-item-danger';
                resultItems[1].className = 'list-group-item list-group-item-danger';
            }
            
            console.log('人脸比对结果:', data.data);
        } else {
            alert(data.msg || '比对失败');
        }
    })
    .catch(error => {
        // 隐藏加载提示
        loadingDiv.style.display = 'none';
        
        // 恢复按钮状态
        compareButton.disabled = false;
        compareButton.innerHTML = '<i class="fas fa-people-arrows"></i> 人脸比对';
        compareButton.style.opacity = '1';
        
        console.error('比对请求失败:', error);
        alert('比对请求失败，请重试: ' + error.message);
    });
}

// 添加拖放功能支持
function setupDragAndDrop() {
    const dropZones = document.querySelectorAll('.upload-drop-zone');
    
    dropZones.forEach((zone, index) => {
        const fileInput = index === 0 ? document.getElementById('file') : document.getElementById('file2');
        const statusId = index === 0 ? 'file1-status' : 'file2-status';
        
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.border = '2px dashed #007bff';
            this.style.backgroundColor = '#f0f8ff';
        });
        
        zone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.border = '2px dashed #ddd';
            this.style.backgroundColor = '';
        });
        
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.border = '2px dashed #ddd';
            this.style.backgroundColor = '';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                
                // 触发change事件
                const event = new Event('change');
                fileInput.dispatchEvent(event);
                
                // 更新状态
                document.getElementById(statusId).innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在处理...';
            }
        });
        
        // 点击图片也可以选择文件
        zone.addEventListener('click', function() {
            fileInput.click();
        });
    });
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}