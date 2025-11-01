function navigate(path) {
    window.location.href = path;
}

// 初始化或获取存储的数据
function initializeStats() {
    // 如果localStorage中没有数据，设置初始值
    if (!localStorage.getItem('userCount')) {
        localStorage.setItem('userCount', '100');
        localStorage.setItem('todayQuestions', '50');
        localStorage.setItem('activeIndex', '75');
    }
    
    // 更新页面显示
    document.getElementById('userCount').textContent = localStorage.getItem('userCount');
    document.getElementById('todayQuestions').textContent = localStorage.getItem('todayQuestions');
    document.getElementById('activeIndex').textContent = localStorage.getItem('activeIndex');
}

// 页面加载时初始化数据
window.addEventListener('load', initializeStats);