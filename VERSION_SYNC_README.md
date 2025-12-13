# 版本信息自动同步系统

## 问题背景

之前 `version_info.txt` 是手工维护的,导致:
- 更新 `version.py` 后忘记同步 `version_info.txt`
- 打包出的 exe 文件属性显示旧版本号
- 版本信息不一致,影响用户体验

## 解决方案

创建了自动化同步脚本 `update_version_info.py`,在每次打包前自动从 `version.py` 读取版本号并更新 `version_info.txt`。

## 文件说明

### 1. `update_version_info.py` - 版本同步脚本

**功能**:
- 从 `version.py` 读取当前版本号
- 自动更新 `version_info.txt` 中的所有版本信息
- 支持 Windows 命令行编码

**更新的字段**:
- `filevers` - 文件版本号元组 (例: `(1, 6, 8, 0)`)
- `prodvers` - 产品版本号元组
- `FileVersion` - 文件版本字符串 (例: `1.6.8.0`)
- `ProductVersion` - 产品版本字符串
- `OriginalFilename` - exe 文件名 (例: `GaiYa-v1.6.exe`)
- `InternalName` - 内部名称 (例: `GaiYa`)
- `ProductName` - 产品名称

**手动运行**:
```bash
python update_version_info.py
```

### 2. `build-fast.bat` - 快速打包脚本 (已集成)

在打包前自动运行版本同步:
```bat
REM 1. 同步版本信息
echo 🔄 同步版本信息...
python update_version_info.py
```

### 3. `build-clean.bat` - 完全重建脚本 (已集成)

同样在清理前自动运行版本同步。

## 工作流程

### 原来的流程 (手动维护,容易出错)
```
1. 修改 version.py 中的版本号
2. 手动打开 version_info.txt
3. 手动查找并修改 6 处版本相关字段
4. 运行 build-fast.bat 或 build-clean.bat
5. 经常忘记步骤 2-3,导致版本不同步 ❌
```

### 现在的流程 (全自动,不会出错)
```
1. 修改 version.py 中的版本号 ✅
2. 运行 build-fast.bat 或 build-clean.bat ✅
3. 脚本自动同步 version_info.txt ✅
4. 版本信息始终保持一致 ✅
```

## 使用示例

### 发布新版本 1.6.9

**步骤 1**: 修改 `version.py`
```python
__version__ = "1.6.9"
VERSION_MAJOR = 1
VERSION_MINOR = 6
VERSION_PATCH = 9
```

**步骤 2**: 运行打包脚本
```bash
build-fast.bat
# 或
build-clean.bat
```

**结果**:
- `version_info.txt` 自动更新为 `1.6.9.0`
- 打包出的 exe 文件属性显示正确版本号
- 无需手动维护任何文件

## 验证版本信息

打包完成后,可以验证版本信息是否正确:

**方法 1**: 查看 exe 属性
- 右键 `dist\GaiYa-v1.6.exe`
- 选择 "属性" → "详细信息"
- 检查 "文件版本" 和 "产品版本"

**方法 2**: 运行脚本查看
```bash
python update_version_info.py
```

## 技术细节

### 正则表达式替换

脚本使用正则表达式精确匹配和替换版本信息:

```python
# 替换 filevers=(1, 6, 8, 0) 格式
content = re.sub(
    r'filevers=\([0-9]+,\s*[0-9]+,\s*[0-9]+,\s*[0-9]+\)',
    f'filevers={version_tuple}',
    content
)

# 替换 StringStruct(u'FileVersion', u'1.6.8.0') 格式
content = re.sub(
    r"StringStruct\(u'FileVersion',\s*u'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'\)",
    f"StringStruct(u'FileVersion', u'{version_string}')",
    content
)
```

### Windows 编码修复

为了在 Windows 命令行正确显示 emoji 和中文:

```python
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

## 常见问题

### Q: 如果手动运行脚本失败怎么办?

**A**: 检查错误信息:
- 确保 `version.py` 存在且格式正确
- 确保 `version_info.txt` 存在
- 确保 Python 版本 >= 3.6

### Q: 可以手动修改 version_info.txt 吗?

**A**: 可以,但不推荐:
- 下次打包时会被自动覆盖
- 建议只修改 `version.py`,让脚本自动同步

### Q: 如何临时跳过版本同步?

**A**: 注释掉构建脚本中的同步步骤:
```bat
REM python update_version_info.py
```

但不推荐这样做,可能导致版本不一致。

## 维护指南

### 修改版本信息字段

如果需要修改其他版本信息字段 (例如公司名称、版权信息),请:

1. **编辑 `version_info.txt` 模板**:
   - 手动修改相应字段
   - 这些字段不会被脚本覆盖

2. **如果需要自动化**:
   - 在 `version.py` 中添加对应变量
   - 在 `update_version_info.py` 中添加替换规则

### 扩展脚本功能

可以添加更多自动化功能:

```python
# 示例: 自动更新构建日期
import datetime
build_date = datetime.datetime.now().strftime("%Y-%m-%d")

content = re.sub(
    r"StringStruct\(u'BuildDate',\s*u'[^']+'\)",
    f"StringStruct(u'BuildDate', u'{build_date}')",
    content
)
```

## 总结

通过这个自动化系统:
- ✅ **版本信息始终同步** - 单一事实来源 (version.py)
- ✅ **无需手动维护** - 打包时自动更新
- ✅ **减少人为错误** - 避免遗漏或输入错误
- ✅ **提升开发效率** - 专注于代码,而非繁琐的版本维护

---

**最后更新**: 2025-12-13
**创建者**: Claude Code
**维护者**: GaiYa 团队
