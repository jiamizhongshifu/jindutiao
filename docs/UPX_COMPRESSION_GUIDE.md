# UPX压缩配置说明

## 什么是UPX?

UPX (Ultimate Packer for eXecutables) 是一个强大的可执行文件压缩工具,可以显著减少打包后的文件大小。

**优势**:
- 压缩率: 通常可以减少30-50%的文件大小
- 运行时解压: 程序启动时自动解压到内存,对用户透明
- 跨平台: 支持Windows, Linux, macOS

**潜在问题**:
- 首次启动略慢(解压时间)
- 某些DLL压缩后可能导致程序崩溃
- 杀毒软件可能误报

---

## 安装UPX

### Windows

**方法1: 手动下载安装**

1. 访问UPX官方GitHub仓库:
   ```
   https://github.com/upx/upx/releases
   ```

2. 下载最新版本 (如 `upx-4.2.1-win64.zip`)

3. 解压到任意目录,例如:
   ```
   C:\Tools\upx\
   ```

4. 添加到系统PATH:
   ```powershell
   # 方案A: 临时添加(当前会话有效)
   $env:PATH += ";C:\Tools\upx"

   # 方案B: 永久添加
   # 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
   # 编辑用户变量Path,添加: C:\Tools\upx
   ```

5. 验证安装:
   ```bash
   upx --version
   ```

**方法2: 使用Chocolatey**

```powershell
# 安装Chocolatey (如果未安装)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装UPX
choco install upx
```

**方法3: 放到PyInstaller目录(无需PATH配置)**

将 `upx.exe` 复制到:
```
venv\Lib\site-packages\PyInstaller\bootloader\Windows-64bit\
```

PyInstaller会自动检测并使用。

---

### macOS

```bash
# 使用Homebrew安装
brew install upx

# 验证安装
upx --version
```

---

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install upx-ucl

# Fedora/RHEL
sudo dnf install upx

# Arch Linux
sudo pacman -S upx

# 验证安装
upx --version
```

---

## 配置说明

### Gaiya.spec 配置

```python
exe = EXE(
    ...
    upx=True,  # 启用UPX压缩
    upx_exclude=[
        # 排除Qt核心库,避免压缩后崩溃
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'Qt6Svg.dll',
        # 排除Python核心库
        'python*.dll',
        'vcruntime*.dll',
        # 排除SSL库
        'libcrypto*.dll',
        'libssl*.dll',
    ],
    ...
)
```

### 为什么要排除某些DLL?

1. **Qt核心库**:
   - 这些库经过特殊编译,压缩后可能导致段错误(Segmentation Fault)
   - 保持原始大小可确保稳定性

2. **Python核心库**:
   - `python3.dll` 包含关键运行时,压缩后可能影响性能
   - `vcruntime140.dll` 是Visual C++运行时,不应压缩

3. **SSL加密库**:
   - `libcrypto-*.dll` 和 `libssl-*.dll` 用于HTTPS通信
   - 压缩可能导致证书验证失败

---

## 使用方法

### 1. 确认UPX已安装

```bash
upx --version
# 输出示例:
# upx 4.2.1
# Copyright (C) 1996-2023 the UPX Team. All Rights Reserved.
```

### 2. 重新打包

```bash
# 方法1: 使用快速构建脚本
build-fast.bat

# 方法2: 完全重建
build-clean.bat

# 方法3: 手动打包
pyinstaller Gaiya.spec
```

### 3. 验证压缩效果

```bash
# 检查打包后的文件大小
dir dist\GaiYa-v1.6.exe

# 预期结果:
# 启用UPX前: ~85 MB
# 启用UPX后: ~58-62 MB
# 节省: ~25-30 MB (约30%压缩率)
```

### 4. 测试应用

**重要**: UPX压缩后必须进行完整功能测试!

测试清单:
- [ ] 应用正常启动
- [ ] 主窗口UI正常显示
- [ ] 配置界面可以打开
- [ ] 统计报告图表正常(QtCharts)
- [ ] 新手引导界面正常(FeatureCard SVG图标)
- [ ] AI生成对话框动画正常
- [ ] 场景编辑器功能正常
- [ ] 番茄钟面板正常
- [ ] 网络请求正常(httpx + SSL)

---

## 故障排除

### 问题1: PyInstaller找不到UPX

**症状**:
```
WARNING: Cannot find UPX. Please set environment variable UPX
```

**解决方案**:
```powershell
# 设置UPX路径环境变量
$env:UPX = "C:\Tools\upx\upx.exe"

