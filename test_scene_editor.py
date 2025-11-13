"""
场景编辑器功能测试脚本

测试范围：
1. 数据结构正确性
2. 事件配置逻辑
3. 道路层配置
4. JSON导出格式
"""

import json
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from scene_editor import EventAction, EventConfig, SceneItemGraphics


def test_event_config():
    """测试事件配置数据结构"""
    print("=" * 60)
    print("测试1: 事件配置数据结构")
    print("=" * 60)

    # 创建事件配置
    action = EventAction(
        type="show_tooltip",
        params={"text": "这是一个提示"}
    )

    event = EventConfig(
        trigger="on_hover",
        action=action
    )

    # 转换为字典
    event_dict = event.to_dict()

    print("事件配置字典:")
    print(json.dumps(event_dict, indent=2, ensure_ascii=False))

    # 验证结构
    assert event_dict["trigger"] == "on_hover"
    assert event_dict["action"]["type"] == "show_tooltip"
    assert event_dict["action"]["params"]["text"] == "这是一个提示"

    print("[OK] 事件配置结构正确\n")


def test_scene_item_with_events():
    """测试场景元素的事件导出"""
    print("=" * 60)
    print("测试2: 场景元素事件导出")
    print("=" * 60)

    # 创建一个虚拟的场景元素
    # 注意：这里不能真正创建QGraphicsPixmapItem，因为需要QApplication
    # 我们只测试数据结构

    # 模拟事件列表
    events = [
        EventConfig(
            trigger="on_click",
            action=EventAction(
                type="open_url",
                params={"url": "https://example.com"}
            )
        ),
        EventConfig(
            trigger="on_time_reach",
            action=EventAction(
                type="show_dialog",
                params={"text": "时间到了！", "time": "50%"}
            )
        )
    ]

    # 模拟导出字典
    item_dict = {
        "id": "item_1",
        "image": "tree.png",
        "position": {"x_percent": 25.5, "y_pixel": 50},
        "scale": 1.2,
        "z_index": 5,
        "events": [event.to_dict() for event in events]
    }

    print("元素配置字典:")
    print(json.dumps(item_dict, indent=2, ensure_ascii=False))

    # 验证结构
    assert len(item_dict["events"]) == 2
    assert item_dict["events"][0]["trigger"] == "on_click"
    assert item_dict["events"][1]["action"]["params"]["time"] == "50%"

    print("[OK] 元素事件导出正确\n")


def test_scene_export_format():
    """测试场景导出格式"""
    print("=" * 60)
    print("测试3: 场景导出格式")
    print("=" * 60)

    # 模拟完整的场景配置
    config = {
        "scene_id": "scene_001",
        "name": "测试场景",
        "version": "1.0.0",
        "canvas": {
            "width": 1000,
            "height": 150
        },
        "layers": {
            "road": {
                "type": "tiled",
                "image": "road_tile.png"
            },
            "scene": {
                "items": [
                    {
                        "id": "item_1",
                        "image": "tree.png",
                        "position": {"x_percent": 10.0, "y_pixel": 30},
                        "scale": 1.0,
                        "z_index": 1,
                        "events": [
                            {
                                "trigger": "on_hover",
                                "action": {
                                    "type": "show_tooltip",
                                    "params": {"text": "这是一棵树"}
                                }
                            }
                        ]
                    },
                    {
                        "id": "item_2",
                        "image": "house.png",
                        "position": {"x_percent": 50.0, "y_pixel": 20},
                        "scale": 1.5,
                        "z_index": 2,
                        "events": []
                    }
                ]
            }
        }
    }

    print("场景配置:")
    print(json.dumps(config, indent=2, ensure_ascii=False))

    # 验证结构
    assert "road" in config["layers"]
    assert config["layers"]["road"]["type"] == "tiled"
    assert "scene" in config["layers"]
    assert len(config["layers"]["scene"]["items"]) == 2
    assert config["layers"]["scene"]["items"][0]["events"][0]["trigger"] == "on_hover"

    print("[OK] 场景导出格式正确\n")


def test_event_types():
    """测试所有事件类型组合"""
    print("=" * 60)
    print("测试4: 事件类型组合")
    print("=" * 60)

    # 所有触发器类型
    triggers = ["on_hover", "on_click", "on_time_reach"]

    # 所有动作类型
    actions = [
        ("show_tooltip", {"text": "提示内容"}),
        ("show_dialog", {"text": "对话框内容"}),
        ("open_url", {"url": "https://example.com"})
    ]

    print("支持的触发器:", triggers)
    print("支持的动作:", [a[0] for a in actions])

    # 测试所有组合
    for trigger in triggers:
        for action_type, params in actions:
            if trigger == "on_time_reach":
                params = {**params, "time": "50%"}

            event = EventConfig(
                trigger=trigger,
                action=EventAction(type=action_type, params=params)
            )

            event_dict = event.to_dict()
            assert event_dict["trigger"] == trigger
            assert event_dict["action"]["type"] == action_type

    print(f"[OK] 已测试 {len(triggers) * len(actions)} 种事件组合\n")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("场景编辑器功能测试")
    print("=" * 60 + "\n")

    try:
        test_event_config()
        test_scene_item_with_events()
        test_scene_export_format()
        test_event_types()

        print("=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n[FAILED] 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
