# 部署与发布指南

## API密钥管理方案

### 问题背景

在对外发布应用时，需要解决以下问题：
1. **新用户体验**：新用户打开应用时应能立即使用AI功能，无需手动配置
2. **密钥安全**：不能泄露API密钥，防止滥用
3. **灵活性**：允许用户使用自己的API密钥（如果他们有自己的账户）

### 解决方案

我们采用**三层密钥管理策略**：

#### 1. 内置默认密钥（新用户）

**用途**：为没有配置密钥的新用户提供免费额度

**实现方式**：
- 在打包时通过环境变量 `PYDAYBAR_DEFAULT_API_KEY` 设置
- 使用base64编码增加基本混淆（非加密，仅防止明文暴露）
- 密钥存储在 `api_key_manager.py` 模块中

**安全性**：
- ✅ 密钥不直接暴露在代码中
- ✅ 使用环境变量传递，打包时注入
- ✅ 限制免费额度，防止滥用
- ⚠️ 注意：用户仍可能通过反编译获取，但需要一定技术能力

#### 2. 用户自定义密钥（高级用户）

**用途**：允许用户使用自己的API密钥，享受更多额度

**实现方式**：
- 在应用目录创建 `.env` 文件
- 用户可以配置自己的 `TUZI_API_KEY`
- 优先级高于默认密钥

**创建方式**：
```bash
# Windows
echo TUZI_API_KEY=your_api_key_here > .env

# Linux/macOS
echo "TUZI_API_KEY=your_api_key_here" > .env
```

#### 3. 密钥优先级

```
用户自定义密钥 > 内置默认密钥 > 无密钥（错误）
```

### 配置加载流程

```
启动应用
    ↓
检查 .env 文件是否存在
    ↓
是 ──────────→ 加载用户密钥
    ↓
否
    ↓
检查内置默认密钥
    ↓
存在 ──────────→ 使用默认密钥（免费额度）
    ↓
不存在
    ↓
显示错误提示，引导用户配置
```

### 打包配置

#### 方法1：环境变量方式（推荐）

在打包前设置环境变量：

```bash
# Windows PowerShell
$env:PYDAYBAR_DEFAULT_API_KEY="base64:你的base64编码的API密钥"

# Linux/macOS
export PYDAYBAR_DEFAULT_API_KEY="base64:你的base64编码的API密钥"

# 然后打包
pyinstaller --clean --noconfirm PyDayBar.spec
```

**Base64编码示例**：
```python
import base64
api_key = "sk-your-actual-api-key"
encoded = base64.b64encode(api_key.encode('utf-8')).decode('utf-8')
print(f"base64:{encoded}")  # 输出: base64:c2steW91ci1hY3R1YWwtYXBpLWtleQ==
```

#### 方法2：直接嵌入（不推荐，但简单）

修改 `api_key_manager.py`，直接设置：

```python
# api_key_manager.py
def get_default_api_key(self) -> Optional[str]:
    # 直接返回密钥（简单但不安全）
    return "sk-your-actual-api-key"
```

**⚠️ 警告**：这种方式密钥会直接暴露在代码中，容易被提取。

### 创建专用API密钥（推荐）

**最佳实践**：
1. 在兔子API平台创建一个**专用的应用密钥**
2. 设置合理的**免费额度限制**（例如：每日100次请求）
3. 监控使用情况，防止滥用
4. 定期轮换密钥

**密钥配置建议**：
- **名称**：`PyDayBar-App-Default`
- **额度**：每日100次任务规划（足够大多数用户使用）
- **限制**：仅允许特定IP或域名（如果API支持）

### 新用户首次运行流程

```
1. 用户下载并运行 PyDayBar-v1.4.exe
   ↓
2. 应用启动，检查 .env 文件
   ↓
3. .env 不存在，使用内置默认密钥
   ↓
4. AI服务自动启动，显示"✓ 今日剩余: X 次规划"
   ↓
5. 用户可以直接使用AI功能（免费额度）
```

### 用户自定义密钥配置

如果用户想要使用自己的密钥：

1. **创建 `.env` 文件**
   - 位置：与 `PyDayBar-v1.4.exe` 同目录
   - 内容：`TUZI_API_KEY=your_api_key_here`

2. **重启应用**
   - 应用会自动检测并使用用户密钥
   - 优先级高于默认密钥

3. **验证配置**
   - 打开配置管理器 → 任务管理标签页
   - 查看配额状态，应该显示用户的配额

### 安全建议

1. **默认密钥管理**
   - ✅ 使用独立的API密钥账户
   - ✅ 设置合理的额度限制
   - ✅ 定期监控使用情况
   - ✅ 设置告警机制（超出限额时通知）

2. **密钥存储**
   - ✅ 使用环境变量而非硬编码
   - ✅ 在生产环境中使用加密存储
   - ⚠️ 避免在Git仓库中提交密钥

3. **密钥轮换**
   - 定期更换默认密钥（每3-6个月）
   - 发布新版本时更新密钥
   - 通知用户更新应用

4. **防止滥用**
   - 限制每个IP的请求频率
   - 监控异常使用模式
   - 设置每日/每月限额

### 配置文件示例

#### `.env` 文件（用户自定义）

```env
# PyDayBar API配置
TUZI_API_KEY=sk-your-api-key-here
TUZI_BASE_URL=https://api.tu-zi.com/v1
```

#### `.env.example`（示例文件，不包含真实密钥）

```env
# PyDayBar API配置示例
# 复制此文件为 .env 并填入您的API密钥

TUZI_API_KEY=your_api_key_here
TUZI_BASE_URL=https://api.tu-zi.com/v1
```

### 常见问题

**Q: 用户如何知道可以使用自己的密钥？**

A: 在配置管理器中显示提示：
- "💡 提示：您可以创建 `.env` 文件使用自己的API密钥，享受更多额度"

**Q: 如何防止默认密钥被滥用？**

A: 
- 设置API平台的额度限制
- 监控使用情况
- 使用IP白名单（如果支持）
- 定期轮换密钥

**Q: 密钥会被反编译提取吗？**

A: 
- 是的，有一定技术能力的用户可能提取
- 但通过base64编码和环境变量可以增加难度
- 最重要的防护是API平台的额度限制和监控

**Q: 新版本如何更新密钥？**

A: 
- 发布新版本时，在打包脚本中更新环境变量
- 旧的密钥会自动失效（如果设置了过期时间）
- 用户无需手动更新

### 实施步骤

1. **准备默认密钥**
   ```bash
   # 创建专用API密钥，设置合理额度
   # 记录密钥字符串
   ```

2. **编码密钥**
   ```python
   import base64
   key = "sk-your-key"
   encoded = base64.b64encode(key.encode()).decode()
   print(f"base64:{encoded}")
   ```

3. **打包时设置环境变量**
   ```bash
   # Windows
   $env:PYDAYBAR_DEFAULT_API_KEY="base64:..."
   pyinstaller --clean --noconfirm PyDayBar.spec
   ```

4. **测试新用户流程**
   - 在没有`.env`文件的环境中运行
   - 验证AI服务能够正常启动
   - 验证配额显示正常

5. **发布**
   - 打包完成
   - 在干净的测试环境中验证
   - 发布给用户

### 总结

通过三层密钥管理策略：
- ✅ 新用户无需配置即可使用
- ✅ 支持用户自定义密钥
- ✅ 基本的安全保护措施
- ✅ 灵活的部署选项

这样既保证了用户体验，又提供了基本的安全保障。

