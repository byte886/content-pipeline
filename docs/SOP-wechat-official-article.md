# 公众号文章自动化采集 SOP

> **文档类型**：SOP（标准操作流程）
> **更新时间**：2026-09-18
> **维护者**：AI自动维护 + 用户审核
> **目标公众号**：顶底之王（__biz=MzUxODM4ODM5Mg==）
> **最后验证**：2026-09-17
> **采集结果**：278篇文章（含多图文子文章）
> **前置依赖**：[SOP-wechat-basic-operations.md](SOP-wechat-basic-operations.md)（微信基本操作、UI自动化、鼠标控制）

## 1. 核心方案（按优先级）

### 方案A：wx biz-articles 本地数据库读取（首选，增量采集）

**原理**：微信本地数据库缓存了最近推送的公众号文章。用 `wx-cli` 工具直接解密读取，无需代理、无需登录态、无需UI自动化。

**适用场景**：增量采集（发现新文章）、日常跟踪。

**限制**：只能获取本地缓存的最近推送文章（通常每公众号1-5篇），无法获取全部历史文章。

### 方案B：video-capture MITM代理（全量采集，**当前不可用**）

**原理**：用项目中的 `video-capture` 工具（Go写的MITM代理）解密HTTPS流量，从文章详情页的jsmonitor请求中提取API参数（uin/key/pass_ticket/appmsg_token），再调用文章列表API。

**适用场景**：全量采集（首次采集、补全历史文章）。

**⚠️ 当前状态（2026-09-17验证）**：
- uin/key/pass_ticket可以捕获到
- **appmsg_token始终为空**：微信4.x中appmsg_token通过微信内部API（xweb.worker）生成，不走HTTP，代理捕获不到
- 用appmsg_token为空的参数调用API返回`msg_count=0`
- 早期（2026-09-12）能捕获到，可能是微信服务端后来更新了
- **首次全量采集新公众号的方案待研究**

**顶底之王已有278篇文章URL在manifest中**，不需要全量采集，直接用方案C下载正文即可。

### 方案C：UA伪装法获取正文（通用）

**原理**：微信公众号文章的反爬策略主要检查User-Agent中是否包含`MicroMessenger`关键字。只要UA声明自己是微信客户端，服务器就放行，不需要Cookie、不需要登录、不需要代理。

**适用场景**：获取单篇文章正文（方案A/B获取到URL后，用此方法下载正文）。

---

## 2. 方案A：wx biz-articles 增量采集（推荐）

### 2.1 前置条件

| 项目 | 要求 |
|------|------|
| 微信版本 | 4.1.8（锁定，不升级） |
| wx-cli | 已安装：`/usr/local/bin/wx`（wechat-control技能提供） |
| 微信密钥 | 已提取（wechat-control技能首次配置时完成） |
| 微信登录 | 已登录且已关注目标公众号 |

### 2.2 采集步骤

```bash
# 查询指定公众号的最新文章（本地缓存）
wx biz-articles --account "顶底之王" --limit 500 --json

# 查询所有公众号的最新文章
wx biz-articles --limit 1000 --json
```

**输出字段**：
- `account`：公众号名称
- `title`：文章标题
- `url`：文章URL（含完整参数mid/sn/chksm）
- `time`：发布时间
- `digest`：摘要
- `cover_url`：封面图

### 2.3 增量对比脚本

```python
import json, subprocess

# 获取最新文章
result = subprocess.run(
    ['wx', 'biz-articles', '--account', '顶底之王', '--limit', '500', '--json'],
    capture_output=True, text=True
)
latest = json.loads(result.stdout)

# 读取现有manifest
with open('library/06_articles/stock/顶底之王/manifest.json') as f:
    existing = json.load(f)

# 对比（去掉chksm参数比较，因为每次可能不同）
existing_urls = {a['url'].split('&chksm=')[0] for a in existing}
new_articles = [a for a in latest if a['url'].split('&chksm=')[0] not in existing_urls]

print(f"现有: {len(existing)}篇, 新增: {len(new_articles)}篇")
for a in new_articles:
    print(f"  [{a['time']}] {a['title']}")
```

### 2.4 下载新文章正文

获取到URL后，用方案C（UA伪装法）下载正文。详见第4节。

---

## 3. 方案B：video-capture 全量采集（备选）

### 3.1 前置条件

| 项目 | 要求 |
|------|------|
| video-capture | 已编译：`platforms/wechat_channels/video-capture/video-capture` |
| CA证书 | `platforms/wechat_channels/video-capture/ca.crt` 已在系统钥匙串信任 |
| ClashX | 运行中，监听7890（作为上游代理，可不用但建议开） |

