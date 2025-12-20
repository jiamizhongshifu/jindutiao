# Gemini Image MCP Server - 完整设置指南

## 📖 概述

本 MCP 服务器桥接了 Google Gemini 的图像生成功能到 Claude Code，让你可以在 Claude Code 中直接使用 Gemini 的强大图像能力。

### 功能特性

- ✅ **文本生成图像** - 使用自然语言描述生成精美图像
- ✅ **图像编辑** - 用自然语言指令修改现有图像
- ✅ **图像恢复** - 恢复和增强旧照片
- ✅ **10+ 艺术风格** - 照片、水彩、油画、素描、像素艺术、动漫等
- ✅ **多种尺寸** - 256x256 到 1792x1024
- ✅ **批量生成** - 一次生成多张变体

---

## 🚀 快速开始（5 分钟）

### 第 1 步：获取 Gemini API Key

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 点击 **Create API Key**
3. 复制生成的 API Key（格式：`AIzaSyxxxxxx...`）

### 第 2 步：安装和构建

```bash
cd C:\Users\Sats\Downloads\jindutiao\mcp-server-gemini

# 安装依赖
npm install

# 构建项目
npm run build
```

### 第 3 步：配置环境变量

复制并编辑 `.env` 文件：

```bash
# 复制模板
copy .env.example .env

# 编辑 .env，填写真实的 API Key
notepad .env
```

`.env` 内容：
```bash
GEMINI_API_KEY=你的_真实_API_Key
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
GEMINI_OUTPUT_DIR=C:\Users\Sats\gemini-images
```

### 第 4 步：测试 API 连接（可选但推荐）

```bash
node test.js
```

**预期输出**：
```
========================================
Gemini Image MCP Server - 测试工具
========================================

✅ API Key 已找到: AIzaSyxxxx...
✅ 使用模型: gemini-2.5-flash-image
✅ 输出目录: C:\Users\Sats\gemini-images

========================================
开始测试 Gemini API 连接...
========================================

1️⃣ 测试 API 连接...
✅ API 连接成功！

========================================
✅ 所有测试通过！
========================================
```

### 第 5 步：配置 Claude Code

#### 找到配置文件位置

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

**完整路径示例**:
```
C:\Users\Sats\AppData\Roaming\Claude\claude_desktop_config.json
```

#### 编辑配置文件

如果文件不存在，创建新文件并添加以下内容：

```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "node",
      "args": [
        "C:\\Users\\Sats\\Downloads\\jindutiao\\mcp-server-gemini\\dist\\index.js"
      ],
      "env": {
        "GEMINI_API_KEY": "你的_真实_API_Key",
        "GEMINI_IMAGE_MODEL": "gemini-2.5-flash-image",
        "GEMINI_OUTPUT_DIR": "C:\\Users\\Sats\\gemini-images"
      }
    }
  }
}
```

**⚠️ 重要**:
- 替换 `你的_真实_API_Key` 为实际的 Gemini API Key
- 使用 **双反斜杠** `\\` 作为路径分隔符（Windows）
- 如果配置文件已存在其他 MCP 服务器，只需添加 `gemini-image` 部分

#### 如果配置文件已存在

将 `gemini-image` 配置添加到现有的 `mcpServers` 对象中：

```json
{
  "mcpServers": {
    "existing-server": {
      ...现有配置...
    },
    "gemini-image": {
      "command": "node",
      "args": [
        "C:\\Users\\Sats\\Downloads\\jindutiao\\mcp-server-gemini\\dist\\index.js"
      ],
      "env": {
        "GEMINI_API_KEY": "你的_API_Key",
        "GEMINI_IMAGE_MODEL": "gemini-2.5-flash-image",
        "GEMINI_OUTPUT_DIR": "C:\\Users\\Sats\\gemini-images"
      }
    }
  }
}
```

### 第 6 步：重启 Claude Code

**完全关闭** Claude Code（确保进程已结束），然后重新启动。

---

## ✅ 验证安装

### 测试 1：生成简单图像

在 Claude Code 中输入：

```
请使用 Gemini 生成一张"日落时分的富士山"图像
```

**预期响应**：
```json
{
  "message": "Successfully generated 1 image(s)",
  "filePaths": [
    "C:\\Users\\Sats\\gemini-images\\gemini_sunset_fuji_mountain_2025-12-20_1.png"
  ],
  "enhancedPrompt": "日落时分的富士山, high quality, detailed, professional"
}
```

### 测试 2：查看生成的图像

打开文件资源管理器：
```
C:\Users\Sats\gemini-images\
```

你应该看到刚刚生成的图像文件！

---

## 🎨 使用示例

### 示例 1：生成不同风格的图像

```
请使用 Gemini 生成 4 张"咖啡店室内"图像，分别使用以下风格：
1. photorealistic（照片级）
2. watercolor（水彩画）
3. sketch（素描）
4. minimalist（极简）
```

### 示例 2：编辑现有图像

```
使用 Gemini 编辑我的照片 "C:\Users\Sats\Pictures\portrait.jpg"：
- 给人物添加墨镜
- 改变背景为海滩场景
- 增强色彩饱和度
```

### 示例 3：恢复旧照片

```
使用 Gemini 恢复这张旧照片 "C:\Users\Sats\Pictures\old_family_1980.jpg"：
- 移除划痕和污渍
- 修复撕裂部分
- 提升清晰度
- 增强色彩
```

