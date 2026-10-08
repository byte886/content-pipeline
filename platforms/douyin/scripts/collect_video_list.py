"""
抖音博主全量视频列表收集脚本（浏览器自动化版）

用法：
在 mac_computer_use_tool (plane=bu) 里运行：
    import sys; sys.path.insert(0, 'platforms/douyin/scripts')
    from collect_video_list import collect_all_videos
    videos = collect_all_videos("https://www.douyin.com/user/[sec_uid]")

返回：[{'title': 'xxx', 'url': 'xxx/douyin.com/video/xxx'}, ...]
"""

import time

def collect_all_videos(homepage_url, max_wait=60):
    """
    滚动虚拟容器直到加载完全部视频，提取标题+链接
    关键：抖音是虚拟滚动，滚 .route-scroll-container 不是 window
    """
    import seed_browser_use as bu
    
    bu.navigate(homepage_url)
    bu.wait_for_load()
    time.sleep(2)
    
    last_count = 0
    same_times = 0
    max_same = 3  # 连续3次数量不变就认为到底了
    
    while same_times < max_same:
        # 滚虚拟容器到底
        bu.js("""
            const c = document.querySelector('.route-scroll-container');
            if (c) c.scrollTop = c.scrollHeight;
        """)
        time.sleep(2)  # 模拟人类节奏，等加载
        
        # 数现在有多少视频
        current = bu.js("""
            return document.querySelectorAll('a[href*=\"/video/\"]').length;
        """)
        
        if current == last_count:
            same_times += 1
        else:
            same_times = 0
            last_count = current
    
    # 提取所有视频标题+链接
    videos = bu.js("""
        const items = document.querySelectorAll('ul li');
        return Array.from(items).map(li => {
            const a = li.querySelector('a[href*="/video/"]');
            const p = li.querySelector('p');
            return {
                url: a ? a.href : '',
                title: p ? p.innerText : ''
            }
        }).filter(v => v.url && v.title);
    """)
    
    # 去重
    seen = set()
    unique = []
    for v in videos:
        if v['url'] not in seen:
            seen.add(v['url'])
            unique.append(v)
    
    print(f"收集到 {len(unique)} 个去重视频")
    return unique


def classify_video(title):
    """
    按标题自动分类（珠宝行业版）
    返回：(品类, 价值等级)
    """
    title = title.lower()
    
    # 品类判断
    category = "其他"
    if any(k in title for k in ["翡翠", "帝王绿", "冰种", "糯种", "墨翠", "a货"]):
        category = "翡翠"
    elif any(k in title for k in ["南红", "保山", "凉山"]):
        category = "南红"
    elif any(k in title for k in ["和田玉", "籽料", "白玉", "碧玉", "墨玉"]):
        category = "和田玉"
    elif any(k in title for k in ["蜜蜡", "琥珀", "珍珠"]):
        category = "有机宝石"
    elif any(k in title for k in ["潘家园", "带粉丝", "挑战", "捡漏"]):
        category = "潘家园实战"
    elif any(k in title for k in ["节日", "祝福", "新年", "中秋"]):
        category = "水视频"
    elif any(k in title for k in ["寻宝", "征集", "直播", "抽奖"]):
        category = "广告活动"
    
    # 价值等级判断
    value = "低"
    if any(k in title for k in ["什么是", "区别", "鉴别", "a货", "种水"]):
        value = "高"
    elif category == "潘家园实战":
        value = "中"
    elif category in ["水视频", "广告活动"]:
        value = "不下载"
    
    return category, value
