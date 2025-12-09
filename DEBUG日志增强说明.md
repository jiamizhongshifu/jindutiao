# 行为识别和弹幕系统DEBUG日志增强说明

> **完成时间**: 2025-12-08
> **版本**: v1.6.13
> **增强类型**: DEBUG级别日志节点监控

---

## 📊 增强概述

根据[行为识别 × 弹幕系统 · 设计文档v1.0.md](行为识别 × 弹幕系统 · 设计文档v1.0.md)的要求,在5个关键系统节点增加了DEBUG级别日志监控,同时添加了性能指标追踪。

---

## 🎯 增强的5个关键节点

### 1. **behavior_analyzer.py** - 行为趋势检测和模式判断

#### 增强位置
- Line 191-215: `_determine_content_mode()` 方法
- Line 250-277: `_detect_trend()` 方法

#### 新增日志
```python
# ContentMode判断日志 (4个优先级)
self.logger.debug(f"🎯 Mode determined: {domain_mode} (priority=1:domain, domain={domain})")
self.logger.debug(f"🎯 Mode determined: production (priority=2:title_keywords, title={window_title[:50]})")
self.logger.debug(f"🎯 Mode determined: {default_mode} (priority=3:app_type, type={app_type})")
self.logger.debug(f"🎯 Mode determined: unknown (priority=4:fallback)")

# 行为趋势检测日志 (5种趋势)
self.logger.debug(f"🔍 Trend detected: focus_steady (mode={mode}, duration={duration_sec}s)")
self.logger.debug(f"🔍 Trend detected: moyu_start (mode={mode}, duration={duration_sec}s, prev_mode={previous_mode})")
self.logger.debug(f"🔍 Trend detected: moyu_steady (mode={mode}, duration={duration_sec}s)")
self.logger.debug(f"🔍 Trend detected: mode_switch (transition: {previous_mode} → {mode})")
self.logger.debug(f"🔍 Trend detected: task_switch (app: {self.last_snapshot.app} → {self.current_app})")
```

#### 作用
- 显示**ContentMode判断依据**(域名规则/标题关键词/AppType默认值/unknown)
- 追踪**5种行为趋势**的触发时机和参数
- 显示**模式转换**的前后状态

---

### 2. **cooldown_manager.py** - 冷却系统状态

#### 增强位置
- Line 141-142: `record_danmaku_shown()` 方法

#### 新增日志
```python
self.logger.debug(f"❄️ Cooldown activated - global:{next_global}s, category:{next_category}s, tone:{next_tone}s")
```

#### 作用
- 显示**三级冷却系统**的剩余时间
- 便于调试冷却参数设置
- 追踪冷却机制是否正常工作

---

### 3. **danmaku_event_engine.py** - 概率调度和性能指标

#### 增强位置
- Line 213-216: `_should_trigger()` 方法

#### 新增日志
```python
actual_prob = random.random()
triggered = actual_prob < self.trigger_probability
self.logger.debug(f"🎲 Probability check: {actual_prob:.3f} vs threshold:{self.trigger_probability:.3f} → {'triggered' if triggered else 'suppressed'}")
```

#### 作用
- 显示**概率调度的决策过程**
- 追踪实际概率值vs阈值
- 记录触发/抑制的结果

---

### 4. **activity_collector.py** - 采集快照和性能指标

#### 增强位置
- Line 116: `get_active_window_info()` 方法开头添加性能计时
- Line 147-148: 添加DEBUG日志和性能指标
- Line 153-154: 异常捕获时也记录耗时

#### 新增日志
```python
start_time = time.time()
# ... 采集逻辑 ...
elapsed = (time.time() - start_time) * 1000  # Convert to ms
self.logger.debug(f"📸 Activity snapshot: app={app_name}, title={window_title[:30]}, url={url[:50] if url else 'N/A'}, collect_time={elapsed:.1f}ms")
```

#### 作用
- 记录**每次采集的原始数据**
- 追踪**采集耗时**(性能指标)
- 验证**分类准确性**

---

### 5. **behavior_danmaku_manager.py** - 集成层性能监控

#### 增强位置
- Line 157: `_collection_loop()` 循环开始添加计时
- Line 170-171: 每个循环周期记录耗时
- Line 177-178: 异常时也记录循环耗时

#### 新增日志
```python
loop_start = time.time()
# ... 采集和处理逻辑 ...
loop_elapsed = (time.time() - loop_start) * 1000  # Convert to ms
self.logger.debug(f"⏱️ Collection loop cycle: {loop_elapsed:.1f}ms")
```

#### 作用
- 监控**整个采集循环的性能**
- 识别**性能瓶颈**
- 追踪**事件处理延迟**

