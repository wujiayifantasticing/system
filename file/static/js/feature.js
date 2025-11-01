// // 处理文件选择及验证
// function handleFileChange(input) {
//     const file = input.files[0];
//     const fileName = file ? file.name : "未选择文件";
//     document.querySelector('.file-name').textContent = fileName;

//     if (file) {
//         // 文件类型验证
//         const validImageTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp'];
//         if (!validImageTypes.includes(file.type)) {
//             alert('请上传JPG, PNG或BMP格式的图片');
//             input.value = '';  // 清空文件选择
//             return;
//         }

//         // 文件大小验证 (最大限制800KB)
//         const maxSize = 800 * 1024; // 800KB
//         if (file.size > maxSize) {
//             alert('文件大小不能超过800KB');
//             input.value = '';  // 清空文件选择
//             return;
//         }

//         // 显示预览图片
//         const reader = new FileReader();
//         reader.onload = function(e) {
//             const previewImage = document.getElementById('previewImage');
//             previewImage.src = e.target.result;
//             previewImage.style.display = 'block';  // 显示预览图片
//         };
//         reader.readAsDataURL(file);

//         //
//     }
// }

// //

// // 处理人脸特征分析
// function analyzeFeature() {
//     const fileInput = document.getElementById('fileInput');
//     const file = fileInput.files[0];

//     // 如果未选择文件，则提示用户
//     if (!file) {
//         alert('请先选择一个文件进行分析');
//         return;
//     }

//     // 显示加载提示
//     document.getElementById('loading').style.display = 'block';

//     // 创建 FormData 对象，准备上传
//     const formData = new FormData();
//     formData.append('file', file);

//     // 发起分析请求
//     fetch('/feature_analysis', {
//         method: 'POST',
//         body: formData
//     })
//     .then(response => {
//         if (!response.ok) {
//             throw new Error('网络错误，无法获取数据');
//         }
//         return response.json();
//     })
//     .then(res => {
//         document.getElementById('loading').style.display = 'none'; // 隐藏加载提示

//         if (res.flag === 'true' && res.data) {
//             // 更新页面内容
//             document.getElementById('age-value').textContent = res.data['年龄'] || '--';
//             document.getElementById('beauty-value').textContent = res.data['颜值'] || '--';
//             document.getElementById('gender-value').textContent = res.data['性别'] || '--';
//             document.getElementById('expression-value').textContent = res.data['表情'] || '--';
//         } else {
//             alert(res.msg || '分析失败');
//         }
//     })
//     .catch(error => {
//         document.getElementById('loading').style.display = 'none'; // 隐藏加载提示
//         console.error('分析请求失败:', error);
//         alert('分析请求失败，请重试');
//     });
// }


// 处理文件选择及验证
function handleFileChange(input) {
    const file = input.files[0];
    const fileName = file ? file.name : "未选择文件";
    document.querySelector('.file-name').textContent = fileName;

    if (file) {
        // 文件类型验证
        const validImageTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp'];
        if (!validImageTypes.includes(file.type)) {
            alert('请上传JPG, PNG或BMP格式的图片');
            input.value = '';  // 清空文件选择
            return;
        }

        // 文件大小验证 (最大限制800KB)
        const maxSize = 800 * 1024; // 800KB
        if (file.size > maxSize) {
            alert('文件大小不能超过800KB');
            input.value = '';  // 清空文件选择
            return;
        }

        // 显示预览图片
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewImage = document.getElementById('previewImage');
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';  // 显示预览图片
        };
        reader.readAsDataURL(file);

        // 自动上传文件
        uploadFile(file);
    }
}

// 上传文件到服务器
function uploadFile(file) {
    const formData = new FormData();
    formData.append('fileInput', file);
    formData.append('type', 'feature');
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('文件上传失败: ' + data.error);
        } else {
            console.log('文件上传成功:', data.path);
        }
    })
    .catch(error => {
        console.error('上传错误:', error);
        alert('上传过程中发生错误');
    });
}

// 处理人脸特征分析
function analyzeFeature() {
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // 禁用按钮并显示加载状态
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '分析中...';
    document.getElementById('loading').style.display = 'block';

    // 发起分析请求到正确的端点
    fetch('/feature', {
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
    .then(res => {
        // 恢复按钮状态
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '识别';
        document.getElementById('loading').style.display = 'none';

        if (res.flag === 'true' && res.data) {
            // 更新页面内容
            document.getElementById('age-value').textContent = res.data['年龄'] || '--';
            document.getElementById('beauty-value').textContent = res.data['颜值'] || '--';
            document.getElementById('gender-value').textContent = res.data['性别'] || '--';
            document.getElementById('expression-value').textContent = res.data['表情'] || '--';
        } else {
            alert(res.msg || '分析失败');
        }
    })
    .catch(error => {
        // 恢复按钮状态
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '识别';
        document.getElementById('loading').style.display = 'none';
        
        console.error('分析请求失败:', error);
        alert('分析请求失败，请重试');
    });
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('人脸特征分析页面已加载');
});