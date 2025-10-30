# PyDayBar v1.3 Bug修复说明

**发布日期**: 2025-10-29
**版本**: v1.3

---

## 🐛 已修复的问题

### 问题1: 配置界面没有显示预设任务模板

**用户反馈**:
> PyDayBar-Config中没有看到预设的任务

**问题描述**:
- 虽然项目中提供了3个预设任务模板文件(24小时、工作日、学生作息)
- 但配置界面中没有提供加载这些模板的功能
- 用户需要手动复制文件或逐个添加任务,不够友好

**根本原因**:
- 配置界面(config_gui.py)只实现了编辑当前tasks.json的功能
- 缺少模板加载功能

**修复方案**:
1. 在"任务管理"标签页添加"预设模板"功能区
2. 添加3个快速加载按钮:
   - 📋 24小时完整作息
   - 📋 工作日作息
   - 📋 学生作息
3. 添加"清空所有任务"按钮,方便用户切换模板
4. 点击按钮后自动加载对应模板并刷新表格

**修复代码位置**:
- `config_gui.py:171-241` - 更新create_tasks_tab()方法
- `config_gui.py:362-416` - 新增clear_all_tasks()和load_template()方法

**修复效果**:
- 用户可以在配置界面直接点击按钮加载预设模板
- 加载前会显示确认对话框,说明将被替换的任务数量
- 加载后会提示用户点击"保存所有设置"按钮来应用更改
- 提供友好的错误提示(如模板文件不存在)

---

### 问题2: 点击任务栏导致进度条窗口消失

**用户反馈**:
> 打开程序后,屏幕底部展示了进度条,但是通过鼠标点击屏幕任意一个位置,会自动消失,无法再现,是否没有成功固定置顶展示。特别是点击屏幕底部的导航栏区域,进度条就会消失

**问题描述**:
- 进度条在点击屏幕其他区域时可以正常展示
- 但点击Windows任务栏时,进度条窗口会隐藏并无法恢复
- 与任务栏存在层级冲突

**根本原因**:
- 主窗口使用了`Qt.Tool`窗口标志
- `Qt.Tool`标志会让窗口表现为工具窗口,在失去焦点时可能被隐藏
- 特别是当用户点击任务栏时,系统会认为应该隐藏工具窗口

**技术分析**:
```python
# 旧代码(有问题)
flags = (
    Qt.FramelessWindowHint |      # 无边框
    Qt.WindowStaysOnTopHint |     # 始终置顶
    Qt.Tool |                     # ⚠️ 问题在这里!
    Qt.WindowTransparentForInput  # 点击穿透
)
```

**修复方案**:
1. 将`Qt.Tool`标志改为`Qt.SubWindow`
2. `Qt.SubWindow`同样不会在任务栏显示,但不会被自动隐藏
3. 添加窗口事件日志记录(showEvent, hideEvent, changeEvent)
4. 移除会导致失去焦点的`activateWindow()`调用

**修复代码**:
```python
# 新代码(已修复)
flags = (
    Qt.FramelessWindowHint |      # 无边框
    Qt.WindowStaysOnTopHint |     # 始终置顶
    Qt.SubWindow |                # ✅ 修复:使用SubWindow替代Tool
    Qt.WindowTransparentForInput  # 点击穿透
)
```

**修复代码位置**:
- `main.py:29-65` - 更新init_ui()方法,修改窗口标志
- `main.py:51-65` - 添加showEvent(), hideEvent(), changeEvent()事件处理

**修复效果**:
- 点击任务栏或其他应用时,进度条窗口保持可见
- 窗口始终置顶显示,不会被隐藏
- 日志中可以追踪窗口状态变化,便于后续调试
- 保持原有的点击穿透和透明效果

---

## 🔧 技术改进

### 1. 窗口事件日志

添加了详细的窗口事件记录:

```python
def showEvent(self, event):
    """窗口显示事件"""
    super().showEvent(event)
    self.logger.info("窗口显示事件触发")

def hideEvent(self, event):
    """窗口隐藏事件"""
    super().hideEvent(event)
    self.logger.warning("窗口隐藏事件触发! 这不应该发生")

def changeEvent(self, event):
    """窗口状态变化事件"""
    super().changeEvent(event)
    if event.type() == event.Type.WindowStateChange:
        self.logger.info(f"窗口状态变化: {self.windowState()}")
```

**作用**:
- 追踪窗口显示/隐藏事件
- 如果窗口意外隐藏,会在日志中留下警告
- 便于排查未来可能出现的窗口显示问题

