# GaiYa 自我追踪过滤功能说明

**日期**: 2025-12-01
**版本**: GaiYa v1.6
**构建时间**: 约 16:40

---

## 问题背景

在行为识别功能测试中,发现GaiYa应用自身的exe(如`GaiYa-v1.6.exe`, `main.exe`)也被记录到活动统计中,并显示为"未分类(UNKNOWN)"。这会污染用户的真实使用统计数据。

### 测试数据示例

```
Top 5 apps:
  #1 GaiYa-v1.6.exe (UNKNOWN): 105s (1min)  ← 不应该被统计
  #2 Cursor.exe (PRODUCTIVE): 94s (1min)
  #3 Weixin.exe (LEISURE): 15s (0min)
  #4 chrome.exe (NEUTRAL): 10s (0min)
  #5 explorer.exe (NEUTRAL): 5s (0min)
```

---

## 解决方案

### 1. 数据库结构支持

`app_categories` 表已有 `is_ignored` 字段用于标记忽略的应用:

```sql
CREATE TABLE app_categories (
    process_name TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    is_ignored INTEGER DEFAULT 0  ← 1=忽略, 0=不忽略
)
```

### 2. 默认配置更新

在 `gaiya/data/db_manager.py` 的初始化逻辑中,为GaiYa自身的进程添加忽略规则:

**修改位置**: Lines 86-129

**新增内容**:
```python
defaults = [
    # ... 其他应用配置 ...

    # GaiYa app itself (ignore to avoid self-tracking)
    ("GaiYa-v1.6.exe", "NEUTRAL", True),  ← is_ignored=True
    ("GaiYa.exe", "NEUTRAL", True),
    ("main.exe", "NEUTRAL", True)  # For development builds
]

# 更新SQL插入语句以支持3个字段
cursor.executemany(
    'INSERT INTO app_categories (process_name, category, is_ignored) VALUES (?, ?, ?)',
    defaults
)
```

### 3. 保存逻辑优化

在 `save_activity_session()` 方法中,检查应用是否被忽略,若是则跳过保存:

**修改位置**: Lines 312-333

**核心逻辑**:
```python
def save_activity_session(self, process_name, window_title, start_time, end_time, duration_seconds):
    """Save an aggregated activity session."""
    # Check if app is ignored
    conn = self._get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_ignored FROM app_categories WHERE process_name = ?', (process_name,))
    row = cursor.fetchone()

    # Skip saving if app is ignored
    if row and row[0] == 1:  ← 如果被忽略,直接返回
        conn.close()
        return

    # ... 正常保存逻辑 ...
```

### 4. 统计查询优化

在 `get_today_activity_stats()` 方法中,使用JOIN过滤被忽略的应用:

**修改位置**: Lines 403-462

**核心逻辑**:
```python
# 分类统计 - 排除忽略的应用
cursor.execute('''
    SELECT a.category, sum(a.duration_seconds)
    FROM activity_sessions a
    LEFT JOIN app_categories c ON a.process_name = c.process_name
    WHERE a.start_time >= ?
    AND (c.is_ignored IS NULL OR c.is_ignored = 0)  ← 关键过滤条件
    GROUP BY a.category
''', (start_of_day,))

# Top应用排行 - 同样排除忽略的应用
cursor.execute('''
    SELECT a.process_name, a.category, sum(a.duration_seconds) as total_secs
    FROM activity_sessions a
    LEFT JOIN app_categories c ON a.process_name = c.process_name
    WHERE a.start_time >= ?
    AND (c.is_ignored IS NULL OR c.is_ignored = 0)  ← 关键过滤条件
    GROUP BY a.process_name
    ORDER BY total_secs DESC
    LIMIT 10
''', (start_of_day,))
```

---

## 现有用户更新

为现有用户提供了更新脚本 `update_app_categories.py`,新增对GaiYa自身的忽略配置:

**修改位置**: Lines 21-38

