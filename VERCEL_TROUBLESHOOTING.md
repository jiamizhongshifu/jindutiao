# Vercel部署问题排查与修复

## 问题：返回404错误

访问 `https://jindutiao.vercel.app/api/health` 返回 404 NOT_FOUND

## 可能原因

### 1. Handler函数格式问题

Vercel Python函数可能需要使用不同的格式。让我检查正确的格式：

**当前格式：**
```python
def handler(req):
    return {'statusCode': 200, ...}
```

**Vercel Python可能需要：**
- 使用 `index.py` 文件
- 或者使用特定的函数名（如 `handler` 或 `app`）

### 2. 检查Vercel Dashboard

请在Vercel Dashboard中检查：
1. **Functions标签页** - 查看是否有函数被部署
2. **Deployments标签页** - 查看部署日志
3. **Runtime Logs** - 查看运行时日志

### 3. 简化配置

尝试简化 `vercel.json`：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    }
  ]
}
```

Vercel会自动将 `api/` 目录下的文件映射到 `/api/` 路由。

## 快速修复步骤

### 步骤1：检查部署日志

1. 登录Vercel Dashboard
2. 进入项目 `jindutiao`
3. 查看最新的部署日志
4. 检查是否有错误信息

### 步骤2：检查函数列表

在Vercel Dashboard中：
1. 进入项目的 "Functions" 标签页
2. 查看是否列出了以下函数：
   - `/api/health`
   - `/api/plan-tasks`
   - `/api/quota-status`
   - 等等

如果函数列表为空，说明函数没有正确部署。

### 步骤3：检查文件结构

确保上传的文件结构正确：
```
项目根目录/
├── api/
│   ├── health.py
│   ├── plan-tasks.py
│   ├── quota-status.py
│   └── ...
└── vercel.json
```

### 步骤4：检查环境变量

确保在Vercel Dashboard中设置了：
- `TUZI_API_KEY`
- `TUZI_BASE_URL`

## 备选方案：重新部署

如果以上都不行，尝试：

1. **删除当前部署**
2. **重新上传文件**
   - 确保 `api/` 目录包含所有Python文件
   - 确保 `vercel.json` 存在
3. **重新部署**

## 测试URL

部署成功后，应该可以访问：
- `https://jindutiao.vercel.app/api/health`
- `https://jindutiao.vercel.app/api/quota-status?user_tier=free`

如果这些都不工作，可能需要检查Vercel的Python运行时配置。