### 示例 4：批量生成变体

```
请使用 Gemini 生成 6 张"科技公司 Logo"图像，要求：
- 简洁现代的设计
- 使用蓝色和灰色配色
- 适合作为应用图标
```

---

## 📚 可用工具详解

### 1. `gemini_generate_image` - 生成图像

**基本用法**：
```
生成一张 [描述] 的图像
```

**高级参数**：
- **count**: 生成数量（1-8）
- **size**: 图像尺寸（256x256, 512x512, 1024x1024, 1792x1024, 1024x1792）
- **style**: 艺术风格（见下方风格列表）
- **seed**: 随机种子（用于可复现生成）
- **format**: 输出格式（png, jpeg）

**支持的艺术风格**：
- `photorealistic` - 照片级真实感
- `watercolor` - 水彩画
- `oil-painting` - 油画
- `sketch` - 手绘素描
- `pixel-art` - 像素艺术
- `anime` - 动漫风格
- `vintage` - 复古风格
- `modern` - 现代风格
- `abstract` - 抽象艺术
- `minimalist` - 极简主义

### 2. `gemini_edit_image` - 编辑图像

**基本用法**：
```
编辑图像 [文件路径]：[编辑指令]
```

**示例**：
```
编辑 "C:\Users\Sats\photo.png"：
- 添加太阳眼镜
- 改变背景为海滩
```

### 3. `gemini_restore_image` - 恢复图像

**基本用法**：
```
恢复图像 [文件路径]：[恢复指令]
```

**示例**：
```
恢复 "C:\Users\Sats\old_photo.jpg"：
- 移除划痕
- 提升清晰度
- 修复撕裂
```

---

## 🔧 高级配置

### 使用 Pro 模型（更高质量）

编辑 `.env` 或 Claude 配置中的 `GEMINI_IMAGE_MODEL`：

```bash
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview
```

**差异**：
- **Flash 模型** (`gemini-2.5-flash-image`): 快速，适合日常使用
- **Pro 模型** (`gemini-3-pro-image-preview`): 更高质量，更精准的图像理解

### 自定义输出目录

修改 `GEMINI_OUTPUT_DIR`：

```bash
GEMINI_OUTPUT_DIR=D:\MyImages\GeminiOutput
```

### 开发模式

监听文件变化自动重新编译：

```bash
npm run watch
```

---

## 🐛 故障排除

### 问题 1：API Key 错误

**错误信息**：
```
Error: Gemini API key not found
```

**解决方法**：
1. 检查 `.env` 文件是否存在
2. 确认 API Key 已正确填写（无多余空格）
3. 检查 `claude_desktop_config.json` 中的 API Key
4. 重启 Claude Code

### 问题 2：模块未找到

**错误信息**：
```
Error: Cannot find module 'dist/index.js'
```

**解决方法**：
```bash
cd C:\Users\Sats\Downloads\jindutiao\mcp-server-gemini
npm run build
```

### 问题 3：Claude Code 看不到工具

**可能原因**：
- 配置文件路径错误
- 配置文件格式错误
- 未重启 Claude Code

**解决方法**：
1. 检查 `claude_desktop_config.json` 路径：
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```
2. 验证 JSON 格式（使用 [JSONLint](https://jsonlint.com/)）
3. **完全关闭** Claude Code（任务管理器确认）
4. 重新启动 Claude Code

### 问题 4：生成失败或超时

**可能原因**：
- 网络连接问题
- API 配额已用尽
- 提示词过于复杂

**解决方法**：
1. 检查网络连接
2. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 查看配额
3. 简化提示词
4. 尝试使用更小的图像尺寸

### 问题 5：生成的图像质量不佳

**优化建议**：
1. 使用更详细的提示词
2. 切换到 Pro 模型（`gemini-3-pro-image-preview`）
3. 指定艺术风格
4. 增加图像尺寸

---

## 📁 文件结构

```
mcp-server-gemini/
├── src/
│   ├── index.ts              # MCP 服务器主入口
│   ├── imageGenerator.ts     # Gemini API 调用逻辑
│   └── types.ts              # TypeScript 类型定义
├── dist/                     # 编译后的 JavaScript（自动生成）
├── node_modules/             # 依赖包（自动生成）
├── .env                      # 环境变量配置（需手动创建）
├── .env.example              # 环境变量模板
├── .gitignore                # Git 忽略文件
├── package.json              # Node.js 项目配置
├── tsconfig.json             # TypeScript 配置
├── test.js                   # API 测试脚本
├── README.md                 # 完整文档
├── QUICKSTART.md             # 快速开始指南
└── claude_config_example.json # Claude 配置示例
```

---

## 🔗 相关资源

- **Gemini API**: https://ai.google.dev/
- **获取 API Key**: https://makersuite.google.com/app/apikey
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **Claude Code**: https://claude.ai/code
- **GaiYa 项目**: https://github.com/jiamizhongshifu/jindutiao

---

## 📝 更新日志

### v1.0.0 (2025-12-20)

- ✅ 初始版本发布
- ✅ 支持文本生成图像
- ✅ 支持图像编辑
- ✅ 支持图像恢复
- ✅ 支持 10+ 艺术风格
- ✅ 支持多种图像尺寸
- ✅ 支持批量生成

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

**Created with ❤️ by GaiYa Team**
