async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        const currentOption = weeklyChart.getOption();
        const seriesData = currentOption.series[0].data;
        const todayUsage = seriesData[seriesData.length - 1];
        
        document.getElementById('userCount').textContent = data.userCount;
        document.getElementById('todayQuestions').textContent = todayUsage;
        
        const activeIndex = data.userCount ? 
            (todayUsage / data.userCount).toFixed(2) : 
            '0.00';
        document.getElementById('activeIndex').textContent = activeIndex;
    } catch (error) {
        console.error('获取统计数据失败:', error);
    }
}

// 初始化或获取折线图数据
function initWeeklyChart() {
    // 如果localStorage中没有图表数据，设置初始值
    if (!localStorage.getItem('weeklyUsageData')) {
        const initialData = {
            dates: getLastSevenDays(),  // 使用原有的日期生成函数
            values: [120, 200, 150, 180, 130, 220, 190]
        };
        localStorage.setItem('weeklyUsageData', JSON.stringify(initialData));
    }
    
    // 从localStorage获取数据
    const chartData = JSON.parse(localStorage.getItem('weeklyUsageData'));
    
    // 初始化图表
    const chart = echarts.init(document.getElementById('weeklyUsageChart'));
    
    const option = {
        title: {
            text: '近7天使用趋势',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: chartData.dates,
            boundaryGap: false
        },
        yAxis: {
            type: 'value',
            name: '使用次数'
        },
        series: [{
            data: chartData.values,
            type: 'line',
            smooth: true,
            itemStyle: {
                color: '#4e73df'
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(78,115,223,0.3)' },
                    { offset: 1, color: 'rgba(78,115,223,0)' }
                ])
            }
        }]
    };
    
    chart.setOption(option);
    return chart;
}

// 获取最近7天的日期
function getLastSevenDays() {
    const dates = [];
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    return dates;
}

// 更新图表数据
async function updateWeeklyChart(chart) {
    try {
        const response = await fetch('/api/weekly-usage');
        const data = await response.json();
        
        chart.setOption({
            series: [{
                data: data.usageCount
            }]
        });
    } catch (error) {
        console.error('获取周使用量数据失败:', error);
    }
}

// 修改页面加载初始化部分，将 weeklyChart 声明为全局变量
let weeklyChart;
document.addEventListener('DOMContentLoaded', () => {
    weeklyChart = initWeeklyChart();
    updateStats();
    
    window.addEventListener('resize', () => weeklyChart.resize());
}); 