/**
 * GPS数据处理工具
 * 负责位置坐标到区块编号的映射
 */

// 网格大小（度），越小网格越精细
const GRID_SIZE = 0.001;

/**
 * 将GPS坐标转换为网格区块编号
 * @param {number} lat - 纬度
 * @param {number} lng - 经度  
 * @param {number} gridSize - 网格大小
 * @returns {Object} 网格坐标 {x, y}
 */
export function gpsToGrid(lat, lng, gridSize = GRID_SIZE) {
    const x = Math.floor(lng / gridSize);
    const y = Math.floor(lat / gridSize);
    return { x, y };
}

/**
 * 模拟GPS轨迹数据生成
 * @param {string} type - 轨迹类型: 'circle', 'line', 'random'
 * @returns {Array} GPS点数组 [{lat, lng}]
 */
export function generateMockTrajectory(type = 'circle') {
    const points = [];
    const centerLat = 39.9042; // 北京纬度
    const centerLng = 116.4074; // 北京经度
    const radius = 0.0015; // 更小的半径，避免单步距离过大（约 167 米）

    switch (type) {
        case 'circle':
            // 生成圆形轨迹（更多点，单步更短）
            for (let i = 0; i < 120; i++) {
                const angle = (i * 3 * Math.PI) / 180; // 每步 3°
                const lat = centerLat + radius * Math.cos(angle);
                const lng = centerLng + radius * Math.sin(angle);
                points.push({ lat, lng });
            }
            break;

        case 'line':
            // 生成直线轨迹（更多点，单步更短 ~10m）
            for (let i = 0; i < 120; i++) {
                const lat = centerLat + (i * 0.0001);
                const lng = centerLng + (i * 0.0001);
                points.push({ lat, lng });
            }
            break;

        case 'random':
            // 生成随机轨迹（小步随机游走）
            let currentLat = centerLat;
            let currentLng = centerLng;
            
            for (let i = 0; i < 120; i++) {
                currentLat += (Math.random() - 0.5) * 0.00016; // 单步 ~10m 级别
                currentLng += (Math.random() - 0.5) * 0.00016;
                points.push({ 
                    lat: parseFloat(currentLat.toFixed(6)), 
                    lng: parseFloat(currentLng.toFixed(6)) 
                });
            }
            break;
    }

    return points;
}

/**
 * 计算运动统计信息
 * @param {Array} trajectory - 轨迹点数组
 * @returns {Object} 运动统计 {totalDistance, averagePace, duration}
 */
export function calculateWorkoutStats(trajectory) {
    // 简化版距离计算（实际应该使用Haversine公式）
    const totalDistance = (trajectory.length * 0.08).toFixed(2); // 模拟距离计算
    const duration = (trajectory.length * 10); // 模拟时长（秒）
    const averagePace = (duration / 60 / totalDistance).toFixed(2); // 分钟/公里
    
    return {
        totalDistance: parseFloat(totalDistance),
        averagePace: parseFloat(averagePace),
        duration: duration
    };
}

// 真实地理距离计算（Haversine）+ 真实用时（秒）
function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const toRad = v => v * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon/2)**2;
    return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * 真实统计：基于点间 Haversine 距离与真实经过秒数
 * @param {Array<{lat:number,lng:number}>} trajectory
 * @param {number} elapsedSeconds
 */
export function calculateWorkoutStatsReal(trajectory, elapsedSeconds=0) {
    if (!trajectory || trajectory.length < 2) {
        return { totalDistance: 0, averagePace: 0, duration: elapsedSeconds || 0 };
    }
    let meters = 0;
    for (let i=1;i<trajectory.length;i++) {
        const p1 = trajectory[i-1];
        const p2 = trajectory[i];
        meters += haversine(p1.lat, p1.lng, p2.lat, p2.lng);
    }
    const km = meters / 1000;
    const duration = elapsedSeconds;
    const pace = km > 0 ? (duration/60) / km : 0; // 分/公里
    return {
        totalDistance: +km.toFixed(3),
        averagePace: +pace.toFixed(2),
        duration
    };
}