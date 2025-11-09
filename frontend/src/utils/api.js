/**
 * API调用工具函数
 * 封装与后端FastAPI的通信
 */
import axios from 'axios';

// API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 创建axios实例
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

/**
 * 上传热力图数据
 * @param {string} anonymousId - 用户匿名ID
 * @param {Array} heatmapData - 热力图数据
 * @returns {Promise} API响应
 */
export async function uploadHeatmapData(anonymousId, heatmapData) {
    try {
        const response = await apiClient.post('/api/heatmap/data', {
            anonymous_id: anonymousId,
            data: heatmapData
        });
        return response.data;
    } catch (error) {
        console.error('热力图数据上传失败:', error);
        throw error;
    }
}

/**
 * 获取全局热力图数据
 * @returns {Promise} 热力图数据
 */
export async function getGlobalHeatmap() {
    try {
        const response = await apiClient.get('/api/heatmap');
        return response.data;
    } catch (error) {
        console.error('获取热力图数据失败:', error);
        throw error;
    }
}

/**
 * 请求加入匿名环
 * @param {string} anonymousId - 用户匿名ID
 * @param {string} publicKey - 用户公钥
 * @param {string} userLevel - 用户水平
 * @returns {Promise} 环信息
 */
export async function requestRing(anonymousId, publicKey, userLevel = 'medium') {
    try {
        const response = await apiClient.post('/api/leaderboard/request-ring', {
            anonymous_id: anonymousId,
            public_key: publicKey,
            user_level: userLevel
        });
        return response.data;
    } catch (error) {
        console.error('请求环失败:', error);
        throw error;
    }
}

/**
 * 提交环签名成绩
 * @param {string} ringId - 环ID
 * @param {number} totalDistance - 总距离
 * @param {number} averagePace - 平均配速
 * @param {string} signature - 环签名
 * @returns {Promise} API响应
 */
export async function submitScore(groupName, totalDistance, averagePace, groupSignature) {
    try {
        const response = await apiClient.post('/api/leaderboard/submit-score', {
            group_name: groupName,
            total_distance: totalDistance,
            average_pace: averagePace,
            group_signature: groupSignature
        });
        return response.data;
    } catch (error) {
        console.error('成绩提交失败:', error);
        throw error;
    }
}

/**
 * 提交真正环签名成绩
 * @param {string} ringId
 * @param {number} totalDistance
 * @param {number} averagePace
 * @param {{c0:string,s:string[]}} signature
 */
export async function submitScoreRing(ringId, totalDistance, averagePace, signature) {
    try {
        const response = await apiClient.post('/api/leaderboard/submit-score-ring', {
            ring_id: ringId,
            total_distance: totalDistance,
            average_pace: averagePace,
            signature
        });
        return response.data;
    } catch (error) {
        console.error('环签名成绩提交失败:', error);
        throw error;
    }
}

/**
 * 获取排行榜数据
 * @returns {Promise} 排行榜数据
 */
export async function getLeaderboard() {
    try {
        const response = await apiClient.get('/api/leaderboard');
        return response.data;
    } catch (error) {
        console.error('获取排行榜失败:', error);
        throw error;
    }
}

/**
 * 用户登录（或注册）以获取固定队伍
 * @param {string} anonymousId
 * @param {string} publicKey
 * @param {string} userLevel
 */
export async function loginUser(anonymousId, publicKey, userLevel='medium') {
    try {
        const response = await apiClient.post('/api/user/login', {
            anonymous_id: anonymousId,
            public_key: publicKey,
            user_level: userLevel
        });
        return response.data;
    } catch (error) {
        console.error('用户登录失败:', error);
        throw error;
    }
}