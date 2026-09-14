# 公众号文章自动化采集 SOP

> 目标公众号：顶底之王（__biz=MzUxODM4ODM5Mg==）
> 最后验证：2026-09-12
> 采集结果：277篇文章（含多图文子文章）

## 1. 核心原理

微信Mac版公众号文章列表API（`profile_ext?action=getmsg`）**不走系统代理**，而是通过微信主进程的长连接（IPv6:8080端口）获取。因此无法直接用mitmproxy/res-downloader捕获文章列表API。

**突破方法**：公众号文章**详情页**（`mp.weixin.qq.com/s/xxx`）由内置浏览器（WeChatAppEx）渲染，其流量**走系统代理**。在详情页的jsmonitor请求中，可以捕获到调用文章列表API所需的全部参数（uin/key/pass_ticket/appmsg_token）。拿到这些参数后，直接用requests调用API即可。

## 2. 前置条件

| 项目 | 要求 |
|------|------|
| 微信版本 | 4.1.8（锁定，不升级） |
| mitmproxy | 已安装（`brew install mitmproxy`） |
| mitmproxy证书 | 已安装到系统钥匙串并信任 |
| 微信登录 | 已登录且已关注目标公众号 |

**本方案不依赖ClashX、不依赖res-downloader。** mitmproxy使用直连模式，微信和公众号API都是国内流量，不需要翻墙。

## 3. 采集步骤

### 3.1 启动mitmproxy捕获cookie

```bash
# 1. 启动mitmproxy（端口8084，header捕获脚本）
cat > /tmp/capture_headers.py << 'EOF'
import mitmproxy.http
import json, os, time
OUTPUT_DIR = "/tmp/wechat_headers"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def request(flow):
    host = flow.request.host
    if "weixin.qq.com" in host:
        ts = int(time.time() * 1000)
        data = {
            "timestamp": ts,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "headers": dict(flow.request.headers),
            "cookies": dict(flow.request.cookies),
        }
        safe_host = host.replace(".", "_")
        with open(f"{OUTPUT_DIR}/{safe_host}_{ts}.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if flow.request.cookies:
            print(f"[COOKIE] {flow.request.pretty_url[:80]}")
EOF

nohup mitmdump --listen-port 8084 -s /tmp/capture_headers.py > /tmp/mitmproxy.log 2>&1 &

# 2. 设置系统代理为mitmproxy
networksetup -setwebproxy Wi-Fi 127.0.0.1 8084
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8084
```

### 3.2 在微信中触发cookie

1. 打开目标公众号主页
2. 点击任意一篇文章进入**详情页**
3. **下拉刷新**详情页（关键！必须刷新才能触发带cookie的jsmonitor请求）
4. 等待3-5秒

### 3.3 提取参数

```bash
# 查看最新的带cookie请求
ls -lt /tmp/wechat_headers/mp_weixin_qq_com_*.json | head -3

# 提取参数（从最新的文件中）
python3 << 'EOF'
import json, glob, urllib.parse
files = sorted(glob.glob("/tmp/wechat_headers/mp_weixin_qq_com_*.json"), reverse=True)
for f in files:
    d = json.load(open(f))
    if d.get('cookies'):
        parsed = urllib.parse.urlparse(d['url'])
        params = urllib.parse.parse_qs(parsed.query)
        print("=== 关键参数 ===")
        print(f"__biz: {params.get('__biz', [''])[0]}")
        print(f"uin: {params.get('uin', [''])[0]}")
        print(f"key: {params.get('key', [''])[0][:60]}...")
        print(f"pass_ticket: {params.get('pass_ticket', [''])[0]}")
        print(f"appmsg_token: {params.get('appmsg_token', [''])[0][:60]}...")
        print(f"wxtoken: {params.get('wxtoken', [''])[0]}")
        print(f"\n=== Cookies ===")
        for k, v in d['cookies'].items():
            print(f"  {k}: {v[:60]}")
        break
EOF
```

