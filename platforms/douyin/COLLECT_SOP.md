# 抖音博主全量采集SOP

> **适用场景**：某个抖音博主的全量视频列表收集、分类预判、批量下载、增量更新
> **已验证**：2026-10-08 郭颖珠宝库，387个视频列表收集，6个测试视频下载成功

---

## 前置条件
1. Chrome已登录抖音网页版
2. 能正常打开博主主页
3. 已安装 `mac_computer_use_tool`（浏览器自动化）

---

## 第一步：收集全量视频列表（387个视频的方法）

### 关键坑
抖音网页版是**虚拟滚动**，滚动容器不是window，是 `.route-scroll-container`，滚window不会加载新视频！

### 操作步骤
```python
import seed_browser_use as bu

# 1. 打开博主主页
bu.navigate("https://www.douyin.com/user/[sec_uid]")
bu.wait_for_load()

# 2. 慢慢滚动虚拟容器（模拟人类节奏）
container = bu.js("document.querySelector('.route-scroll-container')")
last_count = 0
same_count_times = 0

while same_count_times < 3:
    # 滚到底
    bu.js("""
        const c = document.querySelector('.route-scroll-container');
        c.scrollTop = c.scrollHeight;
    """)
    bu.wait(2)  # 等2秒加载
    # 数现在有多少个视频卡片
    current = bu.js("document.querySelectorAll('ul li div a[href*=\"/video/\"]').length")
    if current == last_count:
        same_count_times += 1
    else:
        same_count_times = 0
        last_count = current
```

### 提取所有视频标题+链接
```python
videos = bu.js("""
    const items = document.querySelectorAll('ul li');
    return Array.from(items).map(li => {
        const a = li.querySelector('a[href*="/video/"]');
        const title = li.querySelector('p')?.innerText || '';
        return {
            url: a ? a.href : '',
            title: title
        }
    }).filter(v => v.url);
""")
```

---

## 第二步：分类预判+生成状态清单Excel

### 自动分类规则
按标题关键词自动分：
| 分类 | 关键词 | 价值等级 |
|---|---|---|
| 高价值科普 | 什么是、区别、鉴别、A货、种水、帝王绿 | 高 |
| 潘家园实战 | 潘家园、带粉丝、挑战、捡漏 | 中 |
| 普通展示 | 品鉴、给大家看一个 | 低 |
| 水视频 | 节日、祝福、新年快乐 | 不下载 |
| 广告活动 | 寻宝、征集、直播 | 不下载 |

### 生成Excel清单
脚本：`platforms/douyin/scripts/generate_video_list.py`
- 列：序号、标题、URL、品类、价值等级、是否下载、是否转写、本地路径、备注
- 作为增量更新的基准，后续只处理"未下载"的

---

## 第三步：批量下载（防风控）

### 关键坑
**yt-dlp直连抖音返回403 Fresh cookies错误**，加`--cookies-from-browser chrome`也没用，抖音API层已经风控了。

### 已验证的可用方案：浏览器直读video流
1. 逐个打开视频页
2. 从`<video>`标签的`currentSrc`拿到视频流地址
3. 直接用`bu.download()`下载mp4

### 防风控节奏（必须遵守）
- 每下载5个视频，歇30秒
- 不要连续高速请求
- 单批最多下10个，下完歇2分钟再继续
- 按人类节奏，不要一夜之间下完387个

### 下载代码示例
```python
for video in videos_to_download:
    bu.navigate(video['url'])
    bu.wait(1)
    # 等video标签加载
    bu.wait_for_element('video', visible=True, timeout=10)
    # 拿视频流地址
    video_src = bu.js("document.querySelector('video').currentSrc")
    # 下载
    record = bu.download(video_src, filename=f"{video['title']}.mp4")
    # 更新Excel状态
    update_excel(video['url'], '已下载', record['path'])
    # 歇一下
    import time; time.sleep(3)
```

---

## 第四步：增量更新
1. 重新跑第一步收集全量列表
2. 和Excel里的历史URL对比，找出新增的
3. 新增的走第二步→第三步流程
4. 更新Excel状态

---

## 常见问题
| 问题 | 解决方案 |
|---|---|
| 滚动半天不加载新视频 | 滚的是虚拟容器`.route-scroll-container`，不是window |
| yt-dlp报403 Fresh cookies | 不要用yt-dlp，走浏览器直读方案 |
| 打开视频页没有video标签 | 等2秒，抖音有时要多加载一下 |
| 下载下来的视频只有几秒 | 没等video加载完就拿src了，要等video出现再拿 |
| 突然弹验证码 | 停下来歇10分钟，不要继续批量下 |