```python
new_categories = [
    # ... 其他更新 ...

    # Ignore GaiYa itself
    ("GaiYa-v1.6.exe", "NEUTRAL", True),
    ("GaiYa.exe", "NEUTRAL", True),
    ("main.exe", "NEUTRAL", True),
]
```

**运行方法**:
```bash
python update_app_categories.py
```

---

## 技术细节

### 双重过滤机制

1. **写入时过滤** (save_activity_session)
   - 优点: 不会产生垃圾数据,节省存储空间
   - 缺点: 一旦写入就无法恢复

2. **查询时过滤** (get_today_activity_stats)
   - 优点: 即使历史数据中有记录,也不会显示
   - 缺点: 数据库中仍保留记录

**当前实现**: 同时使用两种机制
- 新会话直接不写入 (save时检查)
- 历史遗留数据通过JOIN过滤 (query时排除)

### is_ignored 的设计意图

`is_ignored` 字段不仅用于GaiYa自身,还可以用于:
- 系统进程 (如 dwm.exe, svchost.exe)
- 开发工具的后台进程
- 用户主动标记为"不统计"的应用

未来可以在UI界面中提供"忽略此应用"的按钮,让用户自定义。

---

## 测试验证

### 测试步骤

1. 删除旧数据库 (可选):
   ```
   删除 C:\Users\<用户名>\AppData\Local\GaiYa\user_data.db
   ```

2. 启动新版GaiYa:
   ```
   dist\GaiYa-v1.6.exe
   ```

3. 正常使用5-10分钟 (切换不同应用)

4. 打开"今日时间回放",检查:
   - ✅ "今日用机统计" 中没有 GaiYa.exe
   - ✅ "Top应用排行" 中没有 GaiYa.exe
   - ✅ 其他应用正常统计

### 预期结果

```
Top 5 apps:
  #1 Cursor.exe (PRODUCTIVE): 94s
  #2 Weixin.exe (LEISURE): 15s
  #3 chrome.exe (NEUTRAL): 10s
  #4 explorer.exe (NEUTRAL): 5s

(GaiYa.exe 不再出现在列表中)
```

---

## 已修改文件

1. **gaiya/data/db_manager.py**
   - Lines 86-129: 添加GaiYa自身到默认忽略配置
   - Lines 312-333: save_activity_session 写入时检查忽略
   - Lines 403-462: get_today_activity_stats 查询时过滤忽略

2. **update_app_categories.py**
   - Lines 21-38: 为现有用户添加GaiYa忽略规则

---

## 应用分类总览 (v1.6)

| 分类 | 数量 | 说明 |
|------|------|------|
| PRODUCTIVE | 11个 | 开发工具、办公软件、设计工具 |
| LEISURE | 10个 | 社交、娱乐、音乐、游戏 |
| NEUTRAL | 5个 | 浏览器、文件管理器、任务管理器 |
| **IGNORED** | **3个** | **GaiYa自身进程(不统计)** |
| **总计** | **29个** | 配置完整的应用 |

---

## 打包信息

**版本**: `dist/GaiYa-v1.6.exe`
**构建时间**: 2025-12-01 16:40
**文件大小**: 约 82MB

**主要变更**:
1. ✅ 行为识别默认开启
2. ✅ 扩展应用分类 (12→29个)
3. ✅ 修正微信进程名 (Weixin.exe)
4. ✅ 浏览器分类改为NEUTRAL
5. ✅ **新增: GaiYa自身进程过滤**
6. ✅ 暂时注释火焰标记功能
7. ✅ 时间回放界面布局优化

---

## 相关文档

- [行为识别问题修复说明.md](行为识别问题修复说明.md) - 应用分类配置问题
- [PYINSTALLER_DEVELOPMENT_METHODOLOGY.md](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md) - 打包开发方法论
- [README.md](README.md) - 项目总览

---

**功能完成** ✅
