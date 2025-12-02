"""
用户行为模型管理
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger("gaiya.services.user_behavior_model")


class UserBehaviorModel:
    """用户行为模型管理器"""

    DEFAULT_MODEL = {
        "version": "1.0",
        "user_id": None,
        "last_updated": None,
        "last_synced": None,
        "task_patterns": {},
        "global_patterns": {
            "time_efficiency": {
                "morning": 0.75,
                "afternoon": 0.65,
                "evening": 0.70
            },
            "average_focus_duration": 30,
            "typical_break_pattern": "每90分钟休息一次",
            "frequent_distractions": []
        },
        "learning_quality": {
            "total_corrections": 0,
            "accurate_predictions": 0,
            "accuracy_rate": 0.0,
            "needs_relearning": False
        },
        "data_retention": {
            "keep_days": 30,
            "oldest_data": None,
            "cleanup_last_run": None
        }
    }

    def __init__(self, model_path: Path):
        """
        初始化用户行为模型

        Args:
            model_path: 模型文件路径
        """
        self.model_path = model_path
        self.model = self._load_model()

    def _load_model(self) -> Dict:
        """加载模型文件,如果不存在则创建默认模型"""
        if not self.model_path.exists():
            logger.info(f"模型文件不存在,创建默认模型: {self.model_path}")
            model = self.DEFAULT_MODEL.copy()
            model['last_updated'] = datetime.now().isoformat()
            self.save_model(model)
            return model

        try:
            with open(self.model_path, 'r', encoding='utf-8') as f:
                model = json.load(f)
            logger.info(f"成功加载用户行为模型: {self.model_path}")
            return model
        except Exception as e:
            logger.error(f"加载模型失败,使用默认模型: {e}")
            return self.DEFAULT_MODEL.copy()

    def save_model(self, model: Optional[Dict] = None):
        """保存模型到文件"""
        if model is None:
            model = self.model

        try:
            # 确保目录存在
            self.model_path.parent.mkdir(parents=True, exist_ok=True)

            # 更新时间戳
            model['last_updated'] = datetime.now().isoformat()

            # 保存到文件
            with open(self.model_path, 'w', encoding='utf-8') as f:
                json.dump(model, f, ensure_ascii=False, indent=2)

            logger.info(f"模型已保存: {self.model_path}")
        except Exception as e:
            logger.error(f"保存模型失败: {e}")

    def get_task_pattern(self, task_name: str) -> Dict:
        """
        获取任务模式

        Args:
            task_name: 任务名称

        Returns:
            任务模式字典,如果不存在则返回空字典
        """
        return self.model['task_patterns'].get(task_name, {
            'typical_apps': {},
            'learning_samples': 0
        })

    def initialize_task_pattern(self, task_name: str, task_type: str, primary_apps: list):
        """
        初始化任务模式(用于首次使用或从模板创建)

        Args:
            task_name: 任务名称
            task_type: 任务类型
            primary_apps: 主要使用的应用列表
        """
        if task_name in self.model['task_patterns']:
            logger.info(f"任务模式已存在,跳过初始化: {task_name}")
            return

        initial_pattern = {
            'task_type': task_type,
            'typical_apps': {},
            'typical_duration_minutes': 0,
            'typical_completion_rate': 0.75,
            'focus_usage_rate': 0.0,
            'learning_samples': 0,
            'last_learned': datetime.now().strftime('%Y-%m-%d')
        }

        # 为主要应用设置初始权重
        for app in primary_apps:
            initial_pattern['typical_apps'][app] = {
                'weight': 0.75,
                'confidence': 'template',
                'sample_count': 0
            }

        self.model['task_patterns'][task_name] = initial_pattern
        self.save_model()

        logger.info(f"已初始化任务模式: {task_name}, 主要应用: {primary_apps}")

    def learn_from_correction(self, task_name: str, apps_used: list, correction_type: str):
        """
        从用户修正中学习

        Args:
            task_name: 任务名称
            apps_used: 使用的应用列表 [{'app': 'Cursor.exe', 'duration': 85}, ...]
            correction_type: 修正类型 'underestimated'|'overestimated'|'accurate'
        """
        if task_name not in self.model['task_patterns']:
            self.model['task_patterns'][task_name] = {
                'typical_apps': {},
                'learning_samples': 0
            }

        pattern = self.model['task_patterns'][task_name]

        # 确定学习方向
        if correction_type == 'underestimated':
            delta = 0.05  # AI低估了,提升权重
        elif correction_type == 'overestimated':
            delta = -0.05  # AI高估了,降低权重
        else:  # accurate
            delta = 0.02  # 准确预测,小幅增强权重

        # 更新应用权重
        for app_info in apps_used:
            app = app_info['app']
            duration = app_info['duration']

            # 只调整使用时间较长的应用(>10分钟)
            if duration < 10:
                continue

            if app not in pattern['typical_apps']:
                # 新应用,初始化
                pattern['typical_apps'][app] = {
                    'weight': 0.5,
                    'confidence': 'low',
                    'sample_count': 0
                }

            app_info_model = pattern['typical_apps'][app]

            # 更新权重(限制在0.0-1.0)
            old_weight = app_info_model['weight']
            new_weight = max(0.0, min(1.0, old_weight + delta))
            app_info_model['weight'] = round(new_weight, 2)

            # 更新样本数
            app_info_model['sample_count'] += 1

            # 更新置信度
            if app_info_model['sample_count'] >= 10:
                if new_weight >= 0.8:
                    app_info_model['confidence'] = 'high'
                elif new_weight >= 0.5:
                    app_info_model['confidence'] = 'medium'
                else:
                    app_info_model['confidence'] = 'low'

        # 更新学习样本数
        pattern['learning_samples'] = pattern.get('learning_samples', 0) + 1
        pattern['last_learned'] = datetime.now().strftime('%Y-%m-%d')

        # 更新学习质量指标
        self.model['learning_quality']['total_corrections'] += 1
        if correction_type == 'accurate':
            self.model['learning_quality']['accurate_predictions'] += 1

        # 重新计算准确率
        total = self.model['learning_quality']['total_corrections']
        accurate = self.model['learning_quality']['accurate_predictions']
        self.model['learning_quality']['accuracy_rate'] = accurate / total if total > 0 else 0

        # 检查是否需要重新学习
        if total >= 20 and self.model['learning_quality']['accuracy_rate'] < 0.6:
            self.model['learning_quality']['needs_relearning'] = True
            logger.warning(f"模型准确率低于60%,建议重新学习")
        else:
            self.model['learning_quality']['needs_relearning'] = False

        self.save_model()

        logger.info(f"已从修正中学习: {task_name}, 修正类型: {correction_type}, 样本数: {pattern['learning_samples']}")

    def cleanup_old_data(self):
        """清理30天前的数据"""
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # 清理样本数过少且权重低的应用记录
        for task_name, pattern in list(self.model['task_patterns'].items()):
            if 'typical_apps' not in pattern:
                continue

            apps_to_remove = []
            for app, app_info in pattern['typical_apps'].items():
                # 样本少且权重低的,认为是噪音
                if app_info.get('sample_count', 0) < 3 and app_info.get('weight', 0) < 0.4:
                    apps_to_remove.append(app)

            for app in apps_to_remove:
                del pattern['typical_apps'][app]
                logger.debug(f"清理低质量应用记录: {task_name} - {app}")

        # 更新清理时间
        self.model['data_retention']['cleanup_last_run'] = datetime.now().strftime('%Y-%m-%d')
        self.model['data_retention']['oldest_data'] = cutoff_date

        self.save_model()
        logger.info(f"已清理30天前的数据,截止日期: {cutoff_date}")

    def get_model_stats(self) -> Dict:
        """获取模型统计信息"""
        total_tasks = len(self.model['task_patterns'])
        total_learning_samples = sum([
            pattern.get('learning_samples', 0)
            for pattern in self.model['task_patterns'].values()
        ])

        return {
            'total_tasks': total_tasks,
            'total_learning_samples': total_learning_samples,
            'accuracy_rate': self.model['learning_quality']['accuracy_rate'],
            'needs_relearning': self.model['learning_quality']['needs_relearning'],
            'last_updated': self.model['last_updated'],
            'last_synced': self.model['last_synced']
        }

    def sync_to_cloud(self, auth_client) -> bool:
        """
        同步模型到云端(会员功能)

        Args:
            auth_client: 认证客户端

        Returns:
            是否同步成功
        """
        if not auth_client.is_premium():
            logger.info("非会员用户,跳过云端同步")
            return False

        try:
            response = auth_client.upload_user_model(self.model)

            if response.get('success'):
                self.model['last_synced'] = datetime.now().isoformat()
                self.save_model()
                logger.info("模型已同步到云端")
                return True
            else:
                logger.error(f"云端同步失败: {response.get('error')}")
                return False
        except Exception as e:
            logger.error(f"云端同步异常: {e}")
            return False

    def sync_from_cloud(self, auth_client) -> bool:
        """
        从云端下载模型(会员功能,用于新设备)

        Args:
            auth_client: 认证客户端

        Returns:
            是否同步成功
        """
        if not auth_client.is_premium():
            logger.info("非会员用户,跳过云端同步")
            return False

        try:
            cloud_model = auth_client.download_user_model()

            if cloud_model:
                # 简单策略:云端数据覆盖本地
                # TODO: 实现更智能的合并策略
                self.model = cloud_model
                self.save_model()
                logger.info("已从云端同步模型")
                return True
            else:
                logger.info("云端暂无模型数据")
                return False
        except Exception as e:
            logger.error(f"云端同步异常: {e}")
            return False
