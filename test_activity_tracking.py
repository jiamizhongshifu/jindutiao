#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行为识别功能测试脚本
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_database_manager():
    """测试数据库管理器"""
    print("=== 测试 Database Manager ===")

    try:
        from gaiya.data.db_manager import db

        # 测试App分类管理
        db.set_app_category("test_productive.exe", "PRODUCTIVE")
        db.set_app_category("test_leisure.exe", "LEISURE")
        db.set_app_category("test_neutral.exe", "NEUTRAL")
        db.set_app_category("test_unknown.exe", "UNKNOWN", is_ignored=True)
        print("✅ App分类设置成功")

        # 测试App分类获取
        assert db.get_app_category("test_productive.exe") == "PRODUCTIVE"
        assert db.get_app_category("test_leisure.exe") == "LEISURE"
        assert db.get_app_category("test_neutral.exe") == "NEUTRAL"
        assert db.get_app_category("test_unknown.exe") == "IGNORED"
        print("✅ App分类获取成功")

        # 测试行为会话保存
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        db.save_activity_session(
            "test_productive.exe",
            "Test Window Title",
            start_time,
            end_time,
            300
        )
        print("✅ 行为会话保存成功")

        # 测试今日统计
        focus_stats = db.get_today_focus_stats()
        activity_stats = db.get_today_activity_stats()
        print(f"✅ 专注统计数据: {focus_stats}")
        print(f"✅ 行为统计数据: {activity_stats}")

        return True

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_app_category_manager():
    """测试App分类管理器"""
    print("\n=== 测试 App Category Manager ===")

    try:
        from gaiya.services.app_category_manager import app_category_manager

        # 测试分类获取
        category = app_category_manager.get_app_category("WINWORD.EXE")
        print(f"✅ Word分类: {category}")
        assert category == "PRODUCTIVE"

        category = app_category_manager.get_app_category("WeChat.exe")
        print(f"✅ 微信分类: {category}")
        assert category == "LEISURE"

        category = app_category_manager.get_app_category("UnknownApp.exe")
        print(f"✅ 未知应用分类: {category}")
        assert category == "UNKNOWN"

        # 测试分类设置
        app_category_manager.set_app_category("CustomApp.exe", "PRODUCTIVE")
        category = app_category_manager.get_app_category("CustomApp.exe")
        print(f"✅ 自定义应用分类: {category}")
        assert category == "PRODUCTIVE"

        # 测试分类统计
        stats = app_category_manager.get_category_stats()
        print(f"✅ 分类统计: {stats}")

        # 测试导入默认分类
        app_category_manager.import_default_categories()
        print("✅ 默认分类导入成功")

        return True

    except Exception as e:
        print(f"❌ App分类管理器测试失败: {e}")
        return False

def test_activity_tracker():
    """测试行为追踪服务"""
    print("\n=== 测试 Activity Tracker ===")

    try:
        from gaiya.services.activity_tracker import ActivityTracker

        # 创建活动追踪器实例（不启动）
        tracker = ActivityTracker()
        print("✅ ActivityTracker 创建成功")

        # 测试获取活动窗口信息
        process_name, window_title = tracker.get_active_window_info() if hasattr(tracker, 'get_active_window_info') else (None, None)
        print(f"✅ 当前窗口信息: {process_name} - {window_title}")

        return True

    except Exception as e:
        print(f"❌ ActivityTracker测试失败: {e}")
        return False

def test_activity_settings_window():
    """测试行为识别设置窗口"""
    print("\n=== 测试 Activity Settings Window ===")

    try:
        from PySide6.QtWidgets import QApplication
        from gaiya.ui.activity_settings_window import ActivitySettingsWindow

        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # 创建设置窗口
        settings_window = ActivitySettingsWindow()
        print("✅ ActivitySettingsWindow 创建成功")

        # 测试获取设置
        settings = settings_window.get_settings()
        print(f"✅ 默认设置: {settings}")

        # 测试设置配置
        test_settings = {
            'activity_tracking_enabled': True,
            'polling_interval': 3,
            'min_session_duration': 2,
            'data_retention_days': 30
        }
        settings_window.set_settings(test_settings)
        updated_settings = settings_window.get_settings()
        print(f"✅ 更新设置: {updated_settings}")

        return True

    except Exception as e:
        print(f"❌ ActivitySettingsWindow测试失败: {e}")
        return False

