# 贡献指南

感谢您对 GaiYa每日进度条 项目的关注！我们欢迎任何形式的贡献。

## 🌟 贡献方式

### 1. 报告 Bug

如果您发现了 bug，请：

1. 在 [Issues](https://github.com/jiamizhongshifu/jindutiao/issues) 中搜索是否已有相关问题
2. 如果没有，创建新 Issue，包含：
   - 问题描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（操作系统、Python版本等）
   - 日志文件（如果有）

### 2. 提出功能建议

1. 在 [Discussions](https://github.com/jiamizhongshifu/jindutiao/discussions) 中讨论您的想法
2. 解释为什么需要这个功能
3. 提供可能的实现方案（可选）

### 3. 提交代码

#### 准备工作

```bash
# Fork 本仓库到您的账号

# 克隆您 fork 的仓库
git clone https://github.com/YOUR_USERNAME/jindutiao.git
cd jindutiao

# 添加上游仓库
git remote add upstream https://github.com/jiamizhongshifu/jindutiao.git

# 安装依赖
pip install -r requirements.txt
```

#### 开发流程

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行开发**
   - 遵循现有代码风格
   - 添加必要的注释
   - 确保代码可以正常运行

3. **测试您的更改**
   ```bash
   python main.py  # 测试主程序
   pyinstaller Gaiya.spec  # 测试打包
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加xxx功能"
   ```

   **提交信息规范**：
   - `feat`: 新功能
   - `fix`: Bug修复
   - `docs`: 文档更新
   - `style`: 代码格式调整
   - `refactor`: 重构
   - `test`: 测试相关
   - `chore`: 构建/工具相关

5. **推送到您的仓库**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 在 GitHub 上打开 Pull Request
   - 描述您的更改内容
   - 关联相关 Issue（如果有）

## 📋 代码规范

### Python 代码风格

- 遵循 PEP 8
- 使用有意义的变量名和函数名
- 函数/类添加文档字符串
- 复杂逻辑添加注释

示例：
```python
def calculate_progress(current_time: datetime, total_seconds: int) -> float:
    """
    计算当前进度百分比
    
    Args:
        current_time: 当前时间
        total_seconds: 一天的总秒数
        
    Returns:
        float: 进度百分比（0.0 - 1.0）
    """
    # 实现逻辑...
    pass
```

### 文件组织

- UI相关代码放在 `gaiya/ui/`
- 核心逻辑放在 `gaiya/core/`
- 工具函数放在 `gaiya/utils/`
- API函数放在 `api/`

## 🎨 UI/UX 贡献

- 遵循现有的设计风格
- 确保在不同分辨率下正常显示
- 考虑无障碍访问（辅助功能）
- 提供前后对比截图

## 📚 文档贡献

- 修正拼写错误
- 改进表述清晰度
- 添加使用示例
- 翻译文档

## 🐛 调试技巧

### 查看日志

日志文件：`gaiya.log`

```python
import logging
logging.debug("调试信息")
logging.info("一般信息")
logging.warning("警告")
logging.error("错误")
```

### 打包调试

如果修改代码后需要测试打包版本：

```bash
# 清理旧文件
rm -rf build dist

# 重新打包
pyinstaller Gaiya.spec

# 运行
./dist/GaiYa-v1.5.exe
```

**重要**：详见 [PyInstaller开发方法论](PYINSTALLER_DEVELOPMENT_METHODOLOGY.md)

## ❓ 需要帮助？

- 加入微信群讨论（见关于页面二维码）
- 在 Discussions 中提问
- 查看现有 Issues 和 Pull Requests

## 📜 行为准则

- 尊重所有贡献者
- 提供建设性反馈
- 专注于问题本身，而非个人
- 欢迎新手，耐心解答问题

## 🙏 致谢

感谢每一位贡献者的付出！您的名字将出现在贡献者列表中。

---

再次感谢您的贡献！❤️