### 3.4 调用文章列表API

```python
import requests, json, time, datetime

# 填入3.3提取的参数
PARAMS = {
    "__biz": "MzUxODM4ODM5Mg==",
    "uin": "MTcwNDE4MTE5MA==",
    "key": "从捕获文件中复制完整key",
    "pass_ticket": "从捕获文件中复制",
    "appmsg_token": "从捕获文件中复制",
}

COOKIES = {
    "wxuin": "1704181190",
    "devicetype": "UnifiedPCMac",
    "version": "f264186b",
    "lang": "zh_CN",
    "appmsg_token": PARAMS["appmsg_token"],
    "pass_ticket": PARAMS["pass_ticket"],
    "wxtokenkey": "777",
    "wap_sid2": "从捕获文件中复制",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzUxODM4ODM5Mg==&scene=124",
    "X-Requested-With": "XMLHttpRequest",
}

url = "https://mp.weixin.qq.com/mp/profile_ext"
all_articles = []
offset = 0

while True:
    query = {
        "action": "getmsg",
        "__biz": PARAMS["__biz"],
        "f": "json",
        "offset": str(offset),
        "count": "10",
        "is_ok": "1",
        "scene": "124",
        "uin": PARAMS["uin"],
        "key": PARAMS["key"],
        "pass_ticket": PARAMS["pass_ticket"],
        "wxtoken": "777",
        "appmsg_token": PARAMS["appmsg_token"],
        "x5": "0",
    }
    resp = requests.get(url, params=query, headers=HEADERS, cookies=COOKIES, timeout=30)
    data = resp.json()
    
    if data.get('ret') != 0:
        print(f"错误: {data}")
        break
    
    msg_list = json.loads(data['general_msg_list'])
    for item in msg_list.get('list', []):
        if 'app_msg_ext_info' in item:
            info = item['app_msg_ext_info']
            all_articles.append({
                "title": info.get('title', ''),
                "url": info.get('content_url', '').replace('&amp;', '&'),
                "date": datetime.datetime.fromtimestamp(
                    item['comm_msg_info']['datetime']
                ).strftime('%Y-%m-%d'),
                "digest": info.get('digest', ''),
            })
            # 多图文子文章
            for sub in info.get('multi_app_msg_item_list', []):
                all_articles.append({
                    "title": sub.get('title', ''),
                    "url": sub.get('content_url', '').replace('&amp;', '&'),
                    "date": datetime.datetime.fromtimestamp(
                        item['comm_msg_info']['datetime']
                    ).strftime('%Y-%m-%d'),
                    "digest": sub.get('digest', ''),
                    "is_sub": True,
                })
    
    if data.get('can_msg_continue') == 0:
        break
    offset = data['next_offset']
    time.sleep(1)

# 去重保存
seen = set()
unique = [a for a in all_articles if a['url'] and a['url'] not in seen and not seen.add(a['url'])]
with open("文章URL列表.json", "w", encoding='utf-8') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)
print(f"获取完成: {len(unique)}篇")
```

### 3.5 恢复环境

```bash
# 关闭系统代理（或恢复为你平时用的代理）
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off

# 停止mitmproxy
pkill mitmdump
```

## 4. 关键参数说明

| 参数 | 来源 | 时效性 | 说明 |
|------|------|--------|------|
| `__biz` | 公众号固定 | 永久 | 公众号唯一标识，Base64编码 |
| `uin` | cookie/URL | 长期 | 用户ID，Base64编码 |
| `key` | URL参数 | **数小时** | 调用API的密钥，会过期 |
| `pass_ticket` | cookie/URL | **数小时** | 通行证，会过期 |
| `appmsg_token` | cookie/URL | **数小时** | 应用消息token，会过期 |
| `wxtoken` | URL参数 | 长期 | 固定为777 |
| `wap_sid2` | cookie | 数天 | 会话ID |

**注意**：key/pass_ticket/appmsg_token有时效性（通常几小时），过期后需要重新捕获。

