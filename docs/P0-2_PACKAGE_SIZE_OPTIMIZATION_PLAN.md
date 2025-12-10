# P0-2: 减少打包体积优化方案

## 当前状态分析

### 已有的优化措施 ✓
从 `Gaiya.spec` 文件可见,已经实施了以下优化:

1. **排除WebEngine模块** (~280MB)
   - QtWebEngineCore, QtWebEngineWidgets, QtWebEngineQuick
   - QtWebChannel, QtWebSockets, QtPdf, QtPdfWidgets

2. **排除QML/Quick相关** (~20MB)
   - QtQuick, QtQuickControls2, QtQuickWidgets, QtQml

3. **排除3D和多媒体** (~15MB)
   - QtQuick3D, Qt3D*, QtMultimedia

4. **排除设计和开发工具** (~10MB)
   - QtDesigner, QtUiTools, QtHelp

5. **排除其他Qt模块** (~10MB)
   - QtBluetooth, QtDataVisualization, QtPositioning, QtSensors, QtSerialPort, QtSql, QtTest, QtXml
   - **注意**: QtCharts 保留(用于统计报告趋势图)

6. **排除数据科学库**
   - matplotlib, scipy, pandas, sklearn, numpy.distutils

7. **排除其他GUI库**
   - tkinter, PyQt5, PyQt6

8. **排除测试和文档框架**
   - pytest, unittest, sphinx, docutils, jinja2, IPython, notebook, jupyter

### 当前配置问题

第207行: `upx=False` - **UPX压缩未启用** ❌

这是最大的优化机会!

---

## 优化方案

### 阶段1: 启用UPX压缩 (预期减少 25-30MB)

**目标**: 85MB → 58-62MB

**操作步骤**:

1. **下载UPX压缩工具**
   - 官网: https://github.com/upx/upx/releases
   - 下载最新版本 (如 upx-4.2.1-win64.zip)

2. **安装UPX**
   ```powershell
   # 方案A: 添加到系统PATH
   $env:PATH += ";C:\path\to\upx"

   # 方案B: 放到PyInstaller目录
   # 将upx.exe放到: venv\Lib\site-packages\PyInstaller\bootloader\Windows-64bit\
   ```

3. **修改Gaiya.spec**
   ```python
   exe = EXE(
       ...
       upx=True,  # 启用UPX压缩
       upx_exclude=[
           # 排除Qt核心库(可能导致崩溃)
           'Qt6Core.dll',
           'Qt6Gui.dll',
           'Qt6Widgets.dll',
       ],
       ...
   )
   ```

4. **重新打包**
   ```bash
   pyinstaller Gaiya.spec
   ```

**预期效果**:
- 可执行文件: 85MB → 60MB左右
- DLL文件: 整体压缩率约30%

---

### 阶段2: 排除更多未使用的PySide6模块 (预期减少 3-5MB)

检查并排除以下可能未使用的模块:

```python
excludes=[
    # 现有的excludes...

    # 新增排除
    'PySide6.QtNetwork',  # 如果只使用httpx,可排除Qt网络模块
    'PySide6.QtPrintSupport',  # 打印支持
    'PySide6.QtSvg',  # SVG支持(如果不使用.svg格式)
    'PySide6.QtOpenGL',  # OpenGL渲染(如果不需要)
    'PySide6.QtOpenGLWidgets',
]
```

**注意**: 需要逐一测试,确保不影响功能。

---

### 阶段3: 优化图片资源 (预期减少 3-7MB)

当前打包的图片资源:

```python
datas=[
    ('assets/markers/', 'assets/markers/'),  # 标记图片
    ('assets/checkmark.png', 'assets/'),
    ('kun.webp', '.'),
    ('kun.gif', '.'),
    ('kun_100x100.gif', '.'),
    ('qun.jpg', '.'),  # 微信二维码
    ('Gaiya-logo.png', '.'),
    ('Gaiya-logo-wbk.png', '.'),
    ('gaiya-logo2.png', '.'),
    ('gaiya-logo2-wbk.png', '.'),
]
```

