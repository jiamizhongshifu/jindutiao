"""
场景加载器测试脚本

测试 SceneLoader 的基本功能：
1. 初始化和目录检测
2. 获取可用场景列表
3. 加载场景配置
4. 配置验证
5. 资源路径解析
"""

import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from gaiya.scene import SceneLoader, SceneConfig
except ImportError as e:
    print(f"导入失败: {e}")
    print(f"当前 Python 路径: {sys.path}")
    sys.exit(1)


def test_scene_loader():
    """测试场景加载器"""
    print("\n" + "="*80)
    print("场景加载器功能测试")
    print("="*80)

    # 1. 测试初始化
    print("\n[测试 1] 初始化 SceneLoader...")
    loader = SceneLoader()
    print(f"[OK] 初始化成功")
    print(f"  场景目录: {loader.scenes_dir}")
    print(f"  目录存在: {loader.scenes_dir.exists()}")

    # 2. 测试获取可用场景列表
    print("\n[测试 2] 获取可用场景列表...")
    scenes = loader.get_available_scenes()
    print(f"[OK] 找到 {len(scenes)} 个场景")
    for scene_name in scenes:
        print(f"  - {scene_name}")

    if not scenes:
        print("  ⚠ 警告：没有找到可用的场景")
        print("  请确保 scenes/ 目录下有包含 config.json 的子目录")
        return

    # 3. 测试加载场景配置
    test_scene_name = scenes[0]  # 使用第一个可用场景
    print(f"\n[测试 3] 加载场景配置: {test_scene_name}")

    scene_config = loader.load_scene(test_scene_name)

    if scene_config is None:
        print(f"  [ERROR] 加载失败")
        return

    print(f"[OK] 加载成功")
    print(f"  场景ID: {scene_config.scene_id}")
    print(f"  场景名称: {scene_config.name}")
    print(f"  版本: {scene_config.version}")
    print(f"  画布尺寸: {scene_config.canvas.width}x{scene_config.canvas.height}")

    # 4. 测试道路层
    print(f"\n[测试 4] 道路层配置...")
    if scene_config.road_layer:
        print(f"[OK] 存在道路层")
        print(f"  类型: {scene_config.road_layer.type}")
        print(f"  图片: {scene_config.road_layer.image}")
        print(f"  层级: {scene_config.road_layer.z_index}")
        print(f"  缩放: {scene_config.road_layer.scale}")
        print(f"  图片文件存在: {Path(scene_config.road_layer.image).exists()}")
    else:
        print(f"  ⚠ 无道路层配置")

    # 5. 测试场景元素
    print(f"\n[测试 5] 场景元素...")
    items = scene_config.scene_layer.items
    print(f"[OK] 找到 {len(items)} 个场景元素")

    for i, item in enumerate(items, 1):
        print(f"\n  元素 {i}:")
        print(f"    ID: {item.id}")
        print(f"    图片: {item.image}")
        print(f"    位置: ({item.position.x_percent}%, {item.position.y_pixel}px)")
        print(f"    缩放: {item.scale}")
        print(f"    层级: {item.z_index}")
        print(f"    事件数: {len(item.events)}")
        print(f"    图片文件存在: {Path(item.image).exists()}")

        # 显示事件详情
        for j, event in enumerate(item.events, 1):
            print(f"      事件 {j}: {event.trigger} -> {event.action.type}")
            print(f"        参数: {event.action.params}")

    # 6. 测试 z-index 排序
    print(f"\n[测试 6] Z-index 排序...")
    sorted_items = scene_config.get_all_items_sorted_by_z()
    print(f"[OK] 按层级排序后的元素顺序:")
    for item in sorted_items:
        print(f"  - {item.id} (z={item.z_index})")

    # 7. 测试资源预加载（虽然没有实际图片，但验证逻辑）
    print(f"\n[测试 7] 资源预加载...")
    loaded_count = loader.preload_scene_resources(scene_config)
    print(f"  预加载成功: {loaded_count} 个资源")
    print(f"  缓存大小: {loader.resource_cache.size()}")

    if loaded_count == 0:
        print(f"  ⚠ 注意：没有成功加载任何资源")
        print(f"  这是正常的，因为示例配置中的图片文件还不存在")
        print(f"  请在 scenes/{test_scene_name}/ 目录下添加实际的图片文件")

    # 8. 测试配置验证
    print(f"\n[测试 8] 配置验证...")
    # 重新读取 JSON 并验证
    import json
    config_file = loader.scenes_dir / test_scene_name / "config.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)

    is_valid = loader.validate_config(config_dict)
    print(f"[OK] 配置验证: {'通过' if is_valid else '失败'}")

    print("\n" + "="*80)
    print("测试完成")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        test_scene_loader()
    except Exception as e:
        logging.exception("测试过程中发生错误")
        sys.exit(1)