### 3.2 采集步骤

#### 步骤1：启动video-capture

```bash
cd platforms/wechat_channels/video-capture
nohup ./video-capture -port 8899 -output /tmp/capture.json -upstream "http://127.0.0.1:7890" > /tmp/video_capture.log 2>&1 &
echo $! > /tmp/video_capture_pid.txt
```

#### 步骤2：在微信中触发参数捕获

1. 打开目标公众号**主页**，停留几秒（设置Cookie）
2. 点击任意一篇文章进入**详情页**
3. **下拉刷新**详情页（触发jsmonitor请求）
4. 等待3-5秒

#### 步骤3：提取参数

```python
import re, urllib.parse, json

with open('/tmp/video_capture.log', 'r') as f:
    log = f.read()

# 找包含uin/key/pass_ticket的POST请求
matches = re.findall(r'Sending request POST (https://mp\.weixin\.qq\.com/mp/jsmonitor\?[^\n]+)', log)
uin_matches = [m for m in matches if 'uin=' in m and 'key=' in m]

if uin_matches:
    url = uin_matches[-1]  # 最新的
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    
    def multi_decode(s, times=3):
        for _ in range(times):
            try: s = urllib.parse.unquote(s)
            except: break
        return s
    
    result = {
        '__biz': multi_decode(params.get('__biz', [''])[0]),
        'uin': multi_decode(params.get('uin', [''])[0]),
        'key': multi_decode(params.get('key', [''])[0]),
        'pass_ticket': multi_decode(params.get('pass_ticket', [''])[0]),
        'appmsg_token': multi_decode(params.get('appmsg_token', [''])[0]),
    }
    
    with open('/tmp/wechat_api_params.json', 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
```

**注意**：
- 如果appmsg_token为空，尝试从公众号主页HTML中提取：先用参数调用 `profile_ext?action=home`，从返回HTML中用正则 `appmsg_token\s*=\s*["']([^"']+)["']` 提取。
- 必须确认`__biz`是目标公众号的（顶底之王是`MzUxODM4ODM5Mg==`）。

#### 步骤4：调用文章列表API

```python
import requests, json, time, datetime, base64

with open('/tmp/wechat_api_params.json') as f:
    p = json.load(f)

url = "https://mp.weixin.qq.com/mp/profile_ext"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 MicroMessenger/8.0.34",
    "Referer": f"https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={p['__biz']}&scene=124",
    "X-Requested-With": "XMLHttpRequest",
}
cookies = {
    "wxuin": str(int.from_bytes(base64.b64decode(p['uin']), 'big')),
    "devicetype": "UnifiedPCMac",
    "version": "f264186b",
    "lang": "zh_CN",
    "pass_ticket": p['pass_ticket'],
    "wxtokenkey": "777",
}
if p.get('appmsg_token'):
    cookies['appmsg_token'] = p['appmsg_token']

all_articles = []
offset = 0
while True:
    query = {
        "action": "getmsg", "__biz": p['__biz'], "f": "json",
        "offset": str(offset), "count": "10", "is_ok": "1", "scene": "124",
        "uin": p['uin'], "key": p['key'], "pass_ticket": p['pass_ticket'],
        "wxtoken": "777", "x5": "0",
    }
    if p.get('appmsg_token'):
        query['appmsg_token'] = p['appmsg_token']
    
    resp = requests.get(url, params=query, headers=headers, cookies=cookies, timeout=30)
    data = resp.json()
    
    if data.get('ret') != 0:
        print(f"API错误: {data}")
        break
    
    msg_list = json.loads(data.get('general_msg_list', '{"list":[]}'))
    for item in msg_list.get('list', []):
        if 'app_msg_ext_info' in item:
            info = item['app_msg_ext_info']
            dt = datetime.datetime.fromtimestamp(item['comm_msg_info']['datetime'])
            all_articles.append({"title": info.get('title',''), "url": info.get('content_url','').replace('&amp;','&'), "date": dt.strftime('%Y-%m-%d')})
            for sub in info.get('multi_app_msg_item_list', []):
                all_articles.append({"title": sub.get('title',''), "url": sub.get('content_url','').replace('&amp;','&'), "date": dt.strftime('%Y-%m-%d')})
    
    if data.get('can_msg_continue') == 0:
        break
    offset = data['next_offset']
    time.sleep(1)

# 去重
seen = set()
unique = [a for a in all_articles if a['url'] and a['url'] not in seen and not seen.add(a['url'])]
print(f"获取完成: {len(unique)}篇")
```