# 或添加到系统PATH
$env:PATH += ";C:\Tools\upx"
```

---

### 问题2: 压缩后程序崩溃

**症状**:
- 程序启动后立即闪退
- 或显示"应用程序错误"对话框

**解决方案**:

1. **检查upx_exclude配置**:
   确保关键DLL已被排除

2. **逐步排查**:
   ```python
   # 临时禁用UPX,确认是压缩导致的问题
   upx=False
   ```

3. **添加更多排除项**:
   ```python
   upx_exclude=[
       'Qt6*.dll',  # 排除所有Qt库
       '*.dll',     # 极端情况:排除所有DLL(体积优化效果差)
   ]
   ```

---

### 问题3: 杀毒软件误报

**症状**:
- Windows Defender或其他杀毒软件报告病毒/木马
- 文件被自动删除或隔离

**原因**:
UPX压缩后的可执行文件经常被误报为恶意软件(False Positive)

**解决方案**:

1. **添加信任**:
   - Windows Defender: 添加到"排除项"
   - 其他杀毒软件: 添加到"白名单"

2. **代码签名**:
   - 购买代码签名证书(如Sectigo, DigiCert)
   - 对exe文件进行数字签名
   - 成本: ~$100-300/年

3. **提交样本**:
   - 向杀毒软件厂商提交误报样本
   - 等待白名单更新(1-7天)

---

### 问题4: 首次启动变慢

**症状**:
启动时间从2秒增加到5秒

**原因**:
UPX解压需要时间,尤其是大型应用

**权衡**:
- 文件体积减少30% ✓
- 启动时间增加1-3秒 ✗

**优化方案**:
1. 选择性压缩(排除大型DLL)
2. 使用SSD硬盘(减少I/O延迟)
3. 考虑用户体验是否可接受

---

## 最佳实践

### 1. 渐进式启用

不要一次性启用所有压缩,逐步测试:

```python
# 阶段1: 只压缩Python代码和小型库
upx=True
upx_exclude=['Qt6*.dll', '*.dll']

# 阶段2: 允许压缩非核心DLL
upx_exclude=['Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'python*.dll']

# 阶段3: 最终配置(当前Gaiya.spec)
upx_exclude=[
    'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'Qt6Svg.dll',
    'python*.dll', 'vcruntime*.dll',
    'libcrypto*.dll', 'libssl*.dll',
]
```

### 2. 完整测试

每次修改upx_exclude后,必须进行完整功能测试。

### 3. 版本控制

在Git commit中记录UPX配置变更:

```bash
git commit -m "feat(build): 启用UPX压缩,减少打包体积25MB"
```

### 4. 文档更新

在README.md中说明:
- 应用使用UPX压缩
- 如遇杀毒软件误报,如何处理
- 首次启动可能略慢

---

## 预期效果

### GaiYa项目

| 项目 | 启用前 | 启用后 | 节省 |
|------|--------|--------|------|
| 可执行文件 | 85 MB | 60 MB | 25 MB (29%) |
| 首次启动 | 2.5s | 4.0s | +1.5s |
| 功能完整性 | ✓ | ✓ | 无影响 |

**结论**: 体积优化显著,启动延迟可接受 ✓

---

## 参考资料

- UPX官网: https://upx.github.io/
- UPX GitHub: https://github.com/upx/upx
- PyInstaller文档: https://pyinstaller.org/en/stable/usage.html#upx-packing
- UPX FAQ: https://github.com/upx/upx/blob/devel/doc/upx.pod

---

**最后更新**: 2025-12-10
**配置版本**: P0-2.3
