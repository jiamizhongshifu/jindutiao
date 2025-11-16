#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试场景资源加载"""

import sys
sys.path.insert(0, '.')

from gaiya.scene import SceneLoader

def test_scene_loading():
    """测试场景加载"""
    print("="*50)
    print(" Scene Resource Loading Test")
    print("="*50)

    loader = SceneLoader()

    # 1. 获取可用场景列表
    scenes = loader.get_available_scenes()
    print(f"\n1. Available scenes: {scenes}")

    if 'default' not in scenes:
        print("   [ERROR] Default scene not found!")
        return False

    # 2. 加载默认场景
    print("\n2. Loading default scene...")
    try:
        scene = loader.load_scene('default')
        print(f"   [OK] Scene loaded successfully")
        print(f"   - Name: {scene.name}")
        print(f"   - Description: {scene.description}")
        print(f"   - Author: {scene.author}")
        print(f"   - Version: {scene.version}")
        print(f"   - Canvas: {scene.canvas.width}x{scene.canvas.height}")
    except Exception as e:
        print(f"   [ERROR] Failed to load scene: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. 检查道路层
    print("\n3. Road layer:")
    if scene.road_layer:
        print(f"   - Image: {scene.road_layer.image}")
        print(f"   - Z-index: {scene.road_layer.z_index}")
        print(f"   - Scale: {scene.road_layer.scale}")
        print(f"   - Tile type: {scene.road_layer.type}")
    else:
        print("   [INFO] No road layer")

    # 4. 检查场景元素
    items = scene.scene_layer.items
    print(f"\n4. Scene items: {len(items)} items")
    for i, item in enumerate(items, 1):
        print(f"   {i}. {item.id}:")
        print(f"      - Image: {item.image}")
        print(f"      - Position: x={item.position.x_percent}%, y={item.position.y_pixel}px")
        print(f"      - Scale: {item.scale}")
        print(f"      - Z-index: {item.z_index}")
        print(f"      - Events: {len(item.events)}")

    # 5. 预加载资源
    print(f"\n5. Preloading resources...")
    try:
        count = loader.preload_scene_resources(scene)
        print(f"   [OK] Successfully preloaded {count} resources")
    except Exception as e:
        print(f"   [ERROR] Failed to preload resources: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*50)
    print(" [SUCCESS] All tests passed!")
    print("="*50)
    return True

if __name__ == '__main__':
    success = test_scene_loading()
    sys.exit(0 if success else 1)
