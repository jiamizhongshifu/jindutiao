# Vercel部署指南

## Vercel vs Railway 对比

| 特性 | Vercel | Railway |
|------|--------|---------|
| **免费额度** | 100GB带宽/月，无限函数调用 | $5额度/月 |
| **部署方式** | Serverless Functions | 传统服务器 |
| **冷启动** | 首次请求可能较慢（~1-2秒） | 无冷启动 |
| **适用场景** | API代理、函数式服务 | 长时间运行的服务 |
| **部署速度** | 极快（几秒） | 较快（1-2分钟） |
| **成本** | 免费（初期） | 免费（初期） |

**推荐：** 如果只是API代理，Vercel更适合（完全免费，部署更快）

---

## 快速开始

### 1. 准备工作

1. **注册Vercel账号**
   - 访问 https://vercel.com
   - 使用GitHub账号登录（免费）

2. **安装Vercel CLI**（可选）
   ```bash
   npm install -g vercel
   ```

### 2. 部署步骤

#### 方法A：使用Web界面（推荐）

1. **登录Vercel**
   - 访问 https://vercel.com
   - 点击 "New Project"

2. **导入项目**
   - 选择 "Import Git Repository"
   - 连接你的GitHub仓库
   - 或选择 "Upload Files" 直接上传

3. **配置项目**
   - Framework Preset: 选择 "Other"
   - Root Directory: 保持默认
   - Build Command: 留空（不需要构建）
   - Output Directory: 留空

4. **配置环境变量**
   - 在项目设置中点击 "Environment Variables"
   - 添加以下环境变量：
     ```
     TUZI_API_KEY=your_api_key_here
     TUZI_BASE_URL=https://api.tu-zi.com/v1
     ```

5. **部署**
   - 点击 "Deploy"
   - 等待部署完成（约30秒）

6. **获取URL**
   - 部署完成后，Vercel会提供一个URL
   - 格式：`https://your-project-name.vercel.app`
   - 复制这个URL

#### 方法B：使用CLI

```bash
# 1. 登录
vercel login

# 2. 在项目目录中初始化
cd vercel_api
vercel

# 3. 设置环境变量
vercel env add TUZI_API_KEY
vercel env add TUZI_BASE_URL

# 4. 部署
vercel --prod
```

### 3. 目录结构

```
项目根目录/
├── vercel_api/
│   ├── plan-tasks.py      # 任务规划API
│   ├── quota-status.py    # 配额查询API
│   ├── health.py          # 健康检查API
│   └── requirements.txt   # Python依赖
├── vercel.json            # Vercel配置
└── ... (其他文件)
```

**注意：** 如果使用 `api/` 目录（标准Vercel目录），函数会自动映射到 `/api/` 路径。
如果使用 `vercel_api/` 目录，需要在 `vercel.json` 中配置路由。

### 4. 更新客户端配置

部署完成后，更新 `ai_client.py` 中的默认代理URL：

```python
proxy_url = os.getenv(
    "PYDAYBAR_PROXY_URL",
    "https://your-project-name.vercel.app"  # 替换为你的实际URL
)
```

### 5. 测试部署

部署完成后，测试健康检查：

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

---

## API端点

部署后，你可以访问以下端点：

- `GET /api/health` - 健康检查
- `GET /api/quota-status?user_tier=free` - 配额查询
- `POST /api/plan-tasks` - 任务规划

---

## 成本说明

### Vercel免费额度

- **100GB带宽/月**
- **无限函数调用**
- **足够支持：**
  - 约 10,000-50,000 次API请求/月
  - 小型应用完全够用

### 超出免费额度后

- **自动升级到付费计划**
- **费用：** $20/月起（Pro计划）
- **支持：** 更多带宽和功能

---

## 注意事项

1. **冷启动延迟**
   - 首次请求可能需要1-2秒（冷启动）
   - 后续请求会很快（已预热）
   - 对于AI请求（通常需要30-60秒），这个延迟可以忽略

2. **函数超时**
   - Vercel免费版：10秒超时
   - Vercel Pro版：60秒超时
   - **注意：** AI请求通常需要30-60秒，建议使用Pro版或Railway

3. **环境变量**
   - 在Vercel Dashboard中设置
   - 生产环境会自动使用

4. **函数大小限制**
   - 免费版：50MB
   - Pro版：250MB

---

## Vercel vs Railway 选择建议

### 选择Vercel如果：
- ✅ 只需要API代理功能
- ✅ 希望完全免费（初期）
- ✅ 希望快速部署
- ✅ 请求响应时间 < 10秒（免费版）或 < 60秒（Pro版）

### 选择Railway如果：
- ✅ 需要长时间运行的服务
- ✅ AI请求需要 > 60秒
- ✅ 需要更多控制权
- ✅ 不介意 $5/月的成本

---

## 推荐方案

**对于PyDayBar项目：**

1. **初期（用户量小）：** 使用Vercel（完全免费）
2. **成长期（用户量增长）：** 升级到Vercel Pro（$20/月）或迁移到Railway（$5/月）

**注意：** 由于AI请求通常需要30-60秒，如果使用Vercel免费版（10秒超时），可能需要：
- 升级到Vercel Pro（60秒超时）
- 或使用Railway（无超时限制）

---

## 故障排查

### 问题1：函数超时

**可能原因：**
- AI请求超过10秒（免费版）或60秒（Pro版）

**解决方案：**
- 升级到Vercel Pro（60秒超时）
- 或使用Railway（无超时限制）

### 问题2：环境变量未生效

**可能原因：**
- 环境变量未设置或设置错误

**解决方案：**
- 检查Vercel Dashboard中的环境变量
- 确保环境变量已添加到生产环境

### 问题3：函数无法访问

**可能原因：**
- 路由配置错误
- 函数文件路径错误

**解决方案：**
- 检查 `vercel.json` 中的路由配置
- 确保函数文件在 `api/` 目录下

---

## 总结

**Vercel优点：**
- ✅ 完全免费（初期）
- ✅ 部署极快
- ✅ 自动HTTPS
- ✅ 全球CDN

**Vercel缺点：**
- ⚠️ 免费版10秒超时（AI请求可能不够）
- ⚠️ 冷启动延迟

**推荐：** 如果AI请求时间较长（>10秒），建议使用Railway。如果请求时间较短（<10秒），Vercel是更好的选择。

