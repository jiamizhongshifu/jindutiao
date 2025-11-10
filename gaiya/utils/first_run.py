"""首次运行检测器"""

import json
from pathlib import Path


class FirstRunDetector:
    """首次运行检测器

    使用 first_run.json 文件标记应用是否是首次运行。
    用于决定是否显示新手引导对话框。
    """

    def __init__(self, app_dir=None):
        """初始化检测器

        Args:
            app_dir: 应用数据目录，如果不提供则使用默认路径
        """
        if app_dir is None:
            from . import path_utils
            app_dir = path_utils.get_app_dir()

        self.app_dir = Path(app_dir)
        self.flag_file = self.app_dir / 'first_run.json'

    def is_first_run(self):
        """检查是否是首次运行

        Returns:
            bool: True表示首次运行，False表示已经运行过
        """
        return not self.flag_file.exists()

    def mark_completed(self):
        """标记新手引导已完成

        创建 first_run.json 文件，记录完成时间。
        """
        from datetime import datetime

        data = {
            "onboarding_completed": True,
            "completed_at": datetime.now().isoformat(),
            "version": "1.5.2"
        }

        with open(self.flag_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def reset(self):
        """重置首次运行标记（用于测试）

        删除 first_run.json 文件，下次启动会再次显示新手引导。
        """
        if self.flag_file.exists():
            self.flag_file.unlink()

    def get_completion_info(self):
        """获取新手引导完成信息

        Returns:
            dict: 包含完成时间和版本的字典，如果未完成则返回None
        """
        if not self.flag_file.exists():
            return None

        try:
            with open(self.flag_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
