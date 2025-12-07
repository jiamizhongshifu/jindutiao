"""
GaiYa 性能测试和稳定性诊断工具
用于检测内存泄漏、CPU使用率、响应时间和潜在崩溃点
"""
import sys
import os
import time
import psutil
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.metrics = []

    def capture_metrics(self, label=""):
        """捕获当前性能指标"""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            metric = {
                "timestamp": datetime.now().isoformat(),
                "label": label,
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "threads": self.process.num_threads(),
                "elapsed_seconds": time.time() - self.start_time
            }

            self.metrics.append(metric)

            print(f"[{label}] CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB, Threads: {metric['threads']}")

            return metric

        except Exception as e:
            print(f"[ERROR] 捕获指标失败: {e}")
            return None

    def save_report(self, filepath="performance_report.json"):
        """保存性能报告"""
        import json

        report = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "total_duration_seconds": time.time() - self.start_time,
            "metrics": self.metrics,
            "summary": self._calculate_summary()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 性能报告已保存到: {filepath}")
        return report

    def _calculate_summary(self):
        """计算汇总统计"""
        if not self.metrics:
            return {}

        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_mb"] for m in self.metrics]

        return {
            "cpu_avg": sum(cpu_values) / len(cpu_values),
            "cpu_max": max(cpu_values),
            "memory_avg": sum(memory_values) / len(memory_values),
            "memory_max": max(memory_values),
            "memory_increase_mb": memory_values[-1] - memory_values[0],
            "samples_count": len(self.metrics)
        }