## 5. 常见问题

### Q1: mitmproxy捕获不到带cookie的请求？
- 确认系统代理已设置为mitmproxy 8084
- 确认ClashX已关闭"设置为系统代理"
- 必须进入文章**详情页**并**下拉刷新**，仅在列表页滚动不会触发cookie
- 确认mitmproxy证书已信任

### Q2: API返回ret!=0或errmsg?
- key/pass_ticket/appmsg_token已过期，重新执行3.1-3.3捕获新参数
- 请求频率过高，增加time.sleep延迟

### Q3: 其他代理软件（如ClashX）总是把系统代理改回去？
- 采集期间完全退出其他代理软件
- 或者在其他代理软件中关闭"设置为系统代理"

### Q4: 文章数和公众号主页显示不一致？
- 公众号主页显示的是"原创"文章数
- API返回的是所有文章（含转载、多图文子文章）
- 277篇包含了多图文的子文章（is_sub=true）

## 6. 增量更新（后续跟踪）

```python
# 只获取最新的N篇，offset从0开始，直到遇到已存在的文章
existing_urls = {a['url'] for a in json.load(open('文章URL列表.json'))}
new_articles = []

for article in all_articles:
    if article['url'] in existing_urls:
        break  # 遇到已存在的文章，停止
    new_articles.append(article)

print(f"新增文章: {len(new_articles)}篇")
```

## 7. 已验证死路（不要浪费时间）

| 方案 | 结果 | 原因 |
|------|------|------|
| 微信数据库读取 | ❌ | 公众号文章浏览后不缓存到本地数据库 |
| res-downloader抓包 | ❌ | 文章列表API不走系统代理；且不保存JSON响应 |
| 搜狗微信搜索 | ❌ | 只能找到24篇旧文章，很多已注销 |
| pfctl透明代理 | ❌ | macOS只重定向入站流量，不重定向出站 |
| Proxifier | ❌ | 付费软件 |
| ClashX TUN+mitmproxy | ❌ | 导致ClashX端口冲突，翻墙中断 |
| tcpdump/Wireshark | ❌ | 微信保持长连接无新TLS握手，无法解密 |

## 8. 文章正文获取（UA伪装法，已验证）

### 8.1 核心原理

微信公众号文章的反爬策略主要检查User-Agent中是否包含`MicroMessenger`关键字。只要UA声明自己是微信客户端，服务器就放行，**不需要Cookie、不需要登录、不需要代理**。

### 8.2 关键UA（微信内置浏览器标识）

```
Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x16082222) NetType/WIFI Language/zh_CN
```

### 8.3 采集脚本

脚本位置：`scripts/fetch_articles.py`

```bash
# 运行批量采集
python3 scripts/fetch_articles.py
```

**功能特性**：
- 断点续传：采集进度保存在`采集进度.json`，中断后可继续
- 自动重试：每篇最多重试3次
- 随机延迟：2-4秒间隔，避免触发风控
- 完整保存：标题、正文（纯文本+HTML）、图片URL、发布时间、公众号名称
- 输出格式：每篇文章一个JSON文件

### 8.4 输出目录结构

```
knowledge-base/02-公众号文章/
├── 文章URL列表.json          # 277篇文章URL
├── 采集进度.json             # 断点续传进度
└── 正文/
    ├── 001_文章标题.json
    ├── 002_文章标题.json
    └── ...
```

### 8.5 注意事项

1. **请求频率**：2-4秒间隔，不要太快，避免IP被限制
2. **图片处理**：文章中的图片URL已提取，后续可下载并OCR解析
3. **去重**：按URL去重，已完成的不会重复采集
4. **时效性**：UA伪装法目前有效，微信可能随时升级反爬策略

---

*文档创建：2026-09-12*
*最后更新：2026-09-14（新增UA伪装法，已验证277篇文章可稳定采集）*
*采集方案验证：mitmproxy捕获cookie + profile_ext API直接调用 + UA伪装法获取正文*
