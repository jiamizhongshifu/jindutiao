# 🚀 Vercel 部署指南

## 问题诊断

### ❌ 之前的问题
- `/locales/*.json` 文件返回 404 错误
- 语言切换功能无法正常工作

### 🔍 根本原因
Vercel 配置文件(`vercel.json`)缺少关键配置:
1. **没有指定输出目录**: Vercel 不知道从 `public/` 目录提供静态文件
2. **没有配置 JSON 文件的响应头**: 可能导致 MIME 类型错误

### ✅ 解决方案
已更新 `vercel.json`,添加了:
- `outputDirectory: "public"` - 告诉 Vercel 从 `public/` 目录提供文件
- `headers` 配置 - 为 JSON 文件设置正确的 Content-Type 和缓存策略

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
   - 访问: https://gaiya.cloud/locales/zh_CN.json
   - 应该看到 JSON 内容,而不是 404

---

## ✅ 部署后验证清单

### 1. 检查 JSON 文件可访问性

在浏览器中访问:
- ✅ https://gaiya.cloud/locales/zh_CN.json - 应返回中文翻译
- ✅ https://gaiya.cloud/locales/en_US.json - 应返回英文翻译

### 2. 测试语言切换功能

1. 打开 https://gaiya.cloud
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

1. ✅ https://gaiya.cloud/locales/zh_CN.json - 返回 JSON 内容
2. ✅ https://gaiya.cloud/locales/en_US.json - 返回 JSON 内容
3. ✅ 控制台显示 `[i18n] Loaded translations for zh_CN`
4. ✅ 点击语言切换按钮后页面自动刷新
5. ✅ 所有文本正确切换到对应语言
6. ✅ 没有 "Missing translation" 警告
7. ✅ 没有 404 错误
