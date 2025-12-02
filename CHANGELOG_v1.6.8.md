# GaiYa v1.6.8 更新日志

**发布日期**: 2025-12-02

## 🐛 关键Bug修复

### 1. 修复任务回顾窗口点击"全部确认"后卡死问题

**问题描述**:
- 用户点击任务回顾窗口的"全部确认"按钮后，界面完全卡死无响应
- 控制台报错: `QObject: Cannot create children for a parent that is in a different thread`

**根本原因**:
- 任务推理系统在工作线程中直接创建和显示 Qt UI 窗口
- 违反了 Qt 的线程安全规则：UI 操作必须在主线程中进行

**解决方案**:
- 使用 Qt 信号/槽机制，将 UI 创建操作从工作线程转发到主线程
- 修改窗口为非模态显示，避免阻塞事件循环

**修改文件**:
- [main.py](main.py#L66) - 添加 `task_review_requested` 信号
- [main.py](main.py#L1375) - 连接信号到主线程槽函数
- [main.py](main.py#L1592) - 实现主线程窗口显示槽函数
- [gaiya/ui/task_review_window.py](gaiya/ui/task_review_window.py#L291) - 修改窗口标志

### 2. 修复统计报告手动推理按钮状态未恢复问题

**问题描述**:
- 点击"手动生成推理"按钮后，按钮一直显示"正在执行推理..."
- 推理完成后按钮状态无法恢复

**根本原因**:
- 使用 `QMetaObject.invokeMethod` 和 `Q_ARG` 从工作线程调用主线程方法可能失败
- 回调函数未被正确执行

**解决方案**:
- 添加 `inference_completed` 信号
- 工作线程完成后发射信号，主线程槽函数处理 UI 更新

**修改文件**:
- [statistics_gui.py](statistics_gui.py#L127) - 添加 `inference_completed` 信号
- [statistics_gui.py](statistics_gui.py#L147) - 连接信号到槽函数
- [statistics_gui.py](statistics_gui.py#L1130) - 发射信号替代 `QMetaObject.invokeMethod`

## 🔧 技术改进

### Qt 线程安全最佳实践

**改进前** (❌ 错误做法):
```python
# 在工作线程中直接创建 UI
def callback_from_worker_thread():
    window = QDialog()
    window.exec()  # 导致线程错误
```

**改进后** (✅ 正确做法):
```python
# 定义信号
class MainWindow(QWidget):
    ui_requested = Signal(str, list)

# 工作线程发射信号
def callback_from_worker_thread():
    self.ui_requested.emit(data)

# 主线程处理 UI
@Slot(str, list)
def show_ui_slot(self, data):
    window = QDialog()
    window.show()
```

### 信号/槽优势

- ✅ 自动线程调度 - Qt 会自动将信号调度到正确的线程
- ✅ 类型安全 - 编译期检查参数类型
- ✅ 代码简洁 - 比 `QMetaObject.invokeMethod` 更简单
- ✅ 解耦合 - 发送方和接收方独立

## 📊 测试验证

### 测试1: 任务回顾窗口

**测试步骤**:
1. 运行测试脚本创建测试数据: `python test_task_review_fix.py`
2. 启动主程序: `python main.py`
3. 点击托盘菜单 → "今日任务回顾"
4. 调整完成度滑块
5. 点击"全部确认"按钮

**验证结果**:
- ✅ 窗口正常显示
- ✅ 可以调整完成度滑块
- ✅ 点击"全部确认"后窗口正常关闭
- ✅ 不再出现卡死或线程错误
- ✅ 日志显示: `用户确认 3 个任务完成记录`

### 测试2: 统计报告手动推理

**测试步骤**:
1. 打开统计报告窗口
2. 点击 "🔄 手动生成推理" 按钮
3. 等待推理完成

**验证结果**:
- ✅ 按钮文字变为 "🔄 正在执行推理..."
- ✅ 推理完成后按钮恢复为 "🔄 手动生成推理"
- ✅ 如果有未确认任务，自动弹出回顾窗口
- ✅ 可以多次点击按钮，每次都正常工作

## 🚀 性能优化

- 无性能影响，信号/槽机制开销极小

## 📝 文档更新

- 新增 [任务确认崩溃修复报告_v2.md](任务确认崩溃修复报告_v2.md) - 详细技术分析
- 更新测试脚本 [test_task_review_fix.py](test_task_review_fix.py) - 创建测试数据
- 新增清理脚本 [clean_test_data.py](clean_test_data.py) - 清理测试数据

## ⚠️ 破坏性变化

无

## 🔄 升级指南

直接覆盖安装即可，无需额外操作。

## 🙏 致谢

感谢用户反馈这些关键问题！

---

**完整更新内容**: 2 个关键 Bug 修复
**修改文件数**: 3 个文件
**新增文件数**: 3 个文件（测试/清理脚本和文档）
**测试状态**: ✅ 已通过完整测试
