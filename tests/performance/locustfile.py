"""
Locust压力测试脚本 - GaiYa API性能测试

使用方法:
    locust -f tests/performance/locustfile.py --host=https://jindutiao.vercel.app

Web UI: http://localhost:8089

测试场景:
- 配额查询 (高频)
- 任务规划 (中频)
- 订阅状态查询 (低频)
"""

from locust import HttpUser, task, between
import random


class GaiYaUser(HttpUser):
    """
    模拟GaiYa用户行为的负载测试类

    wait_time: 模拟用户在请求之间的等待时间（1-3秒）
    """
    wait_time = between(1, 3)

    def on_start(self):
        """
        每个用户启动时执行一次
        模拟用户登录并获取user_id
        """
        # 在实际测试中，这里应该从测试数据库获取真实的user_id
        # 暂时使用模拟的user_id
        self.user_id = f"test-user-{random.randint(1, 1000)}"
        self.user_tier = random.choice(["free", "pro"])

    @task(5)
    def check_quota_status(self):
        """
        任务权重: 5 (最高频)
        场景: 用户查询剩余配额

        预期性能:
        - 响应时间 < 500ms (P95)
        - 成功率 > 99%
        """
        with self.client.get(
            f"/api/quota-status?user_tier={self.user_tier}",
            name="/api/quota-status",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # 验证响应格式
                    if "remaining" in data:
                        response.success()
                    else:
                        response.failure("Missing 'remaining' field in response")
                except ValueError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)
    def plan_tasks(self):
        """
        任务权重: 3 (中频)
        场景: 用户使用AI生成任务规划

        预期性能:
        - 响应时间 < 5s (AI生成较慢是正常的)
        - 成功率 > 95% (考虑到AI服务可能偶尔失败)
        """
        # 模拟的任务描述
        task_descriptions = [
            "完成项目报告并提交",
            "学习Python编程",
            "健身锻炼30分钟",
            "阅读技术文章",
            "整理代码仓库"
        ]

        payload = {
            "task_description": random.choice(task_descriptions),
            "user_tier": self.user_tier
        }

        with self.client.post(
            "/api/plan-tasks",
            json=payload,
            name="/api/plan-tasks",
            catch_response=True,
            timeout=10  # AI请求可能需要更长时间
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # 验证响应格式
                    if "tasks" in data or "subtasks" in data:
                        response.success()
                    else:
                        response.failure("Missing task data in response")
                except ValueError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                # 配额不足是预期行为（对于免费用户）
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def check_subscription_status(self):
        """
        任务权重: 2 (低频)
        场景: 用户查询订阅状态

        预期性能:
        - 响应时间 < 500ms (P95)
        - 成功率 > 99%
        """
        with self.client.get(
            f"/api/subscription-status?user_id={self.user_id}",
            name="/api/subscription-status",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # 订阅状态查询应返回用户等级信息
                    response.success()
                except ValueError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def health_check(self):
        """
        任务权重: 1 (偶尔)
        场景: 健康检查端点

        预期性能:
        - 响应时间 < 200ms
        - 成功率 = 100%
        """
        with self.client.get(
            "/api/health",
            name="/api/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class AdminUser(HttpUser):
    """
    模拟管理员用户的负载测试类

    管理员操作频率较低，主要用于测试管理端点的性能
    """
    wait_time = between(5, 15)

    @task
    def get_system_stats(self):
        """
        场景: 管理员查看系统统计
        （如果有这样的端点）
        """
        # 暂时跳过，等待实际的管理端点实现
        pass


# Locust配置建议
"""
运行命令示例:

1. 基本压力测试 (100用户, 10秒增长):
   locust -f tests/performance/locustfile.py \\
          --host=https://jindutiao.vercel.app \\
          --users 100 \\
          --spawn-rate 10 \\
          --run-time 5m

2. 无UI模式 (适合CI/CD):
   locust -f tests/performance/locustfile.py \\
          --host=https://jindutiao.vercel.app \\
          --users 50 \\
          --spawn-rate 5 \\
          --run-time 3m \\
          --headless \\
          --html=reports/performance_report.html

3. 性能基准测试 (验证100 QPS目标):
   locust -f tests/performance/locustfile.py \\
          --host=https://jindutiao.vercel.app \\
          --users 200 \\
          --spawn-rate 20 \\
          --run-time 10m

验收标准:
- P95响应时间 < 500ms (配额查询、订阅查询)
- P95响应时间 < 5s (AI任务规划)
- 支持100 QPS
- 错误率 < 1%
"""
