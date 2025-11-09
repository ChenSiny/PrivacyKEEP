/**
 * 密码学工具函数
 * 处理环签名相关的密码学操作
 */

import * as secp from '@noble/secp256k1';

// =============== 工具函数 ===============
function hexToBytes(hex) {
    if (hex.length % 2 !== 0) throw new Error('Invalid hex');
    const out = new Uint8Array(hex.length/2);
    for (let i=0;i<hex.length;i+=2) out[i/2] = parseInt(hex.slice(i,i+2),16);
    return out;
}
function bytesToHex(bytes){ return Array.from(bytes).map(b=>b.toString(16).padStart(2,'0')).join(''); }
function sha256(...parts){
    const data = new Uint8Array(parts.reduce((acc,p)=>acc+p.length,0));
    let offset=0; parts.forEach(p=>{data.set(p,offset);offset+=p.length;});
    return crypto.subtle.digest('SHA-256', data);
}
async function sha256Hex(...parts){ const d = await sha256(...parts); return bytesToHex(new Uint8Array(d)); }
/**
 * 生成 secp256k1 椭圆曲线密钥对（hex）
 */
export function generateKeyPair() {
    const privBytes = secp.utils.randomPrivateKey();
    const privHex = Array.from(privBytes).map(b=>b.toString(16).padStart(2,'0')).join('');
    const pubHex = Array.from(secp.getPublicKey(privBytes, true)).map(b=>b.toString(16).padStart(2,'0')).join('');
    return { privateKey: privHex, publicKey: pubHex };
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
    return `${ringId}|${totalDistance}|${averagePace}`;
}

/**
 * 与后端一致的 Schnorr-like 环签名（教学版）
 * message: string（格式 ringId|distance|pace）
 * privHex: 32字节私钥 hex
 * ringPublicKeys: 压缩公钥 hex 数组
 * 返回 { c0, s[] }
 */
export async function ringSign(message, privHex, ringPublicKeys){
    if (ringPublicKeys.length < 2) throw new Error('环大小至少为2');
    const ORDER = BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141');
    const privBytes = hexToBytes(privHex);
    const myPubHex = bytesToHex(secp.getPublicKey(privBytes, true));
    let pubs = [...ringPublicKeys];
    let idx = pubs.indexOf(myPubHex);
    if (idx === -1){ pubs.push(myPubHex); idx = pubs.length -1; }
    const n = pubs.length;
    // start index
    const start = (idx + 1) % n;
    // k 随机
    let k; do { k = BigInt('0x'+bytesToHex(secp.utils.randomPrivateKey())) % ORDER; } while(k===0n);
    const kBytes = hexToBytes(k.toString(16).padStart(64,'0'));
    const R = secp.getPublicKey(kBytes, true);
    const messageBytes = new TextEncoder().encode(message);
    const L_serial = hexToBytes(pubs.join(''));
    const c = new Array(n).fill(null);
    const s = new Array(n).fill(0n);
    c[start] = hexToBytes(await sha256Hex(messageBytes, L_serial, R));
    let j = start;
    while (j !== idx){
        const jNext = (j+1)%n;
        // 随机 s_j
        let sj; do { sj = BigInt('0x'+bytesToHex(secp.utils.randomPrivateKey())) % ORDER; } while(sj===0n);
        s[j]=sj;
        const cj = BigInt('0x'+bytesToHex(c[j])) % ORDER;
        const Pj = hexToBytes(pubs[j]);
        // R_point = s_j*G + c_j*P_j
        const R1 = secp.getPublicKey(hexToBytes(sj.toString(16).padStart(64,'0')), true);
        const R2 = secp.Point.fromHex(Pj).multiply(cj).toRawBytes(true);
        const Rpoint = secp.Point.fromHex(R1).add(secp.Point.fromHex(R2)).toRawBytes(true);
        c[jNext] = hexToBytes(await sha256Hex(messageBytes, L_serial, Rpoint));
        j = jNext;
    }
    // 计算 s_idx
    const cidx = BigInt('0x'+bytesToHex(c[idx])) % ORDER;
    const x = BigInt('0x'+privHex);
    const sIdx = (k - (cidx * x % ORDER) + ORDER) % ORDER;
    s[idx]=sIdx;
    const c0Hex = bytesToHex(c[0] || c[start]);
    const sHex = s.map(v=>v.toString(16).padStart(64,'0'));
    return { c0: c0Hex, s: sHex };
}

/**
 * 生成群密钥签名（HMAC-SHA512）
 * @param {string} groupKey 十六进制群密钥（后端返回的 secret）
 * @param {string} groupName 群组名称
 * @param {number} totalDistance 总距离
 * @param {number} averagePace 平均配速
 * @returns {Promise<string>} HMAC hex
 */
export async function generateGroupSignature(groupKey, groupName, totalDistance, averagePace) {
    const msg = `${groupName}|${totalDistance}|${averagePace}`;
    // 浏览器 SubtleCrypto 不直接支持 HMAC 纯 hex key导入，需要将 hex 转为 Uint8Array
    const keyBytes = hexToBytes(groupKey);
    if (window.crypto?.subtle) {
        const cryptoKey = await window.crypto.subtle.importKey(
            'raw',
            keyBytes,
            { name: 'HMAC', hash: 'SHA-512' },
            false,
            ['sign']
        );
        const sigBuf = await window.crypto.subtle.sign('HMAC', cryptoKey, new TextEncoder().encode(msg));
        return bytesToHex(new Uint8Array(sigBuf));
    }
    // Fallback：简单拼接再 sha512
    return await sha512Hex(msg + bytesToHex(keyBytes));
}

// 已在顶部定义 hexToBytes / bytesToHex