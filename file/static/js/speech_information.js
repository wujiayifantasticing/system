// speech_information.js - 语音信息识别功能

// 处理文件选择和识别
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('audioFile'); // 注意：这里应该是audioFile不是fileInput
    const recognizeBtn = document.getElementById('recognizeBtn');
    const loadingDiv = document.getElementById('loading');
    const genderResult = document.getElementById('genderResult');
    const ageResult = document.getElementById('ageResult');
    const fileName = document.getElementById('fileName');

    if (fileInput && recognizeBtn) {
        // 文件选择事件
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                fileName.textContent = file.name;
                
                // 验证文件类型
                if (!file.name.toLowerCase().endsWith('.wav')) {
                    alert('请上传WAV格式的音频文件');
                    this.value = '';
                    fileName.textContent = '未选择文件';
                    return;
                }
            } else {
                fileName.textContent = '未选择文件';
            }
        });

        // 识别按钮点击事件
        recognizeBtn.addEventListener('click', function() {
            const file = fileInput.files[0];
            if (!file) {
                alert('请先选择音频文件');
                return;
            }

            // 文件类型验证
            if (!file.name.toLowerCase().endsWith('.wav')) {
                alert('请上传WAV格式的音频文件');
                return;
            }

            // 显示加载状态
            loadingDiv.style.display = 'block';
            recognizeBtn.disabled = true;
            recognizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 识别中...';

            // 准备表单数据
            const formData = new FormData();
            formData.append('file', file);

            // 发送识别请求
            fetch('/speech_information', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // 首先检查响应类型
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json();
                } else {
                    return response.text().then(text => {
                        throw new Error('服务器返回了HTML而不是JSON，请检查后端代码');
                    });
                }
            })
            .then(data => {
                // 隐藏加载状态
                loadingDiv.style.display = 'none';
                recognizeBtn.disabled = false;
                recognizeBtn.innerHTML = '<i class="fas fa-play"></i> 开始识别';

                if (data.success) {
                    // 更新识别结果
                    genderResult.textContent = data.gender_result;
                    ageResult.textContent = data.age_result;
                    
                    console.log('识别成功:', data);
                } else {
                    alert('识别失败: ' + data.error);
                    // 重置结果
                    genderResult.textContent = '--';
                    ageResult.textContent = '--';
                }
            })
            .catch(error => {
                // 隐藏加载状态
                loadingDiv.style.display = 'none';
                recognizeBtn.disabled = false;
                recognizeBtn.innerHTML = '<i class="fas fa-play"></i> 开始识别';
                
                console.error('请求失败:', error);
                alert('请求失败: ' + error.message);
            });
        });
    }
});

// 添加简单的动画效果
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
});