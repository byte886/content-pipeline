"""
方法提炼（Method Extraction）

分析博主的视频表现效果和风格，提炼出可复用的生成方法。
适用于：学习优秀博主的拍摄技巧、AI使用、内容呈现，方便生成类似风格的视频。

这不是传统行业知识库，而是"创意方法库"——提炼的是"怎么做"，不是"讲了什么"。

用户需求场景：
- 看到一个抖音博主（专门做广告的），拍摄技巧、AI使用效果、内容呈现都很新颖
- 除了采集视频和图文，还需要分析视频的表现效果和风格
- 提炼出生成这个视频的方法
- 这个过程可能还会搜索（如搜索某种AI工具的使用方法）
- 目的不是进入这个行业，只是为了提炼方法，方便抄袭风格和生成视频
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class MethodNote:
    """
    方法笔记（MethodNote）

    从博主视频中提炼的可复用生成方法。
    与VideoNote（内容笔记）的区别：VideoNote记录"讲了什么"，MethodNote记录"怎么做的"。
    """
    method_id: str                    # 方法唯一ID（如 method_001）
    title: str                        # 方法名称（如"AI数字人口播视频生成法"）
    source_video_id: str              # 来源视频ID
    source_platform: str              # 来源平台
    source_author: str                # 来源作者

    # 方法维度
    shooting_techniques: List[str] = field(default_factory=list)   # 拍摄技巧
    ai_tools: List[Dict] = field(default_factory=list)             # AI工具使用（工具名、用途、效果）
    content_structure: List[str] = field(default_factory=list)     # 内容呈现结构（钩子→主体→结尾）
    visual_style: Dict = field(default_factory=dict)               # 视觉风格（配色、字体、转场）
    audio_style: Dict = field(default_factory=dict)                # 音频风格（BGM、配音、音效）
    pacing: Dict = field(default_factory=dict)                     # 节奏控制（时长分配、卡点）

    # 生成方法
    step_by_step: List[str] = field(default_factory=list)          # 分步生成方法
    tools_needed: List[str] = field(default_factory=list)          # 需要的工具
    estimated_time: str = ""                                       # 预计制作时间
    difficulty: str = "medium"                                     # 难度（easy/medium/hard）

    # 元数据
    tags: List[str] = field(default_factory=list)
    description: str = ""
    created_at: str = ""
    status: str = "draft"                                          # draft/stable


class MethodExtractor:
    """方法提炼器"""

    def __init__(self, output_dir: str = "library/05_knowledge/concepts/methods"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def extract_from_transcript(self, transcript_path: str, video_metadata: dict) -> MethodNote:
        """
        从视频转写稿中提炼方法。

        分析维度：
        1. 拍摄技巧：博主提到的拍摄方法、设备、构图
        2. AI使用：博主使用的AI工具、提示词、效果
        3. 内容呈现：视频结构、钩子设计、节奏控制
        4. 视觉风格：画面风格、配色、字体
        5. 生成方法：综合以上，提炼出可复用的分步方法

        注意：此过程可能需要搜索（如搜索某种AI工具的使用方法），
        搜索结果应作为补充信息纳入方法笔记。
        """
        # 读取转写稿
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()

        # TODO: 实际的方法提炼逻辑（需要LLM分析）
        # 框架先搭好，后续接入LLM深度分析

        method = MethodNote(
            method_id=f"method_{video_metadata.get('item_id', 'unknown')}",
            title=f"待提炼: {video_metadata.get('title', '未知')}",
            source_video_id=video_metadata.get('item_id', ''),
            source_platform=video_metadata.get('platform', ''),
            source_author=video_metadata.get('author', ''),
            description=f"从视频 '{video_metadata.get('title', '')}' 中提炼的生成方法",
            created_at=__import__('datetime').datetime.now().isoformat()
        )

        return method

    def save(self, method: MethodNote):
        """保存方法笔记"""
        path = os.path.join(self.output_dir, f"{method.method_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(method.__dict__, f, ensure_ascii=False, indent=2)
        return path

    def load(self, method_id: str) -> Optional[MethodNote]:
        """加载方法笔记"""
        path = os.path.join(self.output_dir, f"{method_id}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return MethodNote(**data)
        return None

    def list_methods(self, tags: List[str] = None) -> List[MethodNote]:
        """列出所有方法笔记，可按标签筛选"""
        methods = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.output_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                method = MethodNote(**data)
                if tags is None or any(t in method.tags for t in tags):
                    methods.append(method)
        return methods


# 使用示例
if __name__ == "__main__":
    extractor = MethodExtractor()

    # 示例：从转写稿提炼方法
    # method = extractor.extract_from_transcript(
    #     "library/04_transcript/douyin/xxx/transcript.md",
    #     {"item_id": "xxx", "title": "AI数字人视频", "platform": "douyin", "author": "某博主"}
    # )
    # extractor.save(method)

    # 列出所有方法
    methods = extractor.list_methods()
    print(f"共有 {len(methods)} 个方法笔记")
