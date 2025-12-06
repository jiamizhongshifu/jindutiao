# GaiYa 打包指南

## 🚀 打包脚本说明

本项目提供了三种打包脚本,针对不同场景优化:

### 1. `build-smart.bat` - 智能打包系统 (推荐)

**特点**:
- ✅ **自动检测代码变化**,智能决定是否清理缓存
- ✅ **防止打包卡死**,带超时和自动重试机制
- ✅ **实时进度显示**,避免卡死假象
- ✅ **验证打包结果**,确保文件完整性
- ✅ **确保最新代码**,自动对比文件时间戳

**使用场景**:
- 首次打包
- 不确定是否需要清理缓存
- 打包经常卡死或失败
- 需要验证打包结果

**使用方法**:
```bash
build-smart.bat
```

**优势**:
- 首次打包: 60-90秒
- 增量打包: 10-20秒 (自动检测)
- 带重试机制,成功率高

---

### 2. `build-fast.bat` - 快速增量打包 (日常推荐)

**特点**:
- ✅ **智能缓存检测**,关键文件修改时自动清理
- ✅ **进度监控**,实时显示打包状态
- ✅ **自动结束占用进程**
- ✅ **文件大小验证**

**使用场景**:
- 日常开发中频繁打包
- 修改了少量代码
- 需要快速验证修改

**使用方法**:
```bash
build-fast.bat
```

**优势**:
- 首次打包: 60-90秒
- 使用缓存: 8-20秒 (提升 70-87%)
- 自动检测 main.py 和 membership_ui.py 是否修改

---

### 3. `build-clean.bat` - 完全清理重建

**特点**:
- ✅ **完全清理**所有缓存
- ✅ **确保干净环境**

**使用场景**:
- 修改了 Gaiya.spec 配置
- 添加/删除了依赖库
- 更新了 PySide6 版本
- 打包出现异常错误
- build-fast.bat 失败时

**使用方法**:
```bash
build-clean.bat
```

**优势**:
- 100% 确保打包最新代码
- 适合解决缓存导致的异常

---

## 📊 打包速度对比

| 场景 | build-clean | build-fast | build-smart |
|------|-------------|------------|-------------|
| 首次打包 | 60-90秒 | 60-90秒 | 60-90秒 |
| 修改 main.py | 60-90秒 | 60-90秒 (自动清理) | 60-90秒 (自动清理) |
| 修改 membership_ui.py | 60-90秒 | 60-90秒 (自动清理) | 60-90秒 (自动清理) |
| 修改其他 UI 代码 | 60-90秒 | 10-20秒 | 10-20秒 |
| 修改业务逻辑 | 60-90秒 | 15-25秒 | 15-25秒 |
| 仅修改注释/文档 | 60-90秒 | 8-15秒 | 8-15秒 |

## 🎯 推荐使用流程

### 日常开发流程:

1. **修改代码**
2. **运行** `build-fast.bat` (自动检测是否需要清理)
3. **测试 exe**
4. **如果有问题,运行** `build-clean.bat` **重试**

### 首次打包或重大修改:

1. **运行** `build-smart.bat`
2. **验证打包结果**
3. **测试 exe**

### 遇到问题时:

1. **运行** `build-clean.bat` **完全清理**
2. **如果还是失败,检查**:
   - 是否有杀毒软件占用文件
   - 是否有其他 Python 进程运行
   - 查看 `build.log` 错误信息

---

## 🔧 核心优化机制

### 1. 智能缓存检测

`build-fast.bat` 和 `build-smart.bat` 会自动检测关键文件的修改时间:

```batch
# 检查 main.py 是否比缓存更新
if exist build\Gaiya\main.pyc (
    for /f %%i in ('dir /b /od main.py build\Gaiya\main.pyc') do set NEWER=%%i
    if "!NEWER!"=="main.py" set NEED_CLEAN=1
)
```

**原理**:
- 对比源文件和 .pyc 缓存文件的修改时间
- 如果源文件更新,自动清理缓存
- 确保每次都打包最新代码

### 2. 进程管理