### 2. 字符串编码优化

修改了包含中文引号的字符串,避免PyInstaller打包时的编码问题:

```python
# 旧代码(打包时报语法错误)
'需要点击"保存所有设置"'

# 新代码(使用中文方括号)
'需要点击【保存所有设置】'
```

### 3. Spec文件更新

更新PyDayBar.spec,明确包含config_gui模块:

```python
hiddenimports=['config_gui', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets']
```

---

## 📦 打包更新

### 重新打包的文件

1. **PyDayBar.exe** (47MB)
   - 修复时间: 2025-10-29 20:24
   - 包含主程序所有bug修复

2. **PyDayBar-Config.exe** (47MB)
   - 修复时间: 2025-10-29 20:26
   - 新增预设模板加载功能

### 打包命令

```bash
# 主程序
pyinstaller --clean --noconfirm PyDayBar.spec

# 配置工具
pyinstaller --clean --noconfirm --noconsole --onefile --name=PyDayBar-Config config_gui.py
```

---

## 🧪 测试验证

### 测试1: 预设模板加载

**测试步骤**:
1. 运行PyDayBar-Config.exe
2. 切换到"任务管理"标签页
3. 点击"24小时完整作息"按钮
4. 确认加载
5. 点击"保存所有设置"

**预期结果**: ✅
- 表格中显示14个任务
- 任务时间和颜色与模板文件一致
- 保存后主程序自动重载

### 测试2: 窗口置顶稳定性

**测试步骤**:
1. 运行PyDayBar.exe
2. 点击桌面其他位置
3. 点击任务栏上的其他应用
4. 点击任务栏空白处
5. 检查进度条是否保持可见

**预期结果**: ✅
- 进度条始终显示在屏幕底部
- 不会因点击而消失
- 日志中没有hideEvent警告

### 测试3: 日志记录

**测试步骤**:
1. 运行PyDayBar.exe
2. 查看pydaybar.log文件

**预期日志**:
```
2025-10-29 20:23:17,429 - INFO - PyDayBar 启动
2025-10-29 20:23:17,429 - INFO - 配置文件加载成功
2025-10-29 20:23:17,430 - INFO - 成功加载 4 个任务
2025-10-29 20:23:17,434 - INFO - 窗口显示事件触发
2025-10-29 20:23:17,459 - INFO - 窗口位置设置: x=0, y=1420, w=2560, h=20, position=bottom
2025-10-29 20:23:17,492 - INFO - 文件监视器已启动
```

**验证结果**: ✅
- 日志正常记录所有事件
- 没有hideEvent警告
- 窗口位置计算正确

---

## 📝 使用说明

### 如何使用预设模板

1. **启动配置工具**:
   - 双击`PyDayBar-Config.exe`
   - 或右键托盘图标 → ⚙️ 打开配置

2. **加载模板**:
   - 切换到"任务管理"标签页
   - 在"📋 预设模板"区域选择:
     - 24小时完整作息(14个任务)
     - 工作日作息(12个任务)
     - 学生作息(13个任务)

3. **自定义调整**:
   - 加载模板后可以修改任何任务
   - 双击单元格编辑时间、名称
   - 点击"选色"按钮修改颜色

4. **保存应用**:
   - 点击底部"保存所有设置"按钮
   - 如果主程序正在运行,会自动重载

### 模板文件位置

```
程序目录/
├── PyDayBar.exe
├── PyDayBar-Config.exe
├── tasks_template_24h.json         ← 24小时模板
├── tasks_template_workday.json     ← 工作日模板
├── tasks_template_student.json     ← 学生作息模板
└── tasks.json                      ← 当前使用的任务
```

---

## 🔄 版本对比

| 功能 | v1.2 | v1.3 |
|------|------|------|
| 配置界面加载模板 | ❌ | ✅ |
| 点击任务栏不消失 | ❌ | ✅ |
| 窗口事件日志 | ❌ | ✅ |
| 清空所有任务按钮 | ❌ | ✅ |

---

## 🎯 已知问题

目前版本没有已知的重大问题。

如果遇到其他问题,请查看`pydaybar.log`日志文件并报告。

---

## 📞 反馈方式

如果发现新的bug或有功能建议:
1. 查看运行日志:`pydaybar.log`
2. 记录操作步骤和现象
3. 提供日志相关内容

---

**版本**: v1.3
**更新日期**: 2025-10-29
**修复项目**: 2个重大bug
**新增功能**: 预设模板快速加载
