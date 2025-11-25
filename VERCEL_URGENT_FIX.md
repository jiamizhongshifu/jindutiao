# 🚨 Vercel 404 紧急修复指南

## 当前问题
- ❌ https://www.gaiyatime.com/locales/zh_CN.json 返回 404
- ❌ https://www.gaiyatime.com/locales/en_US.json 返回 404
- ❌ 控制台显示: `Failed to load resource: the server responded with a status of 404`

## 🔍 根本原因

Vercel 的 `outputDirectory` 配置**不会改变项目的根目录**,而是指定构建输出目录。
对于静态网站,**必须在 Vercel Dashboard 中设置 Root Directory**。

---

## ✅ 立即修复 - 方案 1: 更改 Vercel 项目设置 (推荐)

### 步骤 1: 登录 Vercel Dashboard

1. 访问 https://vercel.com/dashboard
2. 找到你的项目 (gaiyatime 或类似名称)
3. 点击进入项目

### 步骤 2: 修改项目设置

1. 点击 **Settings** (设置)
2. 在左侧菜单选择 **General** (常规)
3. 找到 **Root Directory** 配置
4. 当前值可能是: `.` (根目录)
5. **修改为**: `public`
6. 点击 **Save** (保存)

### 步骤 3: 重新部署

1. 返回项目主页
2. 点击 **Deployments** (部署)
3. 找到最新的部署
4. 点击右侧的 **...** (三个点)
5. 选择 **Redeploy** (重新部署)
6. 等待 1-2 分钟

### 步骤 4: 验证修复

访问以下网址,应该看到 JSON 内容:
- https://www.gaiyatime.com/locales/zh_CN.json
- https://www.gaiyatime.com/locales/en_US.json

---

## ✅ 备选修复 - 方案 2: 移动文件到根目录

如果方案 1 不起作用,将 `public/` 目录下的所有文件移到项目根目录:

```bash
# 在本地执行
cd c:/Users/Sats/Downloads/jindutiao

# 将 public/ 的内容移到根目录
mv public/* .
mv public/.htaccess.example .

# 删除空的 public 目录
rmdir public

# 更新 vercel.json
# 删除 "outputDirectory": "public" 这一行

# 提交并推送
git add -A
git commit -m "fix: 将网站文件移至根目录以修复 Vercel 部署"
git push origin main
```

**注意**: 这会改变项目结构,需要更新 `.gitignore` 和其他配置。

---

## ✅ 备选修复 - 方案 3: 使用 vercel.json 的 routes 配置

如果你想保持 `public/` 结构,可以使用路由重写:

更新 `vercel.json`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/public/$1" }
  ]
}
```

但这种方法**不推荐**,因为会增加复杂性。

---

## 🎯 推荐方案对比

| 方案 | 难度 | 速度 | 推荐度 |
|------|------|------|--------|
| 方案 1: 修改 Root Directory | ⭐ 简单 | ⚡ 最快 | ✅✅✅ 强烈推荐 |
| 方案 2: 移动文件到根目录 | ⭐⭐ 中等 | ⚡⚡ 较快 | ⚠️ 需要改变项目结构 |
| 方案 3: 路由重写 | ⭐⭐⭐ 复杂 | ⚡⚡⚡ 慢 | ❌ 不推荐 |

---

## 📸 Vercel Dashboard 设置截图说明

当你登录 Vercel Dashboard 后:

1. **找到 Root Directory 设置**:
   ```
   Settings → General → Root Directory
   ```

2. **当前值**:
   ```
   .
   ```

3. **应该改为**:
   ```
   public
   ```

4. **保存后会看到**:
   ```
   ✓ Changes saved
   ```

---

## 🔧 验证步骤

### 1. 检查部署日志

在 Vercel Dashboard:
1. 点击最新的部署
2. 查看 **Build Logs**
3. 应该看到类似:
   ```
   Installing dependencies...
   Skipping (no dependencies)
   
   Build complete.
   Deploying...
   Deployment complete.
   ```

### 2. 测试 JSON 文件

在浏览器中访问:
```
https://www.gaiyatime.com/locales/zh_CN.json
```

**预期结果**: 看到 JSON 内容,开头类似:
```json
{
  "nav": {
    "home": "首页",
    "features": "功能",
    ...
  }
}
```

### 3. 测试语言切换

1. 访问 https://www.gaiyatime.com
2. 打开控制台 (F12)
3. 应该看到:
   ```
   [i18n] Loaded translations for zh_CN
   [i18n] Initialized with locale: zh_CN
   ```
4. 点击语言切换按钮
5. 页面自动刷新并切换语言

---

## ❓ 如果仍然 404

### 检查 1: Vercel 项目绑定的仓库分支

确保 Vercel 部署的是 `main` 分支:
1. Settings → Git → Production Branch
2. 应该是: `main`

### 检查 2: 清除 Vercel 缓存

1. Settings → Data Cache
2. 点击 **Purge Everything**
3. 重新部署

### 检查 3: 检查文件是否被 .gitignore

```bash
# 检查 locales 目录是否在 Git 中
git ls-files public/locales/

# 应该看到:
# public/locales/zh_CN.json
# public/locales/en_US.json
```

如果没有输出,说明文件没有提交到 Git!

```bash
# 添加文件
git add public/locales/*.json
git commit -m "fix: 确保翻译文件被提交"
git push origin main
```

---

## 📞 紧急联系

如果以上所有方法都不起作用:

1. **检查 Vercel 部署日志**
   - 复制完整的 Build Logs
   - 查找任何错误信息

2. **检查 Git 仓库**
   - 确认 `public/locales/` 目录存在
   - 确认 JSON 文件已提交

3. **验证本地服务器**
   ```bash
   cd public
   python -m http.server 8000
   ```
   访问 http://localhost:8000/locales/zh_CN.json
   如果本地能访问,说明文件没问题,是 Vercel 配置问题

---

## 🎉 成功标志

当修复成功后:

1. ✅ https://www.gaiyatime.com/locales/zh_CN.json - 返回 JSON
2. ✅ https://www.gaiyatime.com/locales/en_US.json - 返回 JSON  
3. ✅ 控制台显示 `[i18n] Loaded translations for zh_CN`
4. ✅ 语言切换按钮正常工作
5. ✅ 没有 404 错误
6. ✅ 没有 "Missing translation" 警告
