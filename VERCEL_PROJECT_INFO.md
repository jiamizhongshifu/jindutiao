# Vercel项目信息查看指南

## 📊 项目基本信息

从你的截图可以看到：

### 1. Project Name（项目名称）
- **当前名称:** `jindutiao`
- **完整URL:** `vercel.com/...zhongshifus-projects/jindutiao`
- **用途:** 用于在Dashboard、CLI和部署URL中识别项目

### 2. Project ID（项目ID）
- **ID:** `prj_TEhZ3iXh2MfgelKntnyiJGpEF09P`
- **用途:** 用于与Vercel API交互

## 🔍 在Vercel Dashboard中查看更多信息

### 1. **Functions（函数列表）**标签页
查看所有已部署的Serverless Functions：
- `/api/health` - 健康检查
- `/api/quota-status` - 配额查询
- `/api/plan-tasks` - 任务规划
- `/api/generate-weekly-report` - 周报生成
- `/api/chat-query` - 对话查询
- `/api/recommend-theme` - 主题推荐
- `/api/generate-theme` - 主题生成

**操作方法:**
1. 在项目页面，点击左侧菜单的 **"Functions"** 标签页
2. 查看所有函数的列表
3. 点击任意函数可以查看详细信息、测试函数、查看日志

### 2. **Deployments（部署历史）**标签页
查看所有部署记录：
- 部署状态（Ready/Failed/Building）
- 部署时间
- 触发原因（Git Push/Manual）
- 部署URL
- 构建日志和运行时日志

**操作方法:**
1. 点击左侧菜单的 **"Deployments"** 标签页
2. 查看部署历史列表
3. 点击任意部署可以查看：
   - 构建日志（Build Logs）
   - 运行时日志（Runtime Logs）
   - 预览URL

### 3. **Settings（设置）**标签页

#### a) General（常规设置）
- Project Name（项目名称）
- Project ID（项目ID）
- Framework Preset（框架预设）
- Root Directory（根目录）
- Build & Development Settings（构建和开发设置）

#### b) Environment Variables（环境变量）⭐ **重要**
检查是否已设置：
- `TUZI_API_KEY` - API密钥
- `TUZI_BASE_URL` - API基础URL（默认：`https://api.tu-zi.com/v1`）

**操作方法:**
1. 在Settings中点击 **"Environment Variables"**
2. 确认以下环境变量已设置：
   ```
   TUZI_API_KEY=你的API密钥
   TUZI_BASE_URL=https://api.tu-zi.com/v1
   ```
3. 确保环境变量设置为 **Production** 环境

#### c) Domains（域名）
- 自定义域名配置
- 默认域名：`jindutiao.vercel.app`

#### d) Integrations（集成）
- Git仓库连接
- 其他服务集成

### 4. **Analytics（分析）**标签页
- 函数调用次数
- 响应时间统计
- 错误率统计
- 流量使用情况

### 5. **Logs（日志）**标签页
- 实时函数执行日志
- 错误日志
- 性能日志

## 🔧 关键检查项

### ✅ 必须检查的内容：

1. **环境变量**
   - [ ] `TUZI_API_KEY` 已设置
   - [ ] `TUZI_BASE_URL` 已设置（可选，有默认值）
   - [ ] 环境变量设置为 **Production**

2. **Functions列表**
   - [ ] 所有7个函数都已部署
   - [ ] 函数状态正常
   - [ ] 点击函数可以查看详细信息

3. **最新部署**
   - [ ] 部署状态为 "Ready"（绿色）
   - [ ] 没有构建错误
   - [ ] 部署日志中没有错误信息

4. **函数测试**
   - [ ] 可以在Functions页面直接测试函数
   - [ ] 测试 `/api/health` 返回正常响应

## 🐛 如果仍然404

如果访问 `https://jindutiao.vercel.app/api/health` 返回404：

1. **检查Functions列表**
   - 确认所有函数都已列出
   - 如果没有，说明函数没有正确部署

2. **检查构建日志**
   - 查看最新部署的Build Logs
   - 检查是否有Python相关的错误

3. **检查环境变量**
   - 确认 `TUZI_API_KEY` 已设置
   - 环境变量必须在 **Production** 环境中

4. **检查文件结构**
   - 确认 `api/` 目录中的所有 `.py` 文件都已提交到Git
   - 确认 `vercel.json` 文件已提交

5. **重新部署**
   - 如果发现问题，可以点击 "Redeploy" 重新部署
   - 或者推送新的代码到Git仓库

## 📝 建议操作

1. **先检查Functions列表**
   - 进入Functions标签页
   - 查看是否有7个函数
   - 如果列表为空，说明函数格式有问题

2. **检查环境变量**
   - 进入Settings → Environment Variables
   - 确认已设置 `TUZI_API_KEY`

3. **查看最新部署日志**
   - 进入Deployments标签页
   - 点击最新部署
   - 查看Build Logs和Runtime Logs

4. **测试函数**
   - 在Functions页面点击任意函数
   - 点击 "Test" 按钮测试函数
   - 查看返回结果

请告诉我你在Vercel Dashboard中看到的具体情况，特别是：
- Functions列表是否显示了函数？
- 环境变量是否已设置？
- 部署日志中是否有错误？

这样我可以更准确地帮你解决问题。










