def test_core_modules():
    """测试核心模块加载"""
    print("\n=== 测试核心模块加载 ===\n")

    monitor = PerformanceMonitor()
    monitor.capture_metrics("开始测试")

    test_results = []

    # 测试1: 导入核心模块
    modules_to_test = [
        ("gaiya.core.auth_client", "AuthClient"),
        ("gaiya.core.behavior_tracker", "BehaviorTracker"),
        ("gaiya.ui.membership_ui", "MembershipDialog"),
        ("config_gui", "ConfigGUI"),
    ]

    for module_name, class_name in modules_to_test:
        try:
            print(f"[测试] 导入 {module_name}...")
            __import__(module_name)
            monitor.capture_metrics(f"导入 {module_name}")
            test_results.append((module_name, "✅ 成功", None))

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[错误] {module_name} 导入失败: {error_msg}")
            traceback.print_exc()
            test_results.append((module_name, "❌ 失败", error_msg))

    # 测试2: 数据库连接
    try:
        print("\n[测试] 数据库连接...")
        from gaiya.utils.db import get_db_path
        db_path = get_db_path()
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / 1024 / 1024
            print(f"✅ 数据库文件存在: {db_path} ({size_mb:.2f}MB)")
            test_results.append(("数据库连接", "✅ 成功", f"大小: {size_mb:.2f}MB"))
        else:
            print(f"⚠️ 数据库文件不存在: {db_path}")
            test_results.append(("数据库连接", "⚠️ 警告", "文件不存在"))

        monitor.capture_metrics("数据库检查")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[错误] 数据库连接失败: {error_msg}")
        test_results.append(("数据库连接", "❌ 失败", error_msg))

    # 测试3: 配置文件加载
    try:
        print("\n[测试] 配置文件加载...")
        from gaiya.utils.config import Config
        config = Config()
        print(f"✅ 配置加载成功")
        test_results.append(("配置文件", "✅ 成功", None))
        monitor.capture_metrics("配置加载")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[错误] 配置加载失败: {error_msg}")
        test_results.append(("配置文件", "❌ 失败", error_msg))

    monitor.capture_metrics("测试完成")

    # 生成报告
    print("\n=== 测试结果汇总 ===\n")
    for name, status, error in test_results:
        print(f"{status} {name}")
        if error:
            print(f"   错误: {error}")

    report = monitor.save_report("stability_test_report.json")

    # 检查性能问题
    summary = report["summary"]
    print("\n=== 性能指标 ===\n")
    print(f"CPU 使用率: 平均 {summary['cpu_avg']:.1f}%, 峰值 {summary['cpu_max']:.1f}%")
    print(f"内存使用: 平均 {summary['memory_avg']:.1f}MB, 峰值 {summary['memory_max']:.1f}MB")
    print(f"内存增长: {summary['memory_increase_mb']:.1f}MB")

    # 性能警告
    warnings = []
    if summary['cpu_max'] > 50:
        warnings.append(f"⚠️ CPU 峰值过高: {summary['cpu_max']:.1f}%")
    if summary['memory_max'] > 500:
        warnings.append(f"⚠️ 内存占用过高: {summary['memory_max']:.1f}MB")
    if summary['memory_increase_mb'] > 100:
        warnings.append(f"⚠️ 可能存在内存泄漏: 增长 {summary['memory_increase_mb']:.1f}MB")

    if warnings:
        print("\n⚠️ 性能警告:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("\n✅ 性能指标正常")

    return test_results, report


def test_memory_leak():
    """测试内存泄漏"""
    print("\n=== 内存泄漏测试 ===\n")
    print("此测试将创建和销毁对象,检测内存是否正确释放...")

    monitor = PerformanceMonitor()
    monitor.capture_metrics("开始泄漏测试")

    # 模拟多次操作
    for i in range(10):
        try:
            # 模拟打开配置窗口
            from PySide6.QtWidgets import QApplication, QDialog
            if not QApplication.instance():
                app = QApplication(sys.argv)

            dialog = QDialog()
            dialog.setWindowTitle(f"测试对话框 {i+1}")
            dialog.resize(400, 300)

            # 立即关闭
            dialog.close()
            dialog.deleteLater()

            monitor.capture_metrics(f"迭代 {i+1}")

            time.sleep(0.1)  # 短暂延迟

        except Exception as e:
            print(f"[错误] 迭代 {i+1} 失败: {e}")

    monitor.capture_metrics("泄漏测试完成")

    report = monitor.save_report("memory_leak_test_report.json")
    summary = report["summary"]

    if summary['memory_increase_mb'] > 50:
        print(f"\n❌ 检测到内存泄漏: 增长 {summary['memory_increase_mb']:.1f}MB")
    else:
        print(f"\n✅ 内存泄漏测试通过: 增长 {summary['memory_increase_mb']:.1f}MB")

    return report


def check_crash_common_causes():
    """检查常见崩溃原因"""
    print("\n=== 检查常见崩溃原因 ===\n")

    issues = []

    # 检查1: Qt 插件路径
    try:
        from PySide6.QtCore import QCoreApplication
        plugin_paths = QCoreApplication.libraryPaths()
        print(f"✅ Qt 插件路径: {plugin_paths}")
    except Exception as e:
        issues.append(f"❌ Qt 插件路径错误: {e}")

    # 检查2: 数据库锁
    try:
        db_path = "data/gaiya.db"
        if os.path.exists(db_path):
            # 尝试打开数据库
            import sqlite3
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            result = cursor.fetchone()
            conn.close()
            print(f"✅ 数据库可访问: {result[0]} 个表")
        else:
            print(f"⚠️ 数据库不存在: {db_path}")
    except Exception as e:
        issues.append(f"❌ 数据库锁定或损坏: {e}")

    # 检查3: 日志文件权限
    try:
        log_file = "gaiya.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] 权限测试\n")
        print(f"✅ 日志文件可写入: {log_file}")
    except Exception as e:
        issues.append(f"❌ 日志文件权限错误: {e}")

    # 检查4: 临时文件目录
    try:
        import tempfile
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "gaiya_test.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✅ 临时目录可用: {temp_dir}")
    except Exception as e:
        issues.append(f"❌ 临时目录不可用: {e}")

    if issues:
        print("\n❌ 发现以下问题:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ 所有检查通过")

    return issues


if __name__ == "__main__":
    print("=" * 60)
    print("GaiYa 性能测试和稳定性诊断工具")
    print("=" * 60)

    try:
        # 运行测试
        test_results, stability_report = test_core_modules()

        leak_report = test_memory_leak()

        crash_issues = check_crash_common_causes()

        # 最终报告
        print("\n" + "=" * 60)
        print("诊断完成")
        print("=" * 60)

        print("\n📊 报告文件:")
        print("  - stability_test_report.json (模块加载测试)")
        print("  - memory_leak_test_report.json (内存泄漏测试)")

        if crash_issues:
            print("\n⚠️ 发现潜在崩溃原因,请查看上方详细信息")
        else:
            print("\n✅ 未发现明显的崩溃原因")

        print("\n💡 建议:")
        print("  1. 运行应用时,观察内存和CPU使用率")
        print("  2. 复现崩溃时,记录操作步骤")
        print("  3. 检查 gaiya.log 中的错误信息")
        print("  4. 如果频繁崩溃,尝试删除 data/gaiya.db 重新初始化")

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)
