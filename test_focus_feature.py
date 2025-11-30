#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红温专注仓功能测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_database_manager():
    """测试数据库管理器"""
    print("=== 测试 Database Manager ===")

    try:
        from gaiya.data.db_manager import db

        # 测试专注会话创建
        session_id = db.create_focus_session("test_task_001")
        print(f"✅ 专注会话创建成功: {session_id}")

        # 测试完成会话
        db.complete_focus_session(session_id)
        print("✅ 专注会话完成成功")

        # 测试今日统计
        stats = db.get_today_focus_stats()
        print(f"✅ 专注统计数据: {stats}")

        return True

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_pomodoro_panel():
    """测试番茄钟面板"""
    print("\n=== 测试 Pomodoro Panel ===")

    try:
        from gaiya.ui.pomodoro_panel import PomodoroPanel
        from gaiya.data.db_manager import db

        # 模拟基本配置
        config = {
            'bar_height': 10,
            'background_opacity': 180,
            'pomodoro': {
                'work_duration': 1500,
                'short_break': 300,
                'long_break': 900,
                'long_break_interval': 4
            }
        }

        # 模拟托盘图标
        class MockTrayIcon:
            def showMessage(self, title, message, icon_type, duration=0):
                print(f"托盘通知: {title} - {message}")

        tray_icon = MockTrayIcon()

        # 创建带有 time_block_id 的番茄钟面板
        pomodoro_panel = PomodoroPanel(
            config=config,
            tray_icon=tray_icon,
            logger=None,  # 简化日志
            time_block_id="test_task_001"
        )

        print(f"✅ PomodoroPanel 创建成功 (time_block_id: test_task_001)")
        print(f"✅ 专注会话ID: {getattr(pomodoro_panel, 'current_focus_session_id', 'None')}")

        # 测试专注会话方法
        if hasattr(pomodoro_panel, '_get_focus_session_db'):
            db_instance = pomodoro_panel._get_focus_session_db()
            print(f"✅ 数据库管理器获取: {'成功' if db_instance else '失败'}")

        return True

    except Exception as e:
        print(f"❌ 番茄钟面板测试失败: {e}")
        return False

def test_imports():
    """测试所有核心导入"""
    print("=== 测试核心导入 ===")

    required_modules = [
        ('gaiya.data.db_manager', 'db'),
        ('gaiya.ui.pomodoro_panel', 'PomodoroPanel'),
        ('gaiya.core.pomodoro_state', 'PomodoroState'),
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
    print("🔥 红温专注仓功能测试")
    print("=" * 50)

    # 测试导入
    imports_ok = test_imports()

    if not imports_ok:
        print("❌ 导入测试失败，终止测试")
        return False

    # 测试数据库
    db_ok = test_database_manager()

    # 测试番茄钟面板
    pomodoro_ok = test_pomodoro_panel()

    # 总结
    print("\n" + "=" * 50)
    print("📋 测试结果总结")
    print(f"✅ 核心导入: {'通过' if imports_ok else '失败'}")
    print(f"✅ 数据库管理: {'通过' if db_ok else '失败'}")
    print(f"✅ 番茄钟集成: {'通过' if pomodoro_ok else '失败'}")

    all_ok = imports_ok and db_ok and pomodoro_ok
    print(f"\n🎯 第一阶段整体状态: {'✅ 完成' if all_ok else '❌ 需要修复'}")

    if all_ok:
        print("\n🚀 第一阶段「红温专注仓」开发完成！")
        print("📋 现在可以进行:")
        print("   1. 在时间块上右键 → 选择「🔥 开启红温专注仓」")
        print("   2. 自动启动绑定到时间块的番茄钟")
        print("   3. 专注时间自动记录到数据库")
        print("   4. 专注会话完成时自动更新数据库")

    return all_ok

if __name__ == "__main__":
    main()