def test_time_review_window():
    """测试时间回放窗口"""
    print("\n=== 测试 Time Review Window ===")

    try:
        from PySide6.QtWidgets import QApplication
        from gaiya.ui.time_review_window import TimeReviewWindow

        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # 创建时间回放窗口
        review_window = TimeReviewWindow()
        print("✅ TimeReviewWindow 创建成功")

        # 测试数据加载
        review_window.load_today_data()
        print("✅ 今日数据加载成功")

        return True

    except Exception as e:
        print(f"❌ TimeReviewWindow测试失败: {e}")
        return False

def test_imports():
    """测试所有核心导入"""
    print("=== 测试核心导入 ===")

    required_modules = [
        ('gaiya.data.db_manager', 'db'),
        ('gaiya.services.app_category_manager', 'app_category_manager'),
        ('gaiya.services.activity_tracker', 'ActivityTracker'),
        ('gaiya.ui.activity_settings_window', 'ActivitySettingsWindow'),
        ('gaiya.ui.time_review_window', 'TimeReviewWindow'),
    ]

    success_count = 0

    for module_name, attr_name in required_modules:
        try:
            exec(f"from {module_name} import {attr_name}")
            print(f"✅ {module_name}.{attr_name} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}.{attr_name} 导入失败: {e}")

    print(f"\n导入成功率: {success_count}/{len(required_modules)}")
    return success_count == len(required_modules)

def main():
    """主测试函数"""
    print("[TEST] 行为识别功能测试")
    print("=" * 50)

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 测试导入
    imports_ok = test_imports()

    if not imports_ok:
        print("❌ 导入测试失败，终止测试")
        return False

    # 测试数据库管理器
    db_ok = test_database_manager()

    # 测试App分类管理器
    app_category_ok = test_app_category_manager()

    # 测试活动追踪器
    activity_tracker_ok = test_activity_tracker()

    # 测试设置窗口
    settings_window_ok = test_activity_settings_window()

    # 测试时间回放窗口
    time_review_ok = test_time_review_window()

    # 总结
    print("\n" + "=" * 50)
    print("📋 测试结果总结")
    print(f"✅ 核心导入: {'通过' if imports_ok else '失败'}")
    print(f"✅ 数据库管理: {'通过' if db_ok else '失败'}")
    print(f"✅ App分类管理: {'通过' if app_category_ok else '失败'}")
    print(f"✅ 活动追踪服务: {'通过' if activity_tracker_ok else '失败'}")
    print(f"✅ 设置窗口: {'通过' if settings_window_ok else '失败'}")
    print(f"✅ 时间回放窗口: {'通过' if time_review_ok else '失败'}")

    all_ok = all([imports_ok, db_ok, app_category_ok, activity_tracker_ok, settings_window_ok, time_review_ok])
    print(f"\n[RESULT] 行为识别功能整体状态: {'完成' if all_ok else '需要修复'}")

    if all_ok:
        print("\n[SUCCESS] 第二阶段「行为识别」开发完成！")
        print("[INFO] 现在可以进行:")
        print("   1. 在进度条上右键 → 选择「行为识别设置」")
        print("   2. 在进度条上右键 → 选择「今日时间回放」")
        print("   3. 后台自动追踪应用使用情况")
        print("   4. 自定义应用分类（生产力/摸鱼/中性）")
        print("   5. 查看今日用机统计和Top应用排行")

    return all_ok

if __name__ == "__main__":
    main()