# 视频号API研究记录

> **文档类型**：技术研究
> **创建时间**：2026-09-15
> **状态**：研究中
> **目标**：找到可直接调用的视频号列表API，替代滚动页面采集

---

## 一、已发现的API端点

### 1.1 Web API（channels.weixin.qq.com）

| 端点 | 功能 | 来源 |
|------|------|------|
| `/web/api/feed/detail` | 获取视频详情 | CSDN博客（抓包分析） |
| `/web/api/feed/list` | 可能的视频列表 | 推测，待验证 |
| `/web/api/profile/feed` | 可能的主页视频列表 | 推测，待验证 |
| `/web/api/profile/info` | 可能的账号信息 | 推测，待验证 |

### 1.2 微信开放平台API（api.weixin.qq.com）

| 端点 | 功能 | 说明 |
|------|------|------|
| `/channels/ec/finderlive/getfinderliverecordlist` | 获取直播记录 | 官方API，需视频号助手权限 |
| `/channels/ec/promoter/get_feed_list` | 获取推广视频列表 | 电商带货相关 |

### 1.3 第三方API服务（付费）

| 服务 | 端点 | 价格 |
|------|------|------|
| TikHub.io | `/api/v2/wechat-channels/fetch_user_video_list` | 付费 |
| OneAPI | `/api/wechat-channels-v2/fetch_user_video_list` | 0.15元/次 |
| Apify | socialdatax-wechat-data-api | 付费 |

---

## 二、技术分析

### 2.1 视频号页面结构

视频号主页URL格式：
```
https://channels.weixin.qq.com/web/pages/profile?username=v2_xxx@finder
```

页面包含两个标签：
- **视频**：短视频列表
- **直播回放**：直播回放列表

### 2.2 可能的鉴权方式

视频号Web API很可能需要：
1. **Cookie**：微信登录态（`wxuin`、`wxsid`、`wxsticket`等）
2. **请求头签名**：可能有`x-sign`或类似签名头
3. **Token**：页面加载时生成的临时token

### 2.3 视频URL格式

```
https://finder.video.qq.com/251/20302/stodownload?encfilekey=<...>&token=<...>
```

- `encfilekey`：加密文件密钥
- `token`：访问令牌（有时效性）
- `DecodeKey`：视频解密密钥（9-10位数字，在视频详情数据中）

---

## 三、研究计划

### 阶段1：捕获API请求（当前）
- [ ] 启动MITM代理，访问视频号主页
- [ ] 记录所有`/web/api/`请求
- [ ] 分析返回数据结构
- [ ] 识别列表API和详情API

### 阶段2：分析鉴权机制
- [ ] 提取请求头和Cookie
- [ ] 分析签名算法（如有）
- [ ] 测试Cookie时效性

### 阶段3：直接调用API
- [ ] 用提取的Cookie直接调用列表API
- [ ] 测试分页参数
- [ ] 验证返回数据完整性

### 阶段4：集成到采集工具
- [ ] 如果API可行，替代滚动采集方案
- [ ] 实现纯API采集脚本
- [ ] 更新SOP文档

---

## 四、已知限制

1. **微信登录态**：API需要微信登录态，Cookie可能有时效性
2. **风控限制**：频繁调用可能触发微信风控
3. **接口变更**：微信可能随时变更API接口
4. **法律风险**：批量采集需注意微信服务条款

---

## 五、参考资料

- [微信视频号下载器API完全参考手册](https://blog.csdn.net/gitblog_00104/article/details/151919958)
- [抓包ck实现微信视频号视频下载](https://blog.csdn.net/m0_68138958/article/details/132333774)
- [微信开放社区 - 视频号API](https://developers.weixin.qq.com/doc/channels/api/)
- [RES Downloader GitHub](https://github.com/putyy/res-downloader)

---

*本文档随研究进展持续更新。*
