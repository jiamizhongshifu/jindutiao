# Vercel部署大小限制问题修复

## 问题

部署时报错：`A Serverless Function has exceeded the unzipped maximum size of 250 MB`

## 原因

Vercel Serverless Functions有250MB的解压后大小限制。如果`requirements.txt`包含不必要的依赖或版本过大，会导致函数包超过限制。

## 解决方案

### 1. 优化依赖（已完成）

确保`api/requirements.txt`只包含必要的依赖：

```
requests==2.31.0
```

**注意：**
- ❌ 不要包含`openai`（我们使用`requests`直接调用API）
- ❌ 不要包含其他不必要的库
- ✅ 只包含`requests`用于HTTP请求

### 2. 检查其他可能的问题

如果仍然超过限制，检查：

1. **项目根目录是否有大文件**
   - 确保`.gitignore`排除了不必要的文件
   - 检查是否有大型数据文件被包含

2. **Python版本**
   - Vercel自动检测Python版本
   - 如果使用Python 3.12，标准库可能较大

3. **依赖版本**
   - 使用固定版本号（如`requests==2.31.0`）
   - 避免使用`latest`或`*`

### 3. 进一步优化（如果仍然太大）

如果仍然超过250MB，可以考虑：

1. **使用更轻量的HTTP库**
   - `urllib3`（Python标准库）
   - 但`requests`通常更小且更易用

2. **检查Vercel Pro**
   - Vercel Pro计划可能有更大的限制
   - 但免费版应该足够

3. **使用Railway替代**
   - Railway没有严格的函数大小限制
   - 但Vercel免费版应该足够

## 验证

部署成功后，检查：
- Functions列表是否正常显示
- API端点是否正常工作
- 日志中是否有其他错误

