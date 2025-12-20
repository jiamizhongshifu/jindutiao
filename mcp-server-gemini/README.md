# Gemini Image MCP Server

一个 MCP（Model Context Protocol）服务器，桥接 Google Gemini 的图像生成功能到 Claude Code。

## ✨ 功能特性

- 🎨 **文本生成图像**: 使用自然语言描述生成精美图像
- ✏️ **图像编辑**: 使用自然语言指令修改现有图像
- 🔧 **图像恢复**: 恢复和增强旧照片或损坏图像
- 🎭 **多种艺术风格**: 支持 10+ 种艺术风格（照片、水彩、油画、素描等）
- 📏 **灵活尺寸**: 支持多种图像尺寸（256x256 到 1792x1024）
- 🔄 **批量生成**: 一次生成多张变体图像

## 📋 前置要求

1. **Node.js 20+** 和 npm
2. **Gemini API Key**: 从 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取
3. **Claude Code**: 已安装并配置

## 🚀 快速开始

### 1. 安装依赖

```bash
cd mcp-server-gemini
npm install
```

### 2. 构建项目

```bash
npm run build
```

### 3. 配置环境变量

创建 `.env` 文件（或在系统环境变量中设置）:

```bash
# Gemini API Key（必需）
GEMINI_API_KEY=your_gemini_api_key_here

# 可选配置
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image  # 或 gemini-3-pro-image-preview
GEMINI_OUTPUT_DIR=C:\Users\YourName\gemini-images  # 输出目录
```

### 4. 配置 Claude Code

编辑 Claude Code 的 MCP 配置文件:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

添加以下配置:

```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "node",
      "args": [
        "C:\\Users\\Sats\\Downloads\\jindutiao\\mcp-server-gemini\\dist\\index.js"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_IMAGE_MODEL": "gemini-2.5-flash-image",
        "GEMINI_OUTPUT_DIR": "C:\\Users\\Sats\\gemini-images"
      }
    }
  }
}
```

### 5. 重启 Claude Code

重启 Claude Code 以加载新的 MCP 服务器。

## 💡 使用方法

### 在 Claude Code 中使用

MCP 服务器会自动向 Claude Code 提供以下工具：

#### 1. 生成图像 (`gemini_generate_image`)

```
请使用 Gemini 生成一张"日落时分的富士山，水彩画风格"的图像
```

高级选项:
```
生成 4 张不同风格的咖啡店室内图像：
- 风格：photorealistic, watercolor, sketch, minimalist
- 尺寸：1024x1024
- 保存到文件
```

#### 2. 编辑图像 (`gemini_edit_image`)

```
使用 Gemini 编辑图像 "my_photo.png"：
- 给照片中的人添加墨镜
- 保存为 PNG 格式
```

#### 3. 恢复图像 (`gemini_restore_image`)

```
使用 Gemini 恢复旧照片 "old_family_photo.jpg"：
- 移除划痕
- 提升清晰度
- 增强色彩
```

## 🎨 支持的艺术风格

| 风格 | 描述 |
|------|------|
| `photorealistic` | 照片级真实感 |
| `watercolor` | 水彩画风格 |
| `oil-painting` | 油画风格 |
| `sketch` | 手绘素描 |
| `pixel-art` | 像素艺术 |
| `anime` | 动漫风格 |
| `vintage` | 复古风格 |
| `modern` | 现代风格 |
| `abstract` | 抽象艺术 |
| `minimalist` | 极简主义 |

## 📏 支持的图像尺寸

- `256x256` - 小尺寸
- `512x512` - 中等尺寸
- `1024x1024` - 标准正方形
- `1792x1024` - 宽屏横向
- `1024x1792` - 宽屏纵向

## 🍌 模型选择

### 默认模型: `gemini-2.5-flash-image`
- 快速生成
- 高质量输出
- 推荐日常使用

### Pro 模型: `gemini-3-pro-image-preview`
- 更高质量
- 更强大的图像理解
- 更精准的编辑

设置环境变量切换模型:
```bash
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview
```

## 📂 输出文件

生成的图像默认保存在:
- **Windows**: `C:\Users\YourName\gemini-images`
- **macOS/Linux**: `~/gemini-images`

可通过 `GEMINI_OUTPUT_DIR` 环境变量自定义。

文件命名格式:
```
gemini_mountain_landscape_2025-12-20_1.png
gemini_edited_add_sunglasses_2025-12-20_1.png
gemini_restored_remove_scratches_2025-12-20_1.png
```

## 🔧 开发模式

```bash
# 监听文件变化自动重新编译
npm run watch

# 开发模式启动（编译 + 运行）
npm run dev
```

## 🐛 调试

服务器日志输出到标准错误流（stderr），可以在 Claude Code 的日志中查看：

```
[Gemini MCP Server] Starting...
[Gemini MCP Server] Using model: gemini-2.5-flash-image
[Gemini MCP Server] Output directory: C:\Users\Sats\gemini-images
[Gemini MCP Server] Server started successfully
[Gemini Image] Generating 1 image(s) with prompt: mountain landscape...
[Gemini Image] Saved: C:\Users\Sats\gemini-images\gemini_mountain_landscape_2025-12-20_1.png
```

## ⚠️ 注意事项

1. **API 配额**: Gemini API 有使用配额限制，请查看 [Google AI Studio](https://makersuite.google.com/app/apikey) 配额信息
2. **图像质量**: 生成质量取决于提示词的详细程度和所选模型
3. **文件大小**: 高分辨率图像会占用较多磁盘空间
4. **网络连接**: 需要稳定的网络连接访问 Gemini API

## 📖 API 参考

### `gemini_generate_image`

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `prompt` | string | ✅ | 图像描述提示词 |
| `count` | number | ❌ | 生成数量 (1-8) |
| `size` | string | ❌ | 图像尺寸 |
| `style` | string | ❌ | 艺术风格 |
| `seed` | number | ❌ | 随机种子 |
| `format` | string | ❌ | 输出格式 (png/jpeg) |
| `saveToFile` | boolean | ❌ | 是否保存到文件 |
| `outputFilename` | string | ❌ | 自定义文件名 |

### `gemini_edit_image`

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `image` | string | ✅ | 图像路径或 base64 |
| `instruction` | string | ✅ | 编辑指令 |
| `format` | string | ❌ | 输出格式 (png/jpeg) |
| `saveToFile` | boolean | ❌ | 是否保存到文件 |
| `outputFilename` | string | ❌ | 自定义文件名 |

### `gemini_restore_image`

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `image` | string | ✅ | 图像路径或 base64 |
| `instruction` | string | ✅ | 恢复指令 |
| `format` | string | ❌ | 输出格式 (png/jpeg) |
| `saveToFile` | boolean | ❌ | 是否保存到文件 |
| `outputFilename` | string | ❌ | 自定义文件名 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Google Gemini AI](https://ai.google.dev/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code](https://claude.ai/code)
- [GaiYa 每日进度条](https://github.com/jiamizhongshifu/jindutiao)

---

**Created with ❤️ by GaiYa Team**
