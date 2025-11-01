# Vercel API测试脚本

## 测试步骤

### 1. 健康检查端点
在浏览器中访问：
```
https://jindutiao.vercel.app/api/health
```

预期返回：
```json
{
  "status": "ok",
  "timestamp": "2025-11-01T...",
  "service": "PyDayBar API Proxy (Vercel)"
}
```

### 2. 配额查询端点
在浏览器中访问：
```
https://jindutiao.vercel.app/api/quota-status?user_tier=free
```

预期返回：
```json
{
  "remaining": {
    "daily_plan": 3,
    "weekly_report": 1,
    "chat": 10,
    "theme_recommend": 5,
    "theme_generate": 3
  },
  "user_tier": "free"
}
```

### 3. 在Vercel Dashboard中检查

1. **Functions列表**
   - 进入项目的 "Functions" 标签页
   - 应该看到7个函数：
     - `/api/health`
     - `/api/quota-status`
     - `/api/plan-tasks`
     - `/api/generate-weekly-report`
     - `/api/chat-query`
     - `/api/recommend-theme`
     - `/api/generate-theme`

2. **函数测试**
   - 点击任意函数
   - 在函数详情页中点击 "Test" 按钮
   - 应该能看到函数响应

### 4. 如果返回404

如果访问返回404，可能的原因：

1. **路由问题**
   - Vercel可能没有正确识别Python函数
   - 检查 `vercel.json` 配置

2. **函数格式问题**
   - 确认函数使用 `BaseHTTPRequestHandler` 格式
   - 确认函数文件名正确

3. **部署未完成**
   - 检查部署状态是否为 "Ready"
   - 查看部署日志是否有错误

## 客户端测试

如果API端点正常工作，可以在PyDayBar应用中测试：

1. **打开配置管理器**
   - 右键系统托盘图标
   - 选择"配置管理器"

2. **测试AI功能**
   - 进入"任务管理"标签页
   - 点击"AI智能规划"
   - 应该能正常连接代理服务器

3. **检查日志**
   - 如果遇到问题，查看 `pydaybar.log` 文件
   - 查找API请求相关的错误信息

