# Scripts 目录说明

本目录包含PyDayBar项目的工具脚本，用于开发、调试和维护。

## 目录结构

```
scripts/
├── diagnostics/        # 诊断工具
│   ├── check_*.py      # 检查工具（动画、GIF、WebP等）
│   ├── diagnose_*.py   # 诊断工具（时间标记等）
│   ├── compare_*.py    # 性能对比工具
│   └── reset_quota.py  # 配额重置工具
├── generators/         # 资源生成工具
│   ├── create_*.py     # 创建资源（GIF等）
│   ├── convert_*.py    # 格式转换工具
│   ├── fix_*.py        # 修复工具（WebP时序等）
│   └── verify_*.py     # 验证工具
└── README.md           # 本文件
```

## 诊断工具（diagnostics/）

### 动画检查工具
- `check_animation.py` - 检查动画文件格式和属性
- `check_gif_size.py` - 检查GIF文件大小
- `check_webp_frames.py` - 检查WebP动画帧数
- `check_webp_delay.py` - 检查WebP帧延迟设置

### 性能诊断工具
- `compare_speed.py` - 对比不同动画格式的性能
- `diagnose_marker.py` - 诊断时间标记渲染问题

### 配额管理工具
- `reset_quota.py` - 重置Supabase配额数据（需要环境变量配置）

## 资源生成工具（generators/）

### GIF生成工具
- `create_proper_gif.py` - 创建符合规范的GIF动画
- `create_scaled_gif.py` - 创建指定尺寸的GIF

### 格式转换工具
- `convert_to_gif.py` - 将其他格式转换为GIF

### 修复工具
- `fix_webp_timing.py` - 修复WebP帧延迟问题

### 验证工具
- `verify_imageio_gif.py` - 验证imageio生成的GIF格式

## 使用方法

### 基本用法
```bash
# 运行诊断工具
python scripts/diagnostics/check_animation.py

# 运行生成工具
python scripts/generators/create_proper_gif.py
```

### 配额重置工具
```bash
# 需要配置Supabase环境变量
export SUPABASE_URL="your_url"
export SUPABASE_ANON_KEY="your_key"

# 运行重置脚本
python scripts/diagnostics/reset_quota.py
```

### 动画检查工具示例
```bash
# 检查WebP帧延迟
python scripts/diagnostics/check_webp_delay.py

# 输出示例：
# Frame 0: 150ms
# Frame 1: 150ms
# ...
```

## 开发规范

### 新增工具脚本

1. **选择正确的目录**
   - 诊断、检查类工具 → `diagnostics/`
   - 生成、转换类工具 → `generators/`

2. **命名规范**
   - 检查工具：`check_<target>.py`
   - 诊断工具：`diagnose_<issue>.py`
   - 生成工具：`create_<resource>.py` 或 `generate_<resource>.py`
   - 转换工具：`convert_<from>_to_<to>.py`
   - 修复工具：`fix_<issue>.py`

3. **脚本模板**
```python
"""
工具名称：<简短描述>
用途：<详细说明工具的目的和使用场景>
用法：python scripts/<category>/<script_name>.py [args]
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description='<工具描述>')
    parser.add_argument('--input', help='输入文件路径')
    parser.add_argument('--output', help='输出文件路径')
    args = parser.parse_args()

    # 工具逻辑
    print("工具执行完成")

if __name__ == '__main__':
    main()
```

4. **文档要求**
   - 每个脚本顶部添加docstring
   - 说明用途、参数、示例
   - 在本README中添加简要说明

## 维护指南

### 定期清理
- 删除过时的临时脚本
- 合并功能相似的工具
- 更新文档说明

### 版本管理
- 重要工具添加版本号注释
- 记录修改历史
- 保留向后兼容性

## 注意事项

⚠️ **重要提醒**：

1. **不要在主程序中依赖这些脚本**
   - 这些是开发辅助工具，不是核心功能
   - 主程序应该独立运行

2. **环境变量配置**
   - 部分工具需要环境变量（如配额重置）
   - 使用前请检查`.env`文件或环境变量配置

3. **数据安全**
   - 使用配额重置等工具前先备份数据
   - 了解工具的影响范围

4. **性能影响**
   - 部分工具可能消耗较多资源（如GIF生成）
   - 建议在空闲时运行

## 贡献

欢迎提交新的工具脚本！请确保：
- 遵循上述命名和目录规范
- 添加完整的文档说明
- 更新本README

## 参考资料

- [WebP动画优化记录](../docs/webp-animation-optimization.md)（待创建）
- [配额系统说明](../QUOTA_SYSTEM_README.md)
- [开发工具集最佳实践](../docs/dev-tools-best-practices.md)（待创建）
