"""
生成抖音视频状态追踪Excel清单

用法：
from generate_excel import generate_tracking_excel
videos = [{'title': 'xxx', 'url': 'xxx'}, ...]
generate_tracking_excel(videos, "郭颖珠宝视频知识库_总清单.xlsx")

列：序号、标题、URL、品类、价值等级、是否下载、是否转写、本地路径、备注
"""

import pandas as pd
from collect_video_list import classify_video

def generate_tracking_excel(videos, output_path):
    """
    生成状态追踪Excel，作为增量更新基准
    """
    rows = []
    for i, v in enumerate(videos, 1):
        category, value = classify_video(v['title'])
        rows.append({
            '序号': i,
            '标题': v['title'],
            'URL': v['url'],
            '品类': category,
            '价值等级': value,
            '是否下载': '否',
            '是否转写': '否',
            '本地路径': '',
            '备注': ''
        })
    
    df = pd.DataFrame(rows)
    
    # 按价值等级排序：高>中>低>不下载
    value_order = {'高': 0, '中': 1, '低': 2, '不下载': 3}
    df['_sort'] = df['价值等级'].map(value_order)
    df = df.sort_values(['_sort', '序号']).drop('_sort', axis=1)
    
    df.to_excel(output_path, index=False)
    print(f"已生成 {output_path}，共 {len(df)} 个视频")
    print(f"高价值：{len(df[df['价值等级']=='高'])} 个")
    print(f"中价值：{len(df[df['价值等级']=='中'])} 个")
    print(f"低价值：{len(df[df['价值等级']=='低'])} 个")
    print(f"不下载：{len(df[df['价值等级']=='不下载'])} 个")


def update_download_status(excel_path, video_url, local_path):
    """
    下载完一个视频后更新Excel状态
    """
    df = pd.read_excel(excel_path)
    mask = df['URL'] == video_url
    df.loc[mask, '是否下载'] = '是'
    df.loc[mask, '本地路径'] = local_path
    df.to_excel(excel_path, index=False)
