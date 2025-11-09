/**
 * 差分隐私处理工具
 * 实现拉普拉斯机制为数据添加噪声
 */

/**
 * 生成拉普拉斯噪声
 * @param {number} scale - 噪声尺度参数
 * @returns {number} 拉普拉斯噪声值
 */
function generateLaplaceNoise(scale) {
    const u = Math.random() - 0.5;
    return -scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u));
}

/**
 * 对计数数据添加拉普拉斯噪声实现差分隐私
 * @param {number} actualCount - 实际计数值
 * @param {number} epsilon - 隐私预算，越小隐私保护越强
 * @param {number} sensitivity - 敏感度，通常为1
 * @returns {number} 加噪后的数据
 */
export function addLaplaceNoise(actualCount, epsilon = 1.0, sensitivity = 1) {
    const scale = sensitivity / epsilon;
    const noise = generateLaplaceNoise(scale);
    const noisyCount = actualCount + noise;
    
    // 确保结果非负
    return Math.max(0, noisyCount);
}

/**
 * 处理轨迹数据，进行区块化和差分隐私加噪
 * @param {Array} trajectory - 原始轨迹点数组
 * @param {number} epsilon - 隐私预算
 * @returns {Array} 加噪后的区块数据 [{x, y, weight}]
 */
export function processTrajectoryWithDP(trajectory, epsilon = 1.0) {
    const gridCounts = {};
    
    // 1. 区块化：统计每个网格的访问次数
    trajectory.forEach(point => {
        const grid = gpsToGrid(point.lat, point.lng);
        const gridKey = `${grid.x},${grid.y}`;
        gridCounts[gridKey] = (gridCounts[gridKey] || 0) + 1;
    });
    
    // 2. 差分隐私加噪
    const processedData = [];
    Object.entries(gridCounts).forEach(([gridKey, count]) => {
        const [x, y] = gridKey.split(',').map(Number);
        const noisyWeight = addLaplaceNoise(count, epsilon);
        
        // 只保留权重显著大于0的区块（优化数据传输）
        if (noisyWeight > 0.1) {
            processedData.push({
                x: x,
                y: y,
                weight: parseFloat(noisyWeight.toFixed(3))
            });
        }
    });
    
    return processedData;
}

// 导入GPS工具函数
import { gpsToGrid } from './gps.js';