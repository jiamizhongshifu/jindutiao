# 🚀 Vercel 部署指南

## 问题诊断

### ❌ 之前的问题
- `/locales/*.json` 文件返回 404 错误
- 语言切换功能无法正常工作
- Vercel 误识别项目为 Flask 应用(因为根目录有 main.py)

### 🔍 根本原因
1. **Vercel 框架检测问题**:
   - Vercel 在构建时扫描根目录,发现 `main.py` 后尝试部署为 Flask 应用
   - 导致构建失败: "Error: No flask entrypoint found"

2. **配置文件冲突**:
   - `vercel.json` 中的 `outputDirectory` 和 `rewrites` 与 Root Directory 设置冲突
   - 导致路径叠加错误 (如 `/public/public/locales/zh_CN.json`)

### ✅ 解决方案

#### 关键步骤 1: 在 Vercel Dashboard 设置 Root Directory
**这是最关键的一步!** 必须在 Vercel 项目设置中手动配置:

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择你的项目 (jindutiao)
3. Settings → General
4. **Root Directory** 设置为: `public`
5. 点击 Save 保存

#### 关键步骤 2: 简化 vercel.json 配置
保持 `vercel.json` 配置最小化,仅包含必要的 headers:
```json
{
  "headers": [
    {
      "source": "/locales/(.*)",
      "headers": [
        {
          "key": "Content-Type",
          "value": "application/json; charset=utf-8"
        },
        {
          "key": "Cache-Control",
          "value": "public, max-age=3600, must-revalidate"
        }
      ]
    }
  ]
}
```

#### 工作原理
```
Vercel 构建流程:
1. 读取 Root Directory = "public" (从 Dashboard 设置)
2. 仅扫描 public/ 目录内容 (忽略根目录的 Python 文件)
3. 将 public/ 作为网站根目录部署
4. public/locales/zh_CN.json → https://www.gaiyatime.com/locales/zh_CN.json ✅
```

---

## 📋 部署步骤

### 方法 1: 自动部署(推荐)

如果你的 GitHub 仓库已连接到 Vercel:

1. **提交并推送代码**
   ```bash
   git add vercel.json VERCEL_DEPLOYMENT.md
   git commit -m "fix: 修复 Vercel 配置,正确提供静态资源"
   git push origin main
   ```

2. **等待 Vercel 自动部署**
   - 登录 [Vercel Dashboard](https://vercel.com/dashboard)
   - 查看部署状态(通常 1-2 分钟完成)
   - 等待显示 "Ready" 状态

3. **验证部署**
   - 访问: https://www.gaiyatime.com/locales/zh_CN.json
   - 应该看到 JSON 内容,而不是 404

---

## ✅ 部署后验证清单

### 1. 检查 JSON 文件可访问性

在浏览器中访问:
- ✅ https://www.gaiyatime.com/locales/zh_CN.json - 应返回中文翻译
- ✅ https://www.gaiyatime.com/locales/en_US.json - 应返回英文翻译

### 2. 测试语言切换功能

1. 打开 https://www.gaiyatime.com
2. 打开浏览器控制台(F12)
3. 应该看到:
   ```
   [i18n] Loaded translations for zh_CN
   [i18n] Initialized with locale: zh_CN
   ```
4. 点击语言切换按钮
5. 页面应自动刷新并切换到对应语言
6. 不应出现 "Missing translation" 警告

---

## 🎉 成功标志

当一切正常时:

1. ✅ https://www.gaiyatime.com/locales/zh_CN.json - 返回 JSON 内容
2. ✅ https://www.gaiyatime.com/locales/en_US.json - 返回 JSON 内容
3. ✅ 控制台显示 `[i18n] Loaded translations for zh_CN`
4. ✅ 点击语言切换按钮后页面自动刷新
5. ✅ 所有文本正确切换到对应语言
6. ✅ 没有 "Missing translation" 警告
7. ✅ 没有 404 错误
