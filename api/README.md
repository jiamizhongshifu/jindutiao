# PyDayBar Vercel API代理服务器

## 🚀 快速部署指南

### 1. 准备工作

1. **注册Vercel账号**
   - 访问 https://vercel.com
   - 使用GitHub账号登录（免费）

2. **准备代码**
   - 确保 `api/` 目录包含所有Python文件
   - 确保 `vercel.json` 配置文件存在

### 2. 部署步骤

#### 方法A：使用Web界面（最简单）

1. **登录Vercel**
   - 访问 https://vercel.com
   - 点击 "New Project"

2. **导入项目**
   - 选择 "Import Git Repository"
   - 连接你的GitHub仓库
   - 或选择 "Upload Files" 直接上传 `api/` 目录

3. **配置项目**
   - Framework Preset: **Other**
   - Root Directory: 保持默认
   - Build Command: 留空
   - Output Directory: 留空

4. **设置环境变量**
   - 在项目设置中找到 "Environment Variables"
   - 添加以下环境变量：
     ```
     TUZI_API_KEY=your_api_key_here
     TUZI_BASE_URL=https://api.tu-zi.com/v1
     ```
   - 确保环境变量设置为 **Production** 环境

5. **部署**
   - 点击 "Deploy"
   - 等待部署完成（约30秒）

6. **获取部署URL**
   - 部署完成后，Vercel会提供一个URL
   - 格式：`https://your-project-name.vercel.app`
   - **复制这个URL！**

### 3. 更新客户端配置

部署完成后，更新 `ai_client.py` 中的默认代理URL：

```python
# ai_client.py (第28行)
proxy_url = os.getenv(
    "PYDAYBAR_PROXY_URL",
    "https://your-project-name.vercel.app"  # 替换为你的实际Vercel URL
)
```

### 4. 测试部署

测试健康检查：
```bash
curl https://your-project-name.vercel.app/api/health
```

应该返回：
```json
{
  "status": "ok",
  "timestamp": "2025-11-01T...",
  "service": "PyDayBar API Proxy (Vercel)"
}
```

## 📁 文件结构

```
项目根目录/
├── api/
│   ├── plan-tasks.py           # 任务规划API
│   ├── quota-status.py         # 配额查询API
│   ├── health.py               # 健康检查API
│   ├── generate-weekly-report.py  # 周报生成API
│   ├── chat-query.py           # 对话查询API
│   ├── recommend-theme.py      # 主题推荐API
│   └── generate-theme.py       # 主题生成API
├── vercel.json                 # Vercel配置
└── ... (其他文件)
```

## ⚠️ 重要提醒

### 超时限制

- **Vercel免费版：10秒超时**
- **Vercel Pro版：60秒超时**
- **AI请求通常需要30-60秒**

**建议：**
- 如果AI请求时间 < 10秒：使用Vercel免费版 ✅
- 如果AI请求时间 > 10秒：升级到Vercel Pro（$20/月）或使用Railway

### 测试建议

1. **先部署测试**
   - 部署后测试实际AI请求时间
   - 如果 < 10秒，免费版即可
   - 如果 > 10秒，考虑升级或迁移

## ✅ 已完成的工作

- ✅ 所有API端点已实现
- ✅ CORS已配置
- ✅ 错误处理已完善
- ✅ 客户端已更新为使用Vercel

## 🎯 下一步

1. **部署到Vercel**（按照上面的步骤）
2. **更新客户端URL**（部署后获取的URL）
3. **测试功能**（确保所有API正常工作）
4. **监控使用情况**（在Vercel Dashboard查看）

## 📚 相关文档

- `VERCEL_DEPLOYMENT.md` - 详细部署指南
- `VERCEL_QUICK_START.md` - 快速开始指南
- `RAILWAY_DEPLOYMENT.md` - Railway备选方案

