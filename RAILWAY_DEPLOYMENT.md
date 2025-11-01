# Railway部署快速指南

## 部署步骤

### 1. 准备工作

1. **注册Railway账号**
   - 访问 https://railway.app
   - 使用GitHub账号登录（免费）

2. **准备代码**
   - 确保有以下文件：
     - `proxy_server.py`
     - `proxy_requirements.txt`
     - `Procfile` 或 `railway.json`

### 2. 部署方法

#### 方法A：使用Web界面（推荐）

1. **登录Railway**
   - 访问 https://railway.app
   - 点击 "New Project"

2. **创建项目**
   - 选择 "Deploy from GitHub repo"
   - 连接你的GitHub仓库
   - 或选择 "Empty Project"

3. **添加服务**
   - 点击 "New Service"
   - 选择 "GitHub Repo" 或 "Empty Service"
   - 如果选择GitHub，Railway会自动检测到Flask应用

4. **配置环境变量**
   - 在项目设置中点击 "Variables"
   - 添加以下环境变量：
     ```
     TUZI_API_KEY=your_api_key_here
     TUZI_BASE_URL=https://api.tu-zi.com/v1
     PORT=5000
     DEBUG=false
     ```

5. **部署**
   - Railway会自动部署
   - 等待部署完成（约1-2分钟）

6. **获取URL**
   - 部署完成后，Railway会提供一个URL
   - 格式：`https://your-project-name.up.railway.app`
   - 复制这个URL

#### 方法B：使用CLI

```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 初始化项目
railway init

# 4. 设置环境变量
railway variables set TUZI_API_KEY=your_api_key_here
railway variables set TUZI_BASE_URL=https://api.tu-zi.com/v1
railway variables set PORT=5000
railway variables set DEBUG=false

# 5. 部署
railway up
```

### 3. 更新客户端配置

部署完成后，更新 `ai_client.py` 中的默认代理URL：

```python
proxy_url = os.getenv(
    "PYDAYBAR_PROXY_URL",
    "https://your-project-name.up.railway.app"  # 替换为你的实际URL
)
```

或者通过环境变量设置：

```bash
# Windows PowerShell
$env:PYDAYBAR_PROXY_URL="https://your-project-name.up.railway.app"

# Linux/macOS
export PYDAYBAR_PROXY_URL="https://your-project-name.up.railway.app"
```

### 4. 测试部署

部署完成后，测试健康检查：

```bash
curl https://your-project-name.up.railway.app/health
```

应该返回：
```json
{
  "status": "ok",
  "timestamp": "2025-11-01T...",
  "service": "PyDayBar API Proxy"
}
```

## 成本说明

### Railway免费额度

- **$5免费额度/月**
- **足够支持：**
  - 约 1000-5000 次API请求/月
  - 小型应用完全够用

### 超出免费额度后

- **自动升级到付费计划**
- **费用：** $5/月起
- **支持：** 无限制使用

## 注意事项

1. **首次部署可能需要几分钟**
2. **Railway会自动分配HTTPS证书**
3. **URL格式：** `https://your-project-name.up.railway.app`
4. **环境变量修改后需要重新部署**
5. **API密钥安全：** 密钥存储在Railway环境变量中，不会暴露给客户端

## 故障排查

### 问题1：部署失败

**可能原因：**
- 缺少 `requirements.txt` 或 `Procfile`
- 环境变量未设置

**解决方案：**
- 确保 `proxy_requirements.txt` 存在
- 确保 `Procfile` 或 `railway.json` 存在
- 检查环境变量是否正确设置

### 问题2：API请求失败

**可能原因：**
- API密钥未设置或错误
- 网络连接问题

**解决方案：**
- 检查Railway环境变量中的 `TUZI_API_KEY`
- 检查Railway日志查看详细错误信息

### 问题3：客户端无法连接

**可能原因：**
- 代理URL错误
- 网络问题

**解决方案：**
- 确认代理URL正确
- 检查Railway服务是否正常运行
- 测试健康检查端点

## 后续优化

1. **添加数据库**：用于配额管理和用户追踪
2. **添加认证**：用于用户识别和付费转化
3. **添加监控**：用于追踪使用情况和性能
4. **添加缓存**：用于提高响应速度