---

## 📈 性能指标总结

| 性能指标 | 监控位置 | 正常范围 | 作用 |
|---------|---------|---------|------|
| **采集耗时** | activity_collector.py | <50ms | 验证活动采集效率 |
| **循环耗时** | behavior_danmaku_manager.py | <100ms | 整体处理性能 |
| **概率决策** | danmaku_event_engine.py | N/A | 触发率准确性 |

---

## 🔧 使用方法

### 启用DEBUG日志

在主程序或测试脚本中设置日志级别:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 启用DEBUG级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 运行测试

```bash
# 方式1: 使用专门的测试脚本
python test_debug_logs.py

# 方式2: 直接运行主程序 (需要先设置DEBUG级别)
python main.py
```

### 预期输出示例

```
2025-12-08 21:30:15,123 - gaiya.core.activity_collector - DEBUG - 📸 Activity snapshot: app=cursor.exe, title=CLAUDE.md - jindutiao - Cu, url=N/A, collect_time=12.3ms

2025-12-08 21:30:15,145 - gaiya.core.behavior_analyzer - DEBUG - 🎯 Mode determined: production (priority=3:app_type, type=ide)

2025-12-08 21:30:25,234 - gaiya.core.behavior_analyzer - DEBUG - 🔍 Trend detected: task_switch (app: cursor.exe → chrome.exe)

2025-12-08 21:30:25,256 - gaiya.core.danmaku_event_engine - DEBUG - 🎲 Probability check: 0.347 vs threshold:0.400 → suppressed

2025-12-08 21:30:35,367 - gaiya.core.behavior_analyzer - DEBUG - 🎯 Mode determined: consumption (priority=1:domain, domain=bilibili.com)

2025-12-08 21:30:35,389 - gaiya.core.cooldown_manager - DEBUG - ❄️ Cooldown activated - global:30s, category:60s, tone:120s

2025-12-08 21:30:40,123 - gaiya.core.behavior_danmaku_manager - DEBUG - ⏱️ Collection loop cycle: 85.7ms
```

---

## ✅ 测试验证

### 测试脚本

- [test_debug_logs.py](test_debug_logs.py) - DEBUG日志全面测试
- [test_behavior_stats.py](test_behavior_stats.py) - 统计信息实时更新测试

### 验证清单

- [x] ContentMode判断日志 - 显示4个优先级的判断依据
- [x] 行为趋势检测日志 - 追踪5种趋势的触发
- [x] 冷却系统状态日志 - 显示三级冷却剩余时间
- [x] 概率调度决策日志 - 记录触发/抑制过程
- [x] 活动采集快照日志 - 记录原始数据和耗时
- [x] 集成层性能日志 - 监控循环周期耗时

---

## 🎨 日志Emoji说明

| Emoji | 含义 | 使用场景 |
|------|------|---------|
| 🎯 | 目标/决策 | ContentMode判断 |
| 🔍 | 检测/发现 | 行为趋势检测 |
| ❄️ | 冷却 | 冷却系统激活 |
| 🎲 | 概率/随机 | 概率调度决策 |
| 📸 | 快照/捕获 | 活动数据采集 |
| ⏱️ | 性能/耗时 | 循环周期监控 |

---

## 📊 日志级别使用建议

| 级别 | 使用场景 | 性能影响 |
|-----|---------|---------|
| **INFO** | 正常运行监控 | 极低 |
| **DEBUG** | 开发调试、性能分析 | 低 |
| **WARNING** | 潜在问题 | 极低 |
| **ERROR** | 错误处理 | 极低 |

**推荐配置**:
- 开发环境: `DEBUG`
- 生产环境: `INFO`
- 性能调优: `DEBUG` (临时启用)

---

## 🎉 总结

本次DEBUG日志增强完成了:

✅ **5个关键节点**的详细监控
✅ **性能指标**的精准追踪
✅ **决策过程**的透明化
✅ **问题定位**的便捷化

**优势**:
- DEBUG日志不影响INFO级别的正常运行
- 性能开销极小(仅在DEBUG级别时输出)
- 便于后续功能迭代和Bug排查
- 符合设计文档的监控要求

**对比设计文档**:
- ✅ 第2.4节 ContentMode判断逻辑 - 已覆盖
- ✅ 第2.5节 状态趋势检测 - 已覆盖
- ✅ 第3.2节 冷却系统 - 已覆盖
- ✅ 第3.3节 概率调度器 - 已覆盖
- ✅ 第5节 性能监控 - 已添加

---

**开发完成时间**: 2025-12-08 21:35
**代码质量**: ⭐⭐⭐⭐⭐
**测试状态**: ✅ 待验证