#### 步骤5：停止捕获

```bash
kill $(cat /tmp/video_capture_pid.txt)
# video-capture停止时会自动恢复系统代理
```

---

## 4. 方案C：UA伪装法获取文章正文（通用）

### 4.1 核心原理

微信公众号文章的反爬策略主要检查User-Agent中是否包含`MicroMessenger`关键字。只要UA声明自己是微信客户端，服务器就放行，**不需要Cookie、不需要登录、不需要代理**。

### 4.2 关键UA

```
Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x16082222) NetType/WIFI Language/zh_CN
```

### 4.3 采集脚本

```bash
# 单篇文章下载
curl -L -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 MicroMessenger/8.0.34" -o article.html "文章URL"
```

**解析要点**：
- 标题：`<h1 class="rich_media_title">` 或 `#activity-name`
- 正文：`<div id="js_content">`
- 图片：`data-src` 属性（不是`src`）
- 发布时间：`var ct = "时间戳"`

---

## 5. 关键参数说明

| 参数 | 来源 | 时效性 | 说明 |
|------|------|--------|------|
| `__biz` | 公众号固定 | 永久 | 公众号唯一标识，Base64编码 |
| `uin` | URL参数 | 长期 | 用户ID，Base64编码 |
| `key` | URL参数 | **数小时** | 调用API的密钥，会过期 |
| `pass_ticket` | URL参数 | **数小时** | 通行证，会过期 |
| `appmsg_token` | URL参数/cookie | **数小时** | 应用消息token，可能为空 |
| `wxtoken` | 固定 | 长期 | 固定为777 |

---

## 6. 常见问题

### Q1: wx biz-articles 只能获取到最近几篇文章？
- 是的，微信本地数据库只缓存最近推送的文章（通常每公众号1-5篇）
- 全量采集需要用方案B（video-capture）或人工滚动页面采集
- 增量采集用方案A足够

### Q2: video-capture捕获不到公众号流量？
- 确认系统代理已设置为127.0.0.1:8899
- 确认CA证书已在系统钥匙串信任
- 必须进入文章**详情页**并**下拉刷新**
- 微信4.x主进程不走代理，但WeChatAppEx内置浏览器走代理

### Q3: API返回ret!=0或文章数为0？
- key/pass_ticket已过期，重新捕获参数
- **appmsg_token为空**：微信4.x中appmsg_token通过内部API生成，代理捕获不到，此方案当前不可用
- 确认`__biz`是目标公众号的
- 顶底之王已有278篇URL在manifest中，不需要调用此API

### Q4: ClashX和video-capture冲突？
- 不冲突。video-capture是系统代理，ClashX是video-capture的上游代理
- 流量路径：微信 → video-capture(8899) → ClashX(7890) → 目标服务器

### Q5: 文章数和公众号主页显示不一致？
- 公众号主页显示的是"原创"文章数
- API返回的是所有文章（含转载、多图文子文章）

---

## 7. 已验证死路（不要浪费时间）

| 方案 | 结果 | 原因 |
|------|------|------|
| mitmproxy系统代理 | ❌ | 微信4.x主进程不走系统代理，配置复杂 |
| 微信数据库读取文章列表 | ❌ | 公众号文章浏览后不缓存完整列表到本地数据库（但`wx biz-articles`可读取最近推送） |
| res-downloader抓文章列表 | ❌ | 文章列表API不走系统代理；且不保存JSON响应 |
| 搜狗微信搜索 | ❌ | 只能找到24篇旧文章 |
| pfctl透明代理 | ❌ | macOS只重定向入站流量，不重定向出站 |
| tcpdump/Wireshark | ❌ | 微信保持长连接无新TLS握手，无法解密 |
| **appmsg_token通过代理捕获** | ❌ | **微信4.x中appmsg_token通过xweb.worker内部API生成，不走HTTP，代理捕获不到，始终为空** |
| 用pass_ticket代替appmsg_token | ❌ | API返回msg_count=0 |
| getappmsgext API获取appmsg_token | ❌ | 返回ret=-11 |

---

*文档创建：2026-09-12*
*最后更新：2026-09-17（验证appmsg_token无法通过代理捕获，方案B当前不可用；顶底之王已有278篇URL在manifest中）*
*推荐流程：日常增量用方案A（wx biz-articles），正文下载统一用方案C（UA伪装）；全量采集新公众号的方案待研究*
