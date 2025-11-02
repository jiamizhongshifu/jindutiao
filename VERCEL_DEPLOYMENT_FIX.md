# Vercel部署修复文档

## 问题描述

**症状**：
- 用户重新部署后，应用显示"无法连接服务"
- 点击"刷新配额"显示"无法连接云服务"
- 所有Vercel API端点返回500错误或连接失败

**时间线**：
- 2025-11-02 17:36 - 实现了基于Supabase的真实配额管理系统
- 部署到Vercel后 - 所有API端点失败
- 2025-11-02 18:20 - 问题修复完成

## 根本原因

**核心问题**：`api/requirements.txt`缺少`supabase`依赖

### 详细分析

1. **依赖管理机制**：
   - Vercel在构建Python Serverless Functions时，会查找`api/`目录下的`requirements.txt`
   - 如果存在`api/requirements.txt`，Vercel会**优先使用它**，而忽略根目录的`requirements.txt`
   - 这是Vercel的设计：每个API目录可以有独立的轻量级依赖

2. **我们的错误**：
   ```
   根目录/requirements.txt  ✅ 包含 supabase>=2.23.0
   api/requirements.txt      ❌ 缺少 supabase（只有requests）
   ```

3. **失败链**：
   ```
   Vercel部署
    ↓
   读取 api/requirements.txt（只安装requests）
    ↓
   quota_manager.py尝试 import supabase
    ↓
   ImportError: No module named 'supabase'
    ↓
   所有使用quota_manager的API（quota-status、plan-tasks）崩溃
    ↓
   用户看到"无法连接云服务"
   ```

## 诊断过程

### 1. 初步测试
```bash
curl https://jindutiao.vercel.app/api/health
# 结果：500错误或超时
```

### 2. 创建诊断端点
创建`api/debug.py`来检查：
- Python版本
- 系统路径
- 环境变量状态
- Supabase库导入状态
- quota_manager导入状态

### 3. 发现问题
通过检查本地文件结构，发现：
```bash
$ cat api/requirements.txt
requests==2.31.0
# ❌ 缺少supabase！

$ cat requirements.txt
...
supabase>=2.23.0  # ✅ 存在但被忽略
```

### 4. 验证假设
理解了Vercel的依赖优先级机制：
- `api/requirements.txt` > `requirements.txt`
- 这解释了为什么部署失败

## 解决方案

### 修复代码

**文件**：`api/requirements.txt`

**修改前**：
```
requests==2.31.0

```

**修改后**：
```
requests==2.31.0
supabase>=2.23.0
```

### 部署命令
```bash
git add api/requirements.txt
git commit -m "fix: 添加supabase依赖到api/requirements.txt修复Vercel部署失败"
git push
```

## 验证结果

### 1. Health检查
```bash
$ curl https://jindutiao.vercel.app/api/health
{
  "status": "ok",
  "timestamp": "2025-11-02T10:20:50.723723",
  "service": "PyDayBar API Proxy (Vercel)",
  "message": "Health check successful"
}
✅ 状态码: 200
```

### 2. 配额查询
```bash
$ curl "https://jindutiao.vercel.app/api/quota-status?user_id=user_demo&user_tier=free"
{
  "remaining": {
    "daily_plan": 2,
    "weekly_report": 1,
    "chat": 10,
    "theme_recommend": 5,
    "theme_generate": 3
  },
  "user_tier": "free"
}
✅ 状态码: 200
✅ 显示真实配额（之前本地测试用掉1次，3→2）
```

### 3. Debug端点
```bash
$ curl https://jindutiao.vercel.app/api/debug
{
  "python_version": "3.12.11 ...",
  "supabase_version": "2.23.0",
  "supabase_import": "SUCCESS",
  "quota_manager_import": "SUCCESS",
  "env_vars": {
    "SUPABASE_URL": "https://qpgypaxwjgcirssydgqh.supabase.co",
    "SUPABASE_ANON_KEY": "SET"
  },
  "errors": []
}
✅ 所有检查通过
```

## 经验教训

### ✅ 最佳实践

1. **统一依赖管理**
   - 如果项目使用`api/requirements.txt`，所有API依赖都应该在这里声明
   - 根目录的`requirements.txt`可以保留用于本地开发

2. **依赖文件结构**
   ```
   推荐结构（Vercel项目）：
   ├── requirements.txt          # 本地开发依赖（包含GUI、测试等）
   └── api/
       ├── requirements.txt      # API依赖（仅生产必需）
       └── *.py                  # API端点
   ```

3. **部署前检查清单**
   - [ ] 确认`api/requirements.txt`包含所有API代码的导入
   - [ ] 验证环境变量在Vercel Dashboard中配置
   - [ ] 使用debug端点验证依赖安装状态

### ⚠️ 常见陷阱

1. **假设Vercel会合并requirements.txt**
   - ❌ 错误：认为Vercel会同时使用根目录和api/的requirements.txt
   - ✅ 正确：Vercel只使用离API文件最近的requirements.txt

2. **忽略本地vs云环境差异**
   - ❌ 错误：本地测试通过就认为部署会成功
   - ✅ 正确：本地可能使用根目录requirements.txt，云端使用api/requirements.txt

3. **缺少诊断手段**
   - ❌ 错误：500错误后反复尝试修改配置
   - ✅ 正确：先创建debug端点，明确诊断问题

## 相关文件

- `api/requirements.txt` - API依赖（已修复）
- `api/quota_manager.py` - 配额管理器（需要supabase）
- `api/debug.py` - 诊断端点
- `QUOTA_SYSTEM_README.md` - 配额系统文档

## 后续改进

1. **监控**
   - 在Vercel Dashboard中设置函数错误告警
   - 定期检查API端点健康状态

2. **文档**
   - 在README中添加部署检查清单
   - 文档化Vercel特有的依赖管理机制

3. **自动化**
   - 考虑在CI/CD中添加依赖完整性检查
   - 部署后自动运行health check

---

**修复完成时间**：2025-11-02 18:20
**影响**：所有API端点恢复正常，真实配额系统正常工作
**停机时间**：约30分钟（从发现问题到修复完成）
