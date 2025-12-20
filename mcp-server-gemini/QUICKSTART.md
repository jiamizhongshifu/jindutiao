# 🚀 Gemini Image MCP Server - 快速开始

5 分钟内开始使用 Gemini 图像生成功能！

## 📋 准备工作

### 1. 获取 Gemini API Key

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 点击 **Create API Key**
3. 复制生成的 API Key（格式类似 `AIzaSyxxxxxx...`）

### 2. 检查环境

确保已安装:
- ✅ Node.js 20+ (`node --version`)
- ✅ npm (`npm --version`)
- ✅ Claude Code

## 🛠️ 安装步骤

### 步骤 1: 安装依赖

```bash
cd C:\Users\Sats\Downloads\jindutiao\mcp-server-gemini
npm install
```

### 步骤 2: 构建项目

```bash
npm run build
```

**预期输出**:
```
> mcp-server-gemini-image@1.0.0 build
> tsc

[构建成功，生成 dist/ 目录]
```

### 步骤 3: 配置环境变量

复制环境变量模板:
```bash
copy .env.example .env
```

编辑 `.env` 文件:
```bash
GEMINI_API_KEY=你的_API_Key_在这里
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
GEMINI_OUTPUT_DIR=C:\Users\Sats\gemini-images
```

### 步骤 4: 配置 Claude Code

#### Windows 配置路径:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**完整路径示例**:
```
C:\Users\Sats\AppData\Roaming\Claude\claude_desktop_config.json
```

#### 编辑配置文件:

如果文件不存在，创建新文件:
```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "node",
      "args": [
        "C:\\Users\\Sats\\Downloads\\jindutiao\\mcp-server-gemini\\dist\\index.js"
      ],
      "env": {
        "GEMINI_API_KEY": "你的_API_Key_在这里",
        "GEMINI_IMAGE_MODEL": "gemini-2.5-flash-image",
        "GEMINI_OUTPUT_DIR": "C:\\Users\\Sats\\gemini-images"
      }
    }
  }
}
```

**⚠️ 重要**: 将 `你的_API_Key_在这里` 替换为真实的 Gemini API Key！

如果文件已存在，添加 `gemini-image` 配置到 `mcpServers` 对象中。

### 步骤 5: 重启 Claude Code

完全关闭并重新启动 Claude Code 以加载新的 MCP 服务器。

## ✅ 验证安装

### 测试 1: 生成简单图像

在 Claude Code 中输入:

```
请使用 Gemini 生成一张"日落时分的富士山"图像
```

**预期响应**:
```json
{
  "message": "Successfully generated 1 image(s)",
  "filePaths": [
    "C:\\Users\\Sats\\gemini-images\\gemini_sunset_fuji_mountain_2025-12-20_1.png"
  ],
  "enhancedPrompt": "日落时分的富士山, high quality, detailed, professional"
}
```

### 测试 2: 查看生成的图像

打开文件资源管理器:
```
C:\Users\Sats\gemini-images\
```

你应该看到生成的图像文件！

## 🎨 使用示例

### 示例 1: 生成多种风格的图像

```
请使用 Gemini 生成 3 张"咖啡店室内"图像：
- 第一张：photorealistic 风格
- 第二张：watercolor 风格
- 第三张：sketch 风格
```

### 示例 2: 编辑现有图像

```
使用 Gemini 编辑图像 "C:\Users\Sats\Pictures\my_photo.png"：
- 给照片中的人添加墨镜
- 改变背景为海滩场景
```

### 示例 3: 恢复旧照片

```
使用 Gemini 恢复旧照片 "C:\Users\Sats\Pictures\old_family_photo.jpg"：
- 移除划痕和污渍
- 提升清晰度
- 增强色彩饱和度
```

## 🐛 常见问题

### 问题 1: "Gemini API key not found"

**原因**: API Key 未正确配置

**解决方法**:
1. 检查 `.env` 文件是否存在
2. 检查 `claude_desktop_config.json` 中的 `GEMINI_API_KEY`
3. 确保 API Key 没有多余的空格或引号

### 问题 2: "Cannot find module"

**原因**: 未运行构建

**解决方法**:
```bash
cd C:\Users\Sats\Downloads\jindutiao\mcp-server-gemini
npm run build
```

### 问题 3: Claude Code 看不到 Gemini 工具

**原因**: 配置未生效或未重启

**解决方法**:
1. 完全关闭 Claude Code（确保进程已结束）
2. 检查 `claude_desktop_config.json` 路径和格式
3. 重新启动 Claude Code

### 问题 4: 生成失败或超时

**原因**: 网络问题或 API 配额限制

**解决方法**:
1. 检查网络连接
2. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 查看配额
3. 尝试使用更短的提示词

## 📖 下一步

- 查看 [README.md](README.md) 了解完整功能
- 尝试不同的艺术风格和尺寸
- 探索批量生成功能

## 🆘 需要帮助？

- 查看服务器日志: Claude Code 日志窗口
- 查看生成的图像: `C:\Users\Sats\gemini-images\`
- 提交 Issue: [GitHub Issues](https://github.com/jiamizhongshifu/jindutiao/issues)

---

**祝你使用愉快！** 🎉
