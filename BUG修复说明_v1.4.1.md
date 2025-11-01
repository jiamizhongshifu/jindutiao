# PyDayBar v1.4.1 问题修复说明

**修复日期**: 2025-11-01
**版本**: v1.4.1

---

## 🐛 修复的问题

### 问题1: 保存配置时出现属性错误

**错误信息:**
```
'ConfigManager' object has no attribute 'notify_before_start_checks'
```

**问题描述:**
- 在某些情况下，保存配置时会尝试访问 `notify_before_start_checks` 属性
- 如果通知设置标签页未正确初始化，该属性可能不存在
- 导致保存失败并显示错误对话框

**根本原因:**
- `save_all()` 方法中直接访问 `self.notify_before_start_checks`，未检查属性是否存在
- 同样的问题也存在于其他通知相关的 UI 控件属性

**修复方案:**
- 在 `save_all()` 方法中添加 `hasattr()` 检查
- 如果属性不存在，使用配置中的默认值
- 对所有通知相关的 UI 控件属性都添加了安全检查

**修复代码位置:**
- `config_gui.py:2303-2354` - `save_all()` 方法

**修复效果:**
- ✅ 保存配置时不再出现属性错误
- ✅ 即使通知标签页未初始化也能正常保存
- ✅ 使用配置中的默认值作为后备方案

---

### 问题2: 打包过程会删除用户数据文件

**问题描述:**
- 使用 `build.bat` 或 `build_onefile.bat` 打包时，会删除 `dist` 目录
- 如果用户的数据文件（`config.json`, `tasks.json`, `statistics.json` 等）在 `dist` 目录中，会被意外删除
- 用户创建的自定义任务模板也会丢失

**根本原因:**
- 打包脚本在清理 `dist` 目录前没有警告提示
- `build.bat` 中使用了 `--add-data "config.json;."` 和 `--add-data "tasks.json;."`，这会将用户数据文件打包进exe（不应该这样做）

**修复方案:**
1. **移除用户数据文件的打包配置**
   - 从 `build.bat` 中移除了 `--add-data "config.json;."` 和 `--add-data "tasks.json;."`
   - 用户数据文件不应该被打包进exe，应该由程序运行时创建

2. **添加警告提示**
   - 在 `build_onefile.bat` 中添加了明确的警告信息
   - 提供3秒延迟，让用户有机会取消操作
   - 明确说明哪些文件会被删除

3. **使用 spec 文件打包**
   - 更新 `build.bat` 使用 `PyDayBar.spec` 文件
   - 确保资源文件正确打包，但不包含用户数据

**修复代码位置:**
- `build.bat:24-32` - 添加警告并使用 spec 文件
- `build_onefile.bat:18-29` - 添加警告和延迟

**修复效果:**
- ✅ 打包前会明确提示用户数据文件会被删除
- ✅ 用户数据文件不会被错误地打包进exe
- ✅ 用户有机会取消打包操作

---

## 📝 使用建议

### 打包前的重要注意事项

1. **备份用户数据**
   - 打包前请备份以下文件：
     - `config.json` - 配置文件
     - `tasks.json` - 任务数据
     - `statistics.json` - 统计数据
     - `themes.json` - 主题配置
     - 任何自定义的任务模板文件

2. **数据文件位置**
   - 用户数据文件应该放在 exe 所在的目录
   - **不要**将数据文件放在项目根目录的 `dist` 文件夹中
   - 打包完成后，将 exe 和数据文件复制到使用目录

3. **打包流程**
   ```bash
   # 1. 备份用户数据（如果使用 dist 目录存储数据）
   # 2. 运行打包脚本
   build.bat  # 或 build_onefile.bat
   # 3. 打包完成后，将 exe 和数据文件复制到使用目录
   ```

---

## 🔧 技术细节

### 属性安全检查模式

修复后的代码使用以下模式进行安全检查：

```python
# 模式1: 使用 hasattr 检查 + getattr 获取
if hasattr(self, 'notify_before_start_checks'):
    before_start_minutes = [
        minutes for minutes, checkbox in self.notify_before_start_checks.items()
        if checkbox.isChecked()
    ]
else:
    # 使用配置中的默认值
    before_start_minutes = self.config.get('notification', {}).get('before_start_minutes', [10, 5])

# 模式2: 三元表达式检查存在性
"enabled": (getattr(self, 'notify_enabled_check', None) and self.notify_enabled_check.isChecked()) 
           if hasattr(self, 'notify_enabled_check') 
           else self.config.get('notification', {}).get('enabled', True)
```

### 打包脚本改进

**build.bat 改进:**
- 移除了 `--add-data "config.json;."` 和 `--add-data "tasks.json;."`
- 使用 `PyDayBar.spec` 文件进行打包
- 添加了警告提示

**build_onefile.bat 改进:**
- 添加了明确的警告信息
- 添加了3秒延迟，允许用户取消
- 说明了哪些文件会被删除

---

## ✅ 测试验证

### 测试1: 保存配置不打开通知标签页
- **步骤**: 打开配置管理器，不切换到"通知设置"标签页，直接保存
- **预期**: ✅ 保存成功，无错误提示

### 测试2: 保存配置打开通知标签页
- **步骤**: 打开配置管理器，切换到"通知设置"标签页，修改设置后保存
- **预期**: ✅ 保存成功，通知设置正确保存

### 测试3: 打包前警告提示
- **步骤**: 运行 `build_onefile.bat`
- **预期**: ✅ 显示警告信息，等待3秒后继续

### 测试4: 打包不包含用户数据
- **步骤**: 打包后检查exe中是否包含用户数据文件
- **预期**: ✅ exe中不包含用户数据文件（config.json, tasks.json等）

---

## 📋 文件变更清单

### 修改的文件
- `config_gui.py` - 修复属性访问错误
- `build.bat` - 移除用户数据打包，添加警告
- `build_onefile.bat` - 添加警告和延迟

### 修改的函数
1. `config_gui.py::save_all()` - 添加属性安全检查

---

## 🎯 后续建议

1. **数据文件管理**
   - 考虑添加数据文件备份功能
   - 提供配置文件导入/导出功能

2. **打包流程优化**
   - 考虑添加自动备份功能
   - 提供打包前检查清单

3. **错误处理增强**
   - 添加更详细的错误日志
   - 提供错误恢复机制

---

**版本**: v1.4.1
**修复日期**: 2025-11-01
**修复的问题**: 2个
**状态**: ✅ 已修复并测试

