# 视频号短视频解密技术方案（已端到端验证）

> **文档类型**：Research / 技术结论（authoritative）
> **状态**：✅ 已验证（2026-09-21，真实样本端到端跑通）
> **适用**：微信视频号「短视频」加密流；直播回放为明文 MP4，不适用本方案
> **相关**：采集 SOP 见 [`../guides/wechat-channels-capture.md`](../guides/wechat-channels-capture.md)；高质量规格见 [`video-quality-url.md`](video-quality-url.md)

---

## 1. 结论（一句话）

视频号短视频是 **Isaac64 PRNG 流加密**：以播放接口返回的 `decode_key`（9–10 位数字串）为 seed，经微信官方 wasm 中的 `WxIsaac64` 生成 **131072 字节（128KB）密钥流**，字节序 reverse 后与文件**前 128KB 逐字节 XOR**；128KB 之后为明文，原样保留。解密后头部应为标准 MP4（偏移 4 处为 `ftyp`）。

**不是 AES，不是整文件加密，只加密头部 128KB。**

---

## 2. 算法细节

### 2.1 密钥流生成（官方 worker_release.js 调用契约，逐字关键行）

```js
// 初始化：seed 即 decode_key（数字字符串）
initDecrtptor = async e => {
  p.decryptor = await new Module.WxIsaac64(e);
  await p.decryptor.generate(131072);   // 固定 2^17 = 131072 字节
  p.decryptor.delete();
}

// wasm 通过导入回调把 HEAPU8 数据交给 JS，JS 侧 reverse 字节序
wasm_isaac_generate = (t, e) => {
  p.decryptor_array = new Uint8Array(e);
  var r = new Uint8Array(Module.HEAPU8.buffer, t, e);
  p.decryptor_array.set(r.reverse());   // 必须 reverse
}

// 解密：仅对前 131072 字节 XOR
M(t, e) {
  var r = new Uint8Array(t);
  for (n = 0; n < t.byteLength && e + n < p.decryptor_array.length; n++)
    r[n] ^= p.decryptor_array[n];
  return r;
}
```

要点：
- seed = `decode_key`，按**数字字符串**传入（如 `"267631937"`），不是整数。
- 密钥流长度恒为 `131072`。
- 回调里的 `.reverse()` 不能漏；少了它解出的不是 MP4。
- 仓内自包含解密器 `decrypt_node.js` 内部已含 reverse，调用方无需再处理。

### 2.2 响应头佐证

短视频换签直链的 Range 响应头明确给出加密信息：

```
X-Encflag: 1                 # 1 = 头部加密
X-Enclen: 131072             # 加密长度 = 128KB
X-Snsvideoflag: xWT112       # 本次返回的规格标识
Content-Range: bytes 0-131071/3988294
```

---

## 3. 工具链（仓内，离线可跑，无需浏览器/外部 .wasm）

目录：`platforms/wechat_channels/video-downloader/`

| 文件 | 作用 | 用法 |
|---|---|---|
| `decrypt_node.js` | 自包含 wasm2js 解密模块（5.2MB，内嵌 Isaac64/wasm，全局暴露 `Module.WxIsaac64` 与 `decryptor_array`，已含 reverse） | 被下面两个脚本 vm 加载，不直接用 |
| `wechat_decrypt.js` | 单文件解密（原地改前 128KB） | `node wechat_decrypt.js <seed> <file.mp4>` |
| `batch_decrypt.js` | 批量解密，**单进程加载一次 wasm + 按 seed 缓存密钥流** | `node batch_decrypt.js list.json`，list 元素 `{"decode_key":"...","filepath":"..."}` |
| `batch_download_v4.py` | 下载→解密→ftyp/md5 校验→命名去重→结果 manifest 的完整编排 | 见下 |

`batch_download_v4.py`：

```bash
# 输入 capture 落库的 json（list，每条含 url/decode_key/description/size/md5）
python3 batch_download_v4.py <capture.json> <输出目录> short   # 短视频
python3 batch_download_v4.py <capture.json> <输出目录> live    # 直播回放(明文)
# 可选环境变量：
#   WC_PROXY=http://127.0.0.1:8899  下载走代理（默认直连，finder.video.qq.com 国内 CDN 直连即可）
#   WC_LIMIT=N                       只处理前 N 条（验证用）
#   WC_NODE=/path/to/node            指定 node
# 质量：第 5 个位置参数 default|max(xWT111)|min(xWT128)
```

> 下载请求头：`Referer: https://channels.weixin.qq.com/` + Chrome UA；带 token 的换签直链支持 `Range`。
> 换签 URL 有时效（含 token/svrnonce），**捕获后应尽快下载**，过期需重新播放/滚动捕获。

---

## 4. 验证证据（2026-09-21，样本 decode_key=267631937）

