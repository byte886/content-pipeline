"""
增量水位机制（Watermark）

持久化"上次成功处理到的位置"，下次只取其后的新内容。
先成功落地、再推进水位（at-least-once，崩溃不丢，重复可去重）。

设计参考：珠宝项目的00_manifest/sources.json水位机制
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional


class WatermarkManager:
    """水位管理器"""

    def __init__(self, manifest_dir: str = "library/00_manifest"):
        self.manifest_dir = manifest_dir
        self.watermark_file = os.path.join(manifest_dir, "watermarks.json")
        self.watermarks: Dict = {}
        self._load()

    def _load(self):
        """加载水位文件"""
        if os.path.exists(self.watermark_file):
            with open(self.watermark_file, 'r', encoding='utf-8') as f:
                self.watermarks = json.load(f)

    def _save(self):
        """保存水位文件"""
        os.makedirs(self.manifest_dir, exist_ok=True)
        with open(self.watermark_file, 'w', encoding='utf-8') as f:
            json.dump(self.watermarks, f, ensure_ascii=False, indent=2)

    def get(self, platform: str, account: str, content_type: str = "videos") -> Optional[dict]:
        """
        获取指定源的水位。

        Returns:
            水位字典，如 {"last_max_created": 1789000000, "known_count": 743, "last_check_at": "..."}
            不存在则返回None
        """
        key = f"{platform}:{account}"
        source = self.watermarks.get(key, {})
        return source.get(content_type)

    def update(self, platform: str, account: str, content_type: str,
               last_max_created: int, known_count: int):
        """
        更新水位（先成功落地、再推进水位）。

        Args:
            platform: 平台标识
            account: 账号标识
            content_type: 内容类型（videos / articles）
            last_max_created: 最新内容的创建时间（unix时间戳）
            known_count: 已知内容总数
        """
        key = f"{platform}:{account}"
        if key not in self.watermarks:
            self.watermarks[key] = {
                "kind": platform,
                "account": account
            }
        self.watermarks[key][content_type] = {
            "last_max_created": last_max_created,
            "known_count": known_count,
            "last_check_at": datetime.now().isoformat()
        }
        self._save()

    def get_all_sources(self) -> Dict:
        """获取所有源的水位状态"""
        return self.watermarks

    def reset(self, platform: str, account: str, content_type: str = None):
        """
        重置水位（全量重新采集时使用）。

        Args:
            content_type: 指定类型，None则重置该源所有类型
        """
        key = f"{platform}:{account}"
        if key in self.watermarks:
            if content_type:
                self.watermarks[key].pop(content_type, None)
            else:
                del self.watermarks[key]
            self._save()


# 使用示例
if __name__ == "__main__":
    wm = WatermarkManager()

    # 更新水位
    wm.update("bilibili", "1841256325", "videos",
              last_max_created=1789000000, known_count=743)

    # 获取水位
    watermark = wm.get("bilibili", "1841256325", "videos")
    print(f"水位: {watermark}")

    # 查看所有源
    print(f"所有源: {wm.get_all_sources()}")
