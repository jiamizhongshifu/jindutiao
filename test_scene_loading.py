"""测试场景加载功能"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from gaiya.scene.scene_manager import SceneManager

print("=" * 60)
print("测试场景加载功能")
print("=" * 60)

# 创建 SceneManager
manager = SceneManager()

print(f"\n场景目录: {manager.scenes_dir}")
print(f"场景目录是否存在: {manager.scenes_dir.exists()}")

if manager.scenes_dir.exists():
    print(f"\n场景目录内容:")
    for item in manager.scenes_dir.iterdir():
        print(f"  - {item.name} ({'目录' if item.is_dir() else '文件'})")

print(f"\n可用场景列表: {manager.get_scene_list()}")
print(f"\n场景详情:")
for scene_name in manager.get_scene_list():
    metadata = manager.get_scene_metadata(scene_name)
    if metadata:
        print(f"\n场景: {scene_name}")
        print(f"  显示名称: {metadata['name']}")
        print(f"  描述: {metadata.get('description', '无')}")
        print(f"  版本: {metadata['version']}")
        print(f"  作者: {metadata.get('author', '未知')}")
        print(f"  目录: {metadata['directory']}")

print("\n" + "=" * 60)
