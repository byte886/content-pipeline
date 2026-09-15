const fs = require('fs');
const vm = require('vm');

const decryptCode = fs.readFileSync('/tmp/decrypt_node.js', 'utf8');

const sandbox = {
    console: { log: () => {}, error: () => {}, warn: () => {} },
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    setInterval: setInterval,
    clearInterval: clearInterval,
    __dirname: '/tmp',
    __filename: '/tmp/decrypt.js',
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

function waitForWasm(maxWait = 10000) {
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
    const decryptor = new sandbox.Module.WxIsaac64(seed);
    decryptor.generate(131072);
    return Buffer.from(sandbox.decryptor_array);
}

function decryptFile(filepath, seed) {
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
    
    return { bytesDecrypted: bytesRead, decodeBytes: decodeBytes };
}

async function main() {
    await waitForWasm();
    
    const args = process.argv.slice(2);
    if (args.length >= 2) {
        const seed = args[0];
        const filepath = args[1];
        console.log(`解密文件: ${filepath}`);
        console.log(`Seed: ${seed}`);
        const result = decryptFile(filepath, seed);
        console.log(`已解密前${result.bytesDecrypted}字节`);
        console.log(`解密密钥前16字节(hex): ${result.decodeBytes.slice(0, 16).toString('hex')}`);
    } else if (args.length === 1) {
        const seed = args[0];
        const bytes = getDecodeBytes(seed);
        console.log(`Seed: ${seed}`);
        console.log(`数组长度: ${bytes.length}`);
        console.log(`前16字节(hex): ${bytes.slice(0, 16).toString('hex')}`);
        console.log(`base64前80字符: ${bytes.toString('base64').substring(0, 80)}`);
    } else {
        console.log('用法: node wechat_decrypt.js <seed> [文件路径]');
    }
}

main().catch(e => {
    console.error('错误:', e.message);
    process.exit(1);
});
