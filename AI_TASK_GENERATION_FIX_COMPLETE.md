# AI任务生成修复说明 (完整版)

## 修复时间线

- **2025-12-12 17:27**: 修复1 - AI prompt优化 + 429错误处理 (commit `7c529c1`)
- **2025-12-12 18:31**: 修复2 - UI层错误提示 (commit `155a9cc`)

---

## 问题背景

用户报告了两个AI任务生成相关问题:
1. AI生成的任务时间顺序混乱(睡眠任务在进度条开头)
2. 429速率限制错误未被正确处理(无用户提示)

---

## 问题1: 任务时间顺序混乱

### 问题表现

```
日志证据:
任务已保存到文件: 11个任务
第一个任务: 充足睡眠, 开始: 00:00
最后一个任务: 充足睡眠, 结束: 24:00
```

用户期望:
- 进度条从"起床"开始(左侧)
- 睡眠任务在进度条末尾(右侧)

实际情况:
- AI按照时间(00:00)排序,睡眠任务在第一位
- 进度条从"睡眠"开始,体验不佳

### 根本原因

`api/plan-tasks.py` 的 AI prompt 中没有明确指定任务排序规则,AI模型默认按照24小时制时间顺序(00:00开始)排列任务。

### 解决方案

**修改位置**: `api/plan-tasks.py:100-114`
**Commit**: `7c529c1`

```python
# 新增第6条规则
6. **重要**: 任务排序规则 - 按照用户实际执行顺序排列:
   - 如果有睡眠任务(如00:00-07:00),应该放在数组最后一位
   - 早上的活动(如起床、早餐)应该放在数组最前面
   - 任务顺序应该反映用户一天的实际流程: 起床 -> 工作/学习 -> 休息 -> 睡眠

示例输出(注意睡眠任务在最后):
{"tasks": [
  {"start": "07:00", "end": "08:00", "task": "起床早餐", "category": "break"},
  {"start": "08:00", "end": "12:00", "task": "上午工作", "category": "work"},
  {"start": "12:00", "end": "13:00", "task": "午休", "category": "break"},
  {"start": "23:00", "end": "07:00", "task": "睡眠", "category": "break"}
]}
```

### 预期效果

- ✅ "休息日"场景: 起床(09:00) → 活动 → 睡眠(23:00) [睡眠在最后]
- ✅ "工作日"场景: 起床(07:00) → 工作 → 睡眠(23:00) [睡眠在最后]
- ✅ "学习日"场景: 起床(07:00) → 学习 → 睡眠(23:00) [睡眠在最后]

---

## 问题2: 429速率限制错误处理不当

### 问题表现

```
日志证据:
[AI API] 响应状态码: 429
[AI API] 请求失败: Daily AI quota exceeded. Please try again tomorrow.
[AI Client] 错误: 任务规划失败: Daily AI quota exceeded. Please try again tomorrow.
[AI Client] parent_widget为None,无法显示错误对话框
[改进版AI生成] 关闭进度对话框(成功)
```

用户体验:
- ❌ 点击"AI生成任务"后无任何反馈
- ❌ 进度对话框静默关闭,用户不知道发生了什么

### 根本原因(三层问题)

#### 原因1: API层未处理429

`ai_client.py:82-87` 只处理 `403` 状态码,未处理 `429`

```python
# 旧代码
if response.status_code == 403:
    # 配额用尽
    ...
# ❌ 429走到else分支,被当作普通错误
```

#### 原因2: 错误日志不完整

`ai_client.py:347-350` 在 `parent_widget=None` 时静默返回

```python
# 旧代码
def _show_quota_exceeded_dialog(self, data: Dict, parent_widget):
    if parent_widget is None:
        return  # ❌ 静默失败,无日志
```

#### 原因3: UI层假设错误

`config_gui.py:8965-8967` 的else分支假设ai_client已显示对话框

```python
# 旧代码
else:
    # result为None表示已经在ai_client中显示了错误对话框
    pass  # ❌ 实际上ai_client因parent_widget=None无法显示!
```

### 解决方案(三层修复)

#### 修复1: API层处理429状态码

**修改位置**: `ai_client.py:82-87`
**Commit**: `7c529c1`

```python
# 处理配额/速率限制错误
if response.status_code in [403, 429]:  # ✅ 支持两种状态码
    data = response.json()
    logging.warning(f"[AI API] 配额/速率限制: {data}")
    self._show_quota_exceeded_dialog(data, parent_widget)
    return None
```

#### 修复2: 增强错误日志

**修改位置**: `ai_client.py:347-357`
**Commit**: `7c529c1`

```python
def _show_quota_exceeded_dialog(self, data: Dict, parent_widget):
    """显示配额用尽对话框"""
    import logging

    # ✅ 始终记录错误到日志
    error_msg = data.get('error', '配额已用尽')
    logging.error(f"[AI Client] 配额/速率限制: {error_msg}")

    if parent_widget is None:
        logging.warning("[AI Client] parent_widget为None,无法显示配额对话框")
        return
    # ... 显示对话框代码
```

