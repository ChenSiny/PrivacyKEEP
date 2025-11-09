/**
 * 密码学工具函数
 * 处理环签名相关的密码学操作
 */

/**
 * 生成椭圆曲线密钥对
 * @returns {Object} 包含私钥和公钥的对象
 */
export function generateKeyPair() {
    // 在实际系统中，这里应该使用真正的密码学库
    // 这里使用模拟实现用于演示
    const privateKey = 'mock_private_key_' + Math.random().toString(36).substr(2, 9);
    const publicKey = 'mock_public_key_' + Math.random().toString(36).substr(2, 9);
    
    return {
        privateKey: privateKey,
        publicKey: publicKey
    };
}

/**
 * 模拟环签名生成
 * @param {string} message - 要签名的消息
 * @param {string} privateKey - 签名者私钥
 * @param {Array} publicKeys - 环公钥列表
 * @returns {string} 环签名（十六进制格式）
 */
export function simulateRingSignature(message, privateKey, publicKeys) {
    // 后端验证逻辑要求签名为 hex 字符串并且长度≥64字节（我们在降级逻辑里用 sha512）
    // 这里用浏览器的 SubtleCrypto 生成一个 SHA-512 哈希作为“模拟签名”占位。
    const encoder = new TextEncoder();
    const payload = JSON.stringify({
        message,
        ringSize: publicKeys.length,
        ts: Date.now(),
        keyHint: privateKey.slice(-8)
    });
    return sha512Hex(payload);
}

async function sha512Hex(str) {
    if (window.crypto && window.crypto.subtle) {
        const data = new TextEncoder().encode(str);
        const digest = await window.crypto.subtle.digest('SHA-512', data);
        const bytes = Array.from(new Uint8Array(digest));
        return bytes.map(b => b.toString(16).padStart(2, '0')).join('');
    } else {
        // Fallback：简单字符转码再拉长，保证长度≥128 hex
        const base = Array.from(str).map(c => c.charCodeAt(0).toString(16).padStart(2,'0')).join('');
        return (base + base + base).slice(0, 128); // 截断到128字符
    }
}

/**
 * 准备环签名消息
 * @param {string} ringId - 环ID
 * @param {number} totalDistance - 总距离
 * @param {number} averagePace - 平均配速
 * @returns {string} 用于签名的消息字符串
 */
export function prepareSignatureMessage(ringId, totalDistance, averagePace) {
    return `${ringId}${totalDistance}${averagePace}`;
}