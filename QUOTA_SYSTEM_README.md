# PyDayBar 真实配额管理系统

## 🎯 系统概述

成功实现了基于Supabase的真实配额管理系统，配额将被持久化存储并真实扣除。

## ✅ 已完成的工作

### 1. Supabase数据库设置
- ✅ 创建了`user_quotas`表存储配额信息
- ✅ 支持多种配额类型（任务规划、周报、聊天、主题推荐/生成）
- ✅ 自动重置机制（每日/每周）
- ✅ 行级安全策略

### 2. 后端API实现
- ✅ `quota_manager.py` - 配额管理核心类
- ✅ `quota-status.py` - 配额查询API（从数据库读取）
- ✅ `plan-tasks.py` - 任务生成API（检查并扣除配额）
- ✅ 完整的错误处理和降级策略

### 3. Vercel配置
- ✅ 环境变量：SUPABASE_URL
- ✅ 环境变量：SUPABASE_ANON_KEY
- ✅ 自动部署配置

### 4. 本地测试
- ✅ 配额查询测试通过
- ✅ 配额扣除测试通过
- ✅ 配额验证测试通过

## 📊 配额规则

### 免费用户（free tier）
- 每日任务规划：3次/天
- 每周报告：1次/周
- AI聊天：10次/天
- 主题推荐：5次/天
- 主题生成：3次/天

### 专业用户（pro tier）
- 每日任务规划：50次/天
- 每周报告：10次/周
- AI聊天：100次/天
- 主题推荐：50次/天
- 主题生成：50次/天

## 🧪 如何测试

### 测试1：查看初始配额
1. 打开PyDayBar应用
2. 右键进度条 → 配置
3. 查看"AI智能任务生成"区域的配额显示
4. 应该显示："✓ 今日剩余: 2 次规划"（因为我们已经测试用掉了1次）

### 测试2：生成任务并验证配额扣除
1. 在配置界面的AI输入框输入：
   ```
   明天上午9点到12点工作，12点到13点午休，下午工作到18点
   ```
2. 点击"✨ 智能生成任务"
3. 等待任务生成（约5-10秒）
4. **观察配额变化**：应该从"2次"变为"1次"
5. 点击"🔄 刷新配额"按钮
6. 确认配额确实被扣除

### 测试3：验证配额用尽
1. 重复测试2，直到配额归零
2. 再次尝试生成任务
3. 应该显示错误："⚠️ 今日配额已用完"
4. 无法生成新任务

### 测试4：在Supabase中查看数据
1. 登录Supabase控制台
2. 进入项目 → Table Editor → user_quotas
3. 找到user_id为"user_demo"的记录
4. 查看`daily_plan_used`字段，应该显示已使用次数
5. 查看`daily_plan_reset_at`字段，显示明天的重置时间

## 🔍 验证配额是否真实扣除

### 方法1：重启应用验证
1. 完全关闭PyDayBar应用
2. 重新启动应用
3. 打开配置界面查看配额
4. **配额应该保持扣除后的值**（不会恢复到初始值）

### 方法2：在Supabase中手动查询
```sql
SELECT user_id, user_tier,
       daily_plan_total, daily_plan_used,
       daily_plan_total - daily_plan_used as remaining
FROM user_quotas
WHERE user_id = 'user_demo';
```

### 方法3：使用测试脚本
```bash
python test_quota_simple.py
```

## 🔄 配额重置

### 自动重置
- **每日配额**：每天UTC时间00:00自动重置
- **每周配额**：每周日UTC时间00:00自动重置
- 重置由Supabase触发器自动执行

### 手动重置（仅用于测试）
在Supabase SQL编辑器中执行：
```sql
UPDATE user_quotas
SET daily_plan_used = 0,
    daily_plan_reset_at = NOW() + INTERVAL '1 day'
WHERE user_id = 'user_demo';
```

## 📈 监控和调试

### 查看Vercel函数日志
1. 访问：https://vercel.com/dashboard
2. 选择项目 → Functions
3. 点击函数名（quota-status或plan-tasks）
4. 查看Logs标签，可以看到：
   - 配额查询记录
   - 配额扣除记录
   - 错误信息

### 查看本地日志
应用运行时的配额操作会记录在：
```
C:\Users\Sats\Downloads\jindutiao\pydaybar.log
```

查找配额相关日志：
```bash
type pydaybar.log | findstr "配额"
```

## 🛠 故障排除

### 问题1：配额显示"无法连接云服务"
**原因**：Vercel函数冷启动或网络问题
**解决**：
1. 等待10-15秒
2. 点击"刷新配额"按钮重试

### 问题2：配额没有被扣除
**原因**：Supabase连接失败，使用了降级策略
**解决**：
1. 检查Vercel环境变量是否正确配置
2. 检查Supabase项目是否正常运行
3. 查看Vercel函数日志确认错误

### 问题3：配额显示错误的值
**原因**：可能是缓存或数据不一致
**解决**：
1. 点击"刷新配额"
2. 检查Supabase数据库中的实际值
3. 如需要，手动重置配额

## 🎉 成功标志

如果看到以下情况，说明配额系统完全正常：
- ✅ 启动时能正确显示配额
- ✅ 生成任务后配额数字减少
- ✅ 重启应用后配额保持扣除后的值
- ✅ 配额用尽时无法继续生成任务
- ✅ Supabase数据库中的数据与UI显示一致

## 📝 技术细节

### 数据流程
```
客户端 → Vercel API → Supabase数据库
   ↓
配额查询/扣除
   ↓
返回最新配额
   ↓
UI更新显示
```

### 关键文件
- `api/quota_manager.py` - 配额管理逻辑
- `api/quota-status.py` - 配额查询端点
- `api/plan-tasks.py` - 任务生成端点
- `supabase_schema.sql` - 数据库架构

### 环境变量
```
SUPABASE_URL=https://qpgypaxwjgcirssydgqh.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...（您的密钥）
```

---

**祝测试顺利！如有问题请查看日志或联系支持。** 🚀