1. **密钥流一致性**：仓内 `decrypt_node.js` 与从官方 CDN 拉取的独立 `wasm_video_decode.wasm`（经 Node harness 加载）对同一 seed 产出的 131072B 密钥流**逐字节不同数 = 0**；若再手动 reverse 反而有 130556 字节差异（证明 reverse 已内置且必需）。
2. **头部解密**：Range 下载前 128KB 加密头（`86 92 a5 91 …`，前 2 字节恰等于密钥流前 2 字节，因 MP4 box size 高 2 字节为 `00 00`），XOR 后：
   ```
   00000020 66747970 69736f6d 00000200   .. ftyp isom
   69736f6d 69736f32 61766331 6d703431   isomiso2avc1mp41
   00012446 6d6f6f76 ...                 ..$F moov
   ```
   `file` 识别为 `ISO Media, MP4 Base Media v1 [ISO 14496-12:2003]`。
3. **整文件端到端**：完整下载（3,988,294B，xWT112 标清）→ 解密 → ffprobe：
   - `codec_name=h264, width=1080, height=1920`（竖屏）
   - 音频 `codec_name=aac`
   - `duration=134.861s`，与捕获记录 `videoPlayLen=134` **吻合**
   - 标准可播放 MP4。
4. 批量脚本 `batch_decrypt.js` 与单文件 `wechat_decrypt.js` 均实测解出 ftyp。

---

## 5. 规格与 md5 对账（重要口径）

- 换签直链默认返回 **xWT112 标清**（样本 3.8MB）；捕获记录里的 `size=13,680,074`、`md5=d0cd…` 对应的是 **best_format 高清（约 13.7MB）**，二者是同一视频的不同规格。
- 因此用默认 URL 下载后，md5 与记录里 best_format 的 md5 **不一致是正常现象**，脚本会标注 `md5规格不同`，不判为失败。
- 待办：要做整文件 md5 强对账，需先构造 best_format 对应规格的 URL（解析 `other_data.best_format` / `wx_file_formats` 中的 xWT1xx 列表，或高质量参数，见 [`video-quality-url.md`](video-quality-url.md)），再按该规格 size/md5 对账。

---

## 6. 当前覆盖现状（「交易的游戏」视频号 = 公众号「顶底之王」）

| 类别 | 总数 | 可立即闭环 | 缺口 |
|---|---|---|---|
| 短视频（加密） | 340 | 15 条（capture 落库同时带换签 token 直链 + decode_key） | 其余约 325 条需在视频号「视频」tab **缓慢滚动让卡片曝光预览 / 逐条播放**，使播放接口返回 media JSON（含 urlToken + decodeKey），由捕获代理落库 |
| 直播回放（明文） | 27 | 27 条（换签直链，无需解密直接下） | — |

- 换签直链与 decode_key 来自捕获代理 `-short-probe` 注入的静默探针（HTMLMediaElement.src / handleMedia），属**网络层注入**，不是模拟 GUI；微信内所有 GUI 动作（搜索、进视频号、切 tab、滚动、播放、重启微信）由**用户手动**完成（安全约束：AI 不操作腾讯桌面客户端 GUI）。
- 代理须在**整个微信 Cmd+Q 重启前启动**（魔改 XWeb NetworkService 只在进程启动时读系统代理）；详见采集 SOP。

---

## 7. 安全：捕获产物不入库

捕获落库的 `capture_*.json`、`*_slim.json`/`*_manifest.json`（回放）、`run_*.out`、`*.log` 含**临时签名票据**（`token` / `sign` / `svrbypass` / `svrnonce`），已在 `platforms/wechat_channels/video-capture/.gitignore` 中排除，**禁止提交 public 仓**。
可入库的只有**脱敏台账**（命名 `catalog_*.json` / `registry_*.json`，剥离签名 URL，仅留 oid/标题/时长/size/md5/encfilekey 等元数据）。
> 注意：早期 `capture_result_20260918.json`、`capture_wushi_20260918.json` 曾被跟踪入库（含历史签名票据，票据短期过期失效）；已 `git rm --cached` 停止跟踪当前版本，**git 历史中的旧版本是否清理需用户决策**（改写公开历史需 force push）。

---

## 8. 参考来源

- 开源解密仓：`https://github.com/Evil0ctal/WeChat-Channels-Video-File-Decryption`
  （`api-service/lib/decrypt.js` 仅 XOR 层；`wechat_files/worker_release.js` 是 wasm 调用胶水；`wasm_video_decode.wasm/.js` 为官方模块）
- 逆向分析：`https://www.aynakeya.com/articles/ctf/wechat-video-encryption-reverse-engineer/`（佐证密钥流恒为 2^17、只加密头部）
- 官方 wasm CDN：`https://aladin.wxqcloud.qq.com/aladin/ffmepeg/video-decode/1.2.50/wasm_video_decode.js`
- res-downloader（捕获思路参考）：`https://github.com/putyy/res-downloader`