所有脚本都会:
1. 自动结束占用的 GaiYa-v1.6.exe 进程
2. 等待 1 秒确保文件释放
3. 然后再开始打包

**避免问题**:
- "文件被占用"错误
- 打包失败

### 3. 进度监控

`build-smart.bat` 实现了实时进度监控:

```batch
:wait_loop
timeout /t 5 /nobreak >nul
set /a ELAPSED+=5

# 检查打包进程是否还在运行
tasklist /FI "IMAGENAME eq pyinstaller.exe" 2>NUL | find "pyinstaller.exe">NUL
if "%ERRORLEVEL%"=="1" goto :build_done

# 显示当前阶段
if !ELAPSED! EQU 15 echo    ... 处理模块钩子...
```

**优势**:
- 用户知道打包在正常进行
- 不会误以为卡死

### 4. 超时和重试

`build-smart.bat` 支持:
- 打包超时检测(默认 180 秒)
- 自动重试机制(最多 2 次)
- 超时自动终止卡死进程

---

## 🐛 常见问题

### Q1: 打包后运行 exe,发现代码没更新?

**原因**: PyInstaller 使用了旧的缓存

**解决**:
1. 运行 `build-clean.bat` 完全清理
2. 或者删除 `build` 和 `dist` 目录
3. 重新打包

### Q2: 打包一直卡在某个阶段?

**原因**: 可能是进程卡死或杀毒软件扫描

**解决**:
1. 使用 `build-smart.bat`,带自动超时处理
2. 关闭杀毒软件或添加白名单
3. 手动终止 python.exe 进程后重试

### Q3: build-fast.bat 没有检测到代码修改?

**原因**: 修改的文件不在检测列表中

**解决**:
1. 运行 `build-clean.bat` 强制清理
2. 或者手动删除 `build` 目录

**优化**: 编辑 `build-fast.bat`,添加更多文件检测:
```batch
# 检查 config_gui.py 是否更新
if exist "build\Gaiya\config_gui.pyc" (
    for /f %%i in ('dir /b /od config_gui.py build\Gaiya\config_gui.pyc') do set NEWER=%%i
    if "!NEWER!"=="config_gui.py" set NEED_CLEAN=1
)
```

### Q4: 如何确认打包包含了最新代码?

**方法 1**: 检查文件时间戳
```bash
dir /T:W dist\GaiYa-v1.6.exe
```
时间应该是刚刚打包的时间

**方法 2**: 检查 xref 文件
```bash
findstr /C:"membership_ui" build\Gaiya\xref-Gaiya.html
```
应该能找到 membership_ui 模块

**方法 3**: 运行 exe 并检查日志
```bash
# 查看日志文件
notepad %APPDATA%\GaiYa\gaiya.log
```
应该能看到最新的日志输出

---

## 📝 总结

- **日常开发**: 使用 `build-fast.bat` (自动检测,快速打包)
- **首次打包**: 使用 `build-smart.bat` (带验证和重试)
- **遇到问题**: 使用 `build-clean.bat` (完全清理)

**核心原则**:
1. 修改关键文件(main.py, membership_ui.py)时自动清理缓存
2. 修改其他文件时利用缓存加速
3. 确保每次都打包最新代码
4. 防止打包卡死和失败

---

## 🔍 验证清单

打包完成后,请检查:

- [ ] exe 文件大小 80-120 MB (正常范围)
- [ ] exe 生成时间是当前时间
- [ ] 运行 exe,检查功能是否正常
- [ ] 检查日志文件,确认 logging 配置生效
- [ ] 如果修改了支付功能,测试支付流程

**支付功能验证** (针对本次修复):
1. 运行 exe 并创建支付订单
2. 打开 `%APPDATA%\GaiYa\gaiya.log`
3. 扫码支付并完成
4. 观察日志中应出现:
   ```
   [MEMBERSHIP] Started payment polling for order: GAIYA...
   [MEMBERSHIP] Checking payment status for order: GAIYA...
   [MEMBERSHIP] Payment detected as paid!
   ```
5. 应用应在 3-10 秒内自动识别支付成功
