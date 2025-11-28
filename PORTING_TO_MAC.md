# GaiYa 移植到 macOS 指南 (PORTING_TO_MAC.md)

## 概述

本文档旨在指导开发者将 GaiYa 应用从 Windows 平台移植到 macOS 平台。GaiYa 的核心技术栈 (Python + PySide6) 天然支持跨平台，但仍需对操作系统特定的功能（如开机自启动、窗口底层操作）和打包配置进行适配。

本文档记录了使 GaiYa 代码库“Mac 就绪”所做的修改，并提供了在 macOS 环境中构建和测试的指导。

## 适配目标

*   **单一代码库**：维护同一份代码，同时支持 Windows 和 macOS。
*   **核心功能移植**：确保置顶、透明、点击穿透等核心功能在 macOS 上正常工作。
*   **开机自启动**：在 macOS 上实现开机自启动功能。
*   **打包发布**：能够在 macOS 上成功打包生成 `.app` 应用程序包。

## 已完成的适配工作 (Windows 环境)

以下工作已在 Windows 开发环境中完成，确保代码库具备 macOS 兼容性：

### 1. 跨平台开机自启动管理器 (`autostart_manager.py`)

*   **问题**：原始版本高度依赖 Windows 注册表 (`winreg`)。
*   **解决方案**：
    *   `autostart_manager.py` 已重构为**抽象工厂模式**。
    *   根据 `platform.system()` 动态加载 `WindowsStrategy` (使用 `winreg`) 或 `MacStrategy` (基于 `LaunchAgents .plist` 文件)。
    *   在非 Windows 环境中，`winreg` 模块不会被导入，避免了崩溃。
*   **代码位置**：`autostart_manager.py`

### 2. 跨平台窗口工具 (`gaiya/utils/window_utils.py`)

*   **问题**：`main.py` 中直接使用了 Windows API (`ctypes.windll.user32.SetWindowLongW` 等) 来实现窗口置顶和点击穿透。
*   **解决方案**：
    *   新建 `gaiya/utils/window_utils.py` 模块，封装了这些底层窗口操作。
    *   `set_always_on_top()` 和 `set_click_through()` 函数内部包含平台判断。
    *   **Windows 实现**：保留了原有的 `ctypes` 调用。
    *   **macOS 实现**：预留了 `pyobjc` 的调用框架，通过 `AppKit.NSWindow` 的方法来实现置顶和点击穿透。
*   **代码位置**：`gaiya/utils/window_utils.py`
*   **`main.py` 修改**：已修改 `main.py` 以调用 `window_utils` 中的函数，移除了所有硬编码的 Windows API 调用。

### 3. 智能打包配置 (`Gaiya.spec`)

*   **问题**：PyInstaller `.spec` 文件为 Windows 专属，无法生成 `.app`，图标格式和依赖导入也仅限于 Windows。
*   **解决方案**：
    *   `Gaiya.spec` 已重写，在文件头部引入 `platform` 模块。
    *   **动态 `hiddenimports`**：根据 `IS_WIN` 或 `IS_MAC` 条件，动态包含 `winreg` 或 `pyobjc` 相关的 macOS 库 (`objc`, `Foundation`, `AppKit`)。
    *   **动态图标**：根据平台选择 `.ico` (Windows) 或尝试 `.icns` (macOS)。
    *   **`.app` Bundle**：当在 macOS 环境中打包时，将自动创建 `BUNDLE` 配置块，生成标准的 `.app` 应用程序包。
*   **代码位置**：`Gaiya.spec`

## 在 macOS 环境中构建和测试

完成上述代码和配置修改后，您可以在 macOS 环境中执行以下步骤来构建和测试 GaiYa。

### 1. 环境准备

1.  **克隆代码库**：
    ```bash
    git clone https://github.com/jiamizhongshifu/jindutiao.git
    cd jindutiao
    ```
2.  **创建并激活虚拟环境** (推荐)：
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```
4.  **安装 macOS 特定依赖**：
    为了支持 `window_utils` 中的 macOS 功能，您需要安装 `pyobjc-framework-Cocoa`。
    ```bash
    pip install pyobjc-framework-Cocoa
    ```

### 2. 运行和调试

在 macOS 开发环境中，您可以直接运行 `main.py` 进行测试：

```bash
python main.py
```

### 3. 打包生成 `.app`

使用已修改的 `Gaiya.spec` 文件进行打包。PyInstaller 会自动识别 macOS 环境并生成 `.app` 包。

```bash
pyinstaller Gaiya.spec
```

*   成功后，您会在 `dist` 目录下找到 `GaiYa.app`。

### 4. macOS 独有注意事项

*   **图标 (`.icns`)**：
    *   目前 `Gaiya.spec` 会尝试查找 `gaiya-logo2.icns`。如果不存在，PyInstaller 可能仍然能打包（并使用默认图标或 `.ico` 格式，但可能带有警告）。
    *   **建议**：为您的应用准备一个高质量的 `.icns` 图标文件，并确保它与 `.spec` 文件位于同一目录或可被找到的路径。
*   **开机自启动**：
    *   测试 `autostart_manager` 是否正确生成 `~/Library/LaunchAgents/com.gaiya.autostart.plist`。
    *   验证应用是否在登录时启动。
*   **点击穿透**：
    *   在打包后的 `.app` 中测试点击穿透功能是否正常。
*   **Retina (高分屏) 支持**：PySide6 默认应支持，但请留意 UI 元素在 Retina 屏幕上的清晰度。
*   **应用签名 (Code Signing) 与公证 (Notarization)**：
    *   这是 macOS 用户信任和运行您的 `.app` 的关键。未签名/公证的应用在 macOS Catalina 及更高版本上打开时会收到“文件已损坏”或“无法验证开发者”的警告。
    *   要进行签名和公证，您需要一个 **Apple Developer Program** 订阅（每年 99 美元）。
    *   签名和公证是一个相对复杂的过程，通常涉及 Xcode command line tools、Apple Developer ID 证书和 `notarytool`。

## 结语

通过这些修改，GaiYa 已具备了良好的 macOS 兼容性。接下来的任务是在实际的 macOS 环境中进行全面测试、修复可能出现的 UI/UX 问题，并处理应用的签名与发布流程。

希望这份指南能帮助您顺利完成 macOS 版本的发布！
