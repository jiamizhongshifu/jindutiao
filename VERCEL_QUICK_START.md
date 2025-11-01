# Vercel部署快速开始指南

## ✅ 已完成的工作

1. ✅ 创建了所有Vercel Serverless Functions
2. ✅ 配置了Vercel部署文件
3. ✅ 更新了客户端代码支持代理模式

## 📁 文件结构

```
项目根目录/
├── vercel_api/
│   ├── plan-tasks.py           # 任务规划API
│   ├── quota-status.py         # 配额查询API
│   ├── health.py               # 健康检查API
│   ├── generate-weekly-report.py  # 周报生成API
│   ├── chat-query.py           # 对话查询API
│   ├── recommend-theme.py      # 主题推荐API
│   ├── generate-theme.py       # 主题生成API
│   └── requirements.txt        # Python依赖
├── vercel.json                 # Vercel配置
└── ... (其他文件)
```

## 🚀 部署步骤

### 1. 准备部署

确保以下文件存在：
- ✅ `vercel_api/` 目录及所有API文件
- ✅ `vercel.json` 配置文件
- ✅ `vercel_api/requirements.txt` 依赖文件

### 2. 部署到Vercel

#### 方法A：使用Web界面（推荐）

1. **登录Vercel**
   - 访问 https://vercel.com
   - 使用GitHub账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Import Git Repository"
   - 连接你的GitHub仓库
   - 或选择 "Upload Files" 直接上传 `vercel_api/` 目录

3. **配置项目**
   - Framework Preset: **Other**
   - Root Directory: 保持默认（或设置为 `vercel_api`）
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
   - **复制这个URL，稍后需要更新到客户端**

#### 方法B：使用CLI

```bash
# 1. 安装Vercel CLI
npm install -g vercel

# 2. 登录
vercel login

# 3. 在项目根目录部署
vercel

# 4. 设置环境变量
vercel env add TUZI_API_KEY
vercel env add TUZI_BASE_URL

# 5. 部署到生产环境
vercel --prod
```

### 3. 更新客户端配置

部署完成后，更新 `ai_client.py` 中的默认代理URL：

```python
# ai_client.py
proxy_url = os.getenv(
    "PYDAYBAR_PROXY_URL",
    "https://your-project-name.vercel.app"  # 替换为你的实际Vercel URL
)
```

或者通过环境变量设置（推荐）：

```bash
# Windows PowerShell
$env:PYDAYBAR_PROXY_URL="https://your-project-name.vercel.app"

# Linux/macOS
export PYDAYBAR_PROXY_URL="https://your-project-name.vercel.app"
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

## 📝 重要提醒

### ⚠️ 超时限制

- **Vercel免费版：10秒超时**
- **Vercel Pro版：60秒超时**
- **AI请求通常需要30-60秒**

**建议：**
- 如果AI请求时间 < 10秒：使用Vercel免费版
- 如果AI请求时间 > 10秒：升级到Vercel Pro（$20/月）或使用Railway

### ✅ 当前配置

- ✅ 所有API端点已实现
- ✅ CORS已配置
- ✅ 错误处理已完善
- ✅ 环境变量已配置

## 🎯 下一步

1. **部署到Vercel**（按照上面的步骤）
2. **更新客户端URL**（部署后获取的URL）
3. **测试功能**（确保所有API正常工作）
4. **监控使用情况**（在Vercel Dashboard查看）

## 📚 相关文档

- `VERCEL_DEPLOYMENT.md` - 详细部署指南
- `RAILWAY_DEPLOYMENT.md` - Railway备选方案
- `LOW_COST_SECURITY_SOLUTIONS.md` - 方案对比分析

## 🆘 故障排查

### 问题1：函数超时

**解决方案：**
- 检查AI请求时间
- 如果 > 10秒，升级到Vercel Pro或使用Railway

### 问题2：环境变量未生效

**解决方案：**
- 检查Vercel Dashboard中的环境变量设置
- 确保环境变量已添加到Production环境
- 重新部署

### 问题3：CORS错误

**解决方案：**
- 确保所有函数都返回了正确的CORS头
- 检查客户端请求的Origin

## ✨ 完成！

部署完成后，你的API代理服务器就完全准备好了！🎉