**优化操作**:

1. **压缩PNG/JPG图片**
   - 使用工具: TinyPNG, ImageOptim, pngquant
   - 目标: 减少50-70%体积,保持视觉质量

2. **转换GIF为WebP**
   - kun.gif → kun.webp (已有)
   - 删除冗余的gif版本

3. **删除未使用的Logo版本**
   - 保留一个主Logo即可

---

### 阶段4: 优化场景资源 (预期减少 2-5MB)

```python
('scenes/default/', 'scenes/default/'),
```

**操作**:
1. 检查default场景中的图片资源
2. 压缩所有PNG/JPG图片
3. 移除未使用的场景文件

---

### 阶段5: 新增SVG图标资源 (新增 ~5KB)

我们在P0-1中创建了4个SVG图标,需要添加到打包:

```python
datas=[
    # 现有的datas...

    # 新增: 新手引导SVG图标
    ('assets/icons/', 'assets/icons/'),
]
```

**SVG优势**: 矢量格式,体积极小(每个仅1-2KB)

---

## 优化时间表

### Day 1: 分析当前打包内容 ✓
- 已完成spec文件分析
- 已识别优化机会

### Day 2-3: 排除未使用的PySide6模块
1. 测试排除 QtNetwork
2. 测试排除 QtPrintSupport
3. 测试排除 QtSvg (注意: FeatureCard使用了QSvgWidget!)
4. 测试排除 QtOpenGL

### Day 4: 应用UPX压缩
1. 下载并安装UPX
2. 修改spec文件启用UPX
3. 配置upx_exclude防止崩溃
4. 重新打包并测试

### Day 5: 优化图片资源
1. 压缩PNG/JPG图片
2. 删除冗余图片
3. 添加SVG图标到打包

### Day 6: 验证打包大小
1. 检查最终体积
2. 测试所有功能
3. 记录优化成果

---

## 预期成果

| 优化项 | 预期减少体积 | 累计体积 |
|--------|-------------|----------|
| 当前体积 | - | 85 MB |
| UPX压缩 | -25 MB | 60 MB |
| 排除PySide6模块 | -3 MB | 57 MB |
| 优化图片资源 | -5 MB | 52 MB |
| **最终目标** | **-33 MB** | **52-60 MB** |

**目标达成**: ✓ 55-60 MB范围内

---

## 风险评估

### 高风险 ⚠️
- **排除QtSvg**: FeatureCard组件使用QSvgWidget,不能排除!

### 中风险 ⚠️
- **UPX压缩Qt核心DLL**: 可能导致程序崩溃,需配置upx_exclude

### 低风险 ✓
- **排除QtNetwork**: 项目使用httpx,不依赖Qt网络
- **图片压缩**: 只要保持视觉质量即可

---

## 立即执行的操作

### 1. 检查QtSvg依赖
```python
# 在 feature_card.py 中:
from PySide6.QtSvgWidgets import QSvgWidget  # ← 依赖QtSvg!
```

**结论**: QtSvg **不能**排除!

### 2. 可以安全排除的模块
```python
excludes=[
    # ... 现有的 ...

    # ✅ 可以安全排除
    'PySide6.QtNetwork',  # 使用httpx替代
    'PySide6.QtPrintSupport',  # 无打印功能
    'PySide6.QtOpenGL',  # 无3D渲染
    'PySide6.QtOpenGLWidgets',
]
```

### 3. 必须保留的模块
```python
hiddenimports=[
    # ... 现有的 ...

    # ✅ 必须保留
    'PySide6.QtSvgWidgets',  # FeatureCard使用
    'PySide6.QtCharts',  # 统计报告使用
]
```

---

**下一步**: 开始执行P0-2.2任务,修改spec文件排除未使用的模块