#### 修复3: UI层增加错误提示

**修改位置**: `config_gui.py:8965-8983`
**Commit**: `155a9cc` (✅ 新增修复)

```python
else:
    # ✅ P1-1.6.4: 处理失败情况(配额用尽/速率限制/其他错误)
    error_msg = "AI任务生成失败"

    if result and isinstance(result, dict):
        error_msg = result.get('error', error_msg)

    QMessageBox.warning(
        self,
        "生成失败",
        f"{error_msg}\n\n"
        "常见原因:\n"
        "• 今日AI配额已用尽\n"
        "• 网络连接问题\n"
        "• 服务暂时不可用\n\n"
        "请稍后再试或联系客服。"
    )
```

### 预期效果

- ✅ 429错误被正确识别(API层)
- ✅ 日志清晰记录: `"Daily AI quota exceeded"`(日志层)
- ✅ **用户看到友好的错误对话框**(UI层)
- ✅ 即使无法显示对话框,日志也会记录警告

---

## 测试验证

### 测试场景1: 任务顺序验证

**步骤**:
1. 部署到Vercel: `git push origin main`
2. 打开GaiYa应用
3. 点击"AI生成任务"
4. 选择"休息日"场景
5. 检查生成的任务列表

**预期结果**:
```
✓ 第一个任务: "自然醒+早午餐" (09:00)
✓ 中间任务: 活动/娱乐/休息
✓ 最后任务: "充足睡眠" (23:00-09:00)
```

### 测试场景2: 速率限制处理

**步骤**:
1. 快速连续触发AI生成(超过20次)
2. 观察日志输出
3. 检查用户界面反馈

**预期结果**:
```
日志:
[AI API] 响应状态码: 429
[AI Client] 配额/速率限制: Daily AI quota exceeded. Please try again tomorrow.
[AI Client] parent_widget为None,无法显示配额对话框

UI:
显示对话框标题: "生成失败"
显示内容: "AI任务生成失败

常见原因:
• 今日AI配额已用尽
• 网络连接问题
• 服务暂时不可用

请稍后再试或联系客服。"
```

---

## 部署说明

### 修复生效时机

| 修复内容 | 文件 | 生效方式 | 生效时机 |
|---------|------|---------|---------|
| 任务顺序优化 | `api/plan-tasks.py` | Vercel部署 | 推送后1-2分钟 |
| 429错误处理 | `ai_client.py` | 本地打包 | 下次打包exe后 |
| UI错误提示 | `config_gui.py` | 本地打包 | 下次打包exe后 |

### 部署步骤

```bash
# 1. 查看提交
git log --oneline -2
# 输出:
# 155a9cc fix(ai): 修复AI生成失败时无用户提示的问题
# 7c529c1 fix(ai): 修复AI任务生成的两个关键问题

# 2. 推送到远程(触发Vercel自动部署)
git push origin main

# 3. 验证Vercel部署状态
# 访问: https://vercel.com/jindutiao
# 等待部署完成(约1-2分钟)

# 4. 本地打包新版本exe
build-fast.bat  # 或 build-clean.bat

# 5. 测试新版本exe
cd dist
GaiYa-v1.6.exe
```

### API测试(可选)

```bash
# 测试任务顺序修复
curl -X POST https://api.gaiyatime.com/api/plan-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input": "我需要一个休息日任务计划。包括: 9:00自然醒, 23:00睡眠",
    "user_tier": "pro"
  }' | jq '.tasks[] | {task: .task, start: .start}'

# 预期输出(睡眠在最后):
# {"task": "自然醒+早午餐", "start": "09:00"}
# ...
# {"task": "睡眠", "start": "23:00"}
```

---

## 回滚方案

如果发现问题,可以快速回滚:

```bash
# 回滚UI层修复
git revert 155a9cc
git push origin main

# 回滚API层修复
git revert 7c529c1
git push origin main

# 或回滚全部
git revert HEAD~2..HEAD
git push origin main
```

---

## 相关文件

- `api/plan-tasks.py` - AI任务生成API(Vercel Function)
- `ai_client.py` - AI客户端(本地应用)
- `config_gui.py` - 配置管理界面(本地应用)
- `gaiya/data/ai_scene_presets.json` - 场景预设配置

---

## 后续优化建议

1. **任务排序优化**
   - 考虑增加"跨天任务"的智能识别
   - 支持用户自定义排序规则

2. **错误提示优化**
   - 在UI层增加全局Toast提示
   - 配额用尽时显示"剩余次数"

3. **测试覆盖**
   - 添加AI响应格式的单元测试
   - 添加速率限制的集成测试

4. **Parent Widget问题**
   - 调查为什么 `parent_widget` 为 `None`
   - 考虑在异步工作线程中传递正确的parent

---

**修复时间**: 2025-12-12
**受影响版本**: v1.6.8及更早版本
**修复版本**: v1.6.9 (待发布)
**提交记录**:
- `7c529c1` - API层修复
- `155a9cc` - UI层修复
