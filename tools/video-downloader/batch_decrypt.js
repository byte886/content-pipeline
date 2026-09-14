/**
 * 批量解密脚本 - 一次启动Node.js进程解密多个视频文件
 * 
 * 用法: node batch_decrypt.js <解密列表JSON文件>
 * 
 * JSON格式: [{"decode_key": "123456", "filepath": "/path/to/video.mp4"}, ...]
 * 
 * 优化点:
 * 1. 只启动一次Node.js进程，避免重复加载WASM
 * 2. 解密数组缓存（相同DecodeKey复用）
 * 3. 批量处理，减少进程启动开销
 */

const fs = require('fs');
const vm = require('vm');
const path = require('path');

// 加载WASM解密模块
const decryptCodePath = path.join(__dirname, 'decrypt_node.js');
const decryptCode = fs.readFileSync(decryptCodePath, 'utf8');

const sandbox = {
    console: { log: () => {}, error: () => {}, warn: () => {} },
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    setInterval: setInterval,
    clearInterval: clearInterval,
    __dirname: __dirname,
    __filename: __filename,
    process: process,
    Buffer: Buffer,
    Uint8Array: Uint8Array,
    Int32Array: Int32Array,
    Float64Array: Float64Array,
    DataView: DataView,
    TextDecoder: TextDecoder,
    TextEncoder: TextEncoder,
    performance: { now: () => Date.now() },
    crypto: { getRandomValues: (arr) => require('crypto').randomFillSync(arr) },
    location: { href: 'http://localhost/', origin: 'http://localhost' },
    navigator: { userAgent: 'Mozilla/5.0', hardwareConcurrency: 4 },
    document: { 
        createElement: () => ({ style: {}, appendChild: () => {} }),
        body: { appendChild: () => {} },
        getElementById: () => null
    },
    window: {},
    self: {},
    importScripts: () => {}
};
sandbox.global = sandbox;
sandbox.self = sandbox;
sandbox.window = sandbox;

const context = vm.createContext(sandbox);
vm.runInContext(decryptCode, context);

// 解密数组缓存
const decodeBytesCache = new Map();

function waitForWasm(maxWait = 15000) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const check = () => {
            if (sandbox.Module && sandbox.Module.WxIsaac64) {
                resolve();
            } else if (Date.now() - start > maxWait) {
                reject(new Error('WASM初始化超时'));
            } else {
                setTimeout(check, 100);
            }
        };
        check();
    });
}

function getDecodeBytes(seed) {
    // 检查缓存
    if (decodeBytesCache.has(seed)) {
        return decodeBytesCache.get(seed);
    }
    
    const decryptor = new sandbox.Module.WxIsaac64(seed);
    decryptor.generate(131072);
    const bytes = Buffer.from(sandbox.decryptor_array);
    
    // 存入缓存
    decodeBytesCache.set(seed, bytes);
    return bytes;
}

function decryptFile(filepath, seed) {
    if (!fs.existsSync(filepath)) {
        return { success: false, error: '文件不存在' };
    }
    
    const decodeBytes = getDecodeBytes(seed);
    const fd = fs.openSync(filepath, 'r+');
    const fileBytes = Buffer.alloc(decodeBytes.length);
    const bytesRead = fs.readSync(fd, fileBytes, 0, decodeBytes.length, 0);
    
    const xorResult = Buffer.alloc(bytesRead);
    for (let i = 0; i < bytesRead; i++) {
        xorResult[i] = decodeBytes[i] ^ fileBytes[i];
    }
    
    fs.writeSync(fd, xorResult, 0, bytesRead, 0);
    fs.closeSync(fd);
    
    return { success: true, bytesDecrypted: bytesRead };
}

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.log('用法: node batch_decrypt.js <解密列表JSON文件>');
        console.log('JSON格式: [{"decode_key": "123456", "filepath": "/path/to/video.mp4"}, ...]');
        process.exit(1);
    }
    
    const listFile = args[0];
    const decryptList = JSON.parse(fs.readFileSync(listFile, 'utf8'));
    
    console.log(`批量解密: ${decryptList.length} 个文件`);
    console.log('等待WASM初始化...');
    
    await waitForWasm();
    console.log('WASM初始化完成，开始解密...\n');
    
    let successCount = 0;
    let failCount = 0;
    const startTime = Date.now();
    
    for (let i = 0; i < decryptList.length; i++) {
        const item = decryptList[i];
        const { decode_key, filepath } = item;
        
        try {
            const result = decryptFile(filepath, decode_key);
            if (result.success) {
                successCount++;
                if ((i + 1) % 10 === 0 || i === decryptList.length - 1) {
                    console.log(`[${i + 1}/${decryptList.length}] 成功: ${path.basename(filepath)} (${result.bytesDecrypted}字节)`);
                }
            } else {
                failCount++;
                console.error(`[${i + 1}/${decryptList.length}] 失败: ${path.basename(filepath)} - ${result.error}`);
            }
        } catch (e) {
            failCount++;
            console.error(`[${i + 1}/${decryptList.length}] 错误: ${path.basename(filepath)} - ${e.message}`);
        }
    }
    
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`\n解密完成!`);
    console.log(`  成功: ${successCount}`);
    console.log(`  失败: ${failCount}`);
    console.log(`  耗时: ${elapsed}秒`);
    console.log(`  平均: ${(elapsed / decryptList.length).toFixed(2)}秒/个`);
    console.log(`  缓存命中: ${decodeBytesCache.size} 个唯一密钥`);
}

main().catch(e => {
    console.error('致命错误:', e.message);
    process.exit(1);
});
