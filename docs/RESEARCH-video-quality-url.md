# 高质量URL研究记录

> **文档类型**：技术研究
> **创建时间**：2026-09-15
> **状态**：研究中
> **问题**：当前下载的视频是低分辨率版本（2-5MB/个），原始视频可达48MB+

---

## 一、问题描述

当前通过MITM捕获的视频URL下载的是低分辨率版本：
- 下载大小：2-5MB/个
- 原始大小：可达48MB+（从视频元数据中获取）
- 分辨率差异明显

---

## 二、URL参数分析

### 2.1 完整URL参数

```
https://finder.video.qq.com/251/20302/stodownload
  ?encfilekey=<132字符加密密钥>
  &bizid=1023
  &dotrans=0
  &hy=SH
  &idx=1
  &uzid=1
  &token=<访问令牌>
  &basedata=<Base64编码的Protobuf数据>
  &sign=<签名>
  &web=1
  &extg=10f0000
  &svrbypass=<服务器绕过数据>
  &svrnonce=<服务器随机数>
```

### 2.2 关键参数说明

| 参数 | 说明 | 当前值 |
|------|------|--------|
| `encfilekey` | 加密文件密钥 | 132字符 |
| `idx` | 格式索引 | 1（测试发现不影响清晰度） |
| `dotrans` | 是否转码 | 0 |
| `basedata` | 格式信息（Protobuf） | 见下文 |
| `sign` | URL签名 | 基于完整URL计算 |

---

## 三、basedata解码结果

### 3.1 解码方式

basedata使用**URL安全Base64编码**，解码后是**Protobuf格式**数据。

### 3.2 Protobuf结构

```
Field 1 (varint): 3              ← 当前格式索引
Field 2 (string): "xWT113"       ← 当前格式标识
Field 4 (bytes): 格式列表        ← 所有可用格式
  - xWT113 (当前)
  - xWT112
  - xWT111
  - xWT128
  - xWT127
  - xWT126
  - xA0
  - xA2
Field 7 (bytes): 0802            ← 未知参数
Field 8 (bytes): <48字节数据>     ← 可能是签名/密钥
Field 9 (varint): 127            ← 未知参数
```

### 3.3 格式标识推测

| 格式标识 | 推测清晰度 | 备注 |
|----------|-----------|------|
| xWT111 | 标清 | 最常见 |
| xWT112 | 高清 | - |
| xWT113 | 超清/原始 | 当前使用 |
| xWT126 | 其他 | - |
| xWT127 | 其他 | - |
| xWT128 | 其他 | - |
| xA0 | 音频 | 可能是纯音频 |
| xA2 | 音频 | 可能是纯音频 |

---

## 四、测试结果

### 4.1 修改idx参数

- 测试idx=1,2,3
- 结果：**所有idx返回相同大小（2.32MB）**
- 结论：idx参数不影响清晰度

### 4.2 修改dotrans参数

- 测试dotrans=0,1
- 结果：待验证
- 推测：dotrans=1可能请求转码后的高清版本

### 4.3 X-snsvideoflag参数（已验证有效）

**发现来源**：RES Downloader源码 `core/resource.go` 第128-140行

**原理**：在URL后添加 `&X-snsvideoflag=<格式标识>` 来选择不同清晰度

**测试结果**（视频原始大小48.5MB）：

| 格式标识 | 下载大小 | 相对默认 |
|----------|---------|---------|
| xWT111 | 3.92MB | +69% |
| xWT112 | 3.01MB | +30% |
| xWT126 | 2.68MB | +15% |
| xWT113 | 2.32MB | 默认（当前） |
| xWT127 | 2.15MB | -7% |
| xWT128 | 1.63MB | -30% |

**结论**：
- xWT111是最大的格式，比默认大69%
- 但所有格式都远小于原始48.5MB，说明这些都是转码后的版本
- 原始版本可能需要Quality=1方式（只保留encfilekey+token）

**RES Downloader的Quality映射**：
- Quality=1: 只保留encfilekey+token（推测为原始版本）
- Quality=2: X-snsvideoflag=format[0]（xWT111，最大）
- Quality=3: X-snsvideoflag=format[len/2]（xWT113，中间）
- Quality=4: X-snsvideoflag=format[len-1]（xWT128，最小）

---

## 五、获取高质量URL的可能方案

### 方案1：修改basedata中的格式选择

修改basedata的Field 1（格式索引）和Field 2（格式标识），选择更高清晰度的格式。

**问题**：sign参数是基于完整URL计算的，修改basedata会导致签名失效。

**解决思路**：
1. 研究sign的计算算法
2. 或者找到不验证sign的请求方式

### 方案2：从视频详情API获取所有格式URL

视频号详情API（`/web/api/feed/detail`）可能返回所有清晰度的URL，从中选择最高清晰度。

**需要**：
1. 捕获视频详情API的响应
2. 分析返回数据结构
3. 提取高清URL

### 方案3：参考RES Downloader的实现

RES Downloader可能已经处理了高质量URL的问题，研究其源码：
- 查看是否有格式选择逻辑
- 查看是否有高清URL构建方法

### 方案4：修改请求头

某些CDN通过请求头（如`Range`、`User-Agent`）来判断返回什么清晰度。

---

## 六、下一步研究计划

1. **捕获视频详情API响应**：启动MITM，点击视频播放，捕获`/web/api/feed/detail`请求
2. **分析RES Downloader源码**：查找格式选择和高清URL相关代码
3. **测试dotrans=1**：验证是否返回高清版本
4. **研究sign算法**：如果需要修改basedata，需要重新计算sign

---

## 七、参考资料

- [RES Downloader GitHub](https://github.com/putyy/res-downloader)
- [微信视频号下载器API参考](https://blog.csdn.net/gitblog_00104/article/details/151919958)
- [抓包实现视频号下载](https://blog.csdn.net/m0_68138958/article/details/132333774)

---

*本文档随研究进展持续更新。*
