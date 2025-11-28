# -*- coding: utf-8 -*-
"""
窗口工具函数
处理跨平台的窗口样式设置：置顶、透明、点击穿透等
"""
import platform
import logging
from typing import Any

logger = logging.getLogger(__name__)
SYSTEM = platform.system()

# Windows API 常量
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

def set_click_through(window_id: int, enable: bool = True):
    """
    设置窗口是否允许鼠标穿透
    
    Args:
        window_id: 窗口句柄 (QWidget.winId())
        enable: True开启穿透，False关闭穿透
    """
    if SYSTEM == "Windows":
        _set_click_through_windows(window_id, enable)
    elif SYSTEM == "Darwin":
        _set_click_through_mac(window_id, enable)
    else:
        logger.warning(f"当前系统 {SYSTEM} 暂不支持设置点击穿透")

def set_always_on_top(window_id: int, enable: bool = True):
    """
    设置窗口置顶
    注意：Qt本身的 WindowStaysOnTopHint 通常足够，但在某些系统下可能需要原生API辅助
    """
    if SYSTEM == "Windows":
        _set_always_on_top_windows(window_id, enable)
    # macOS 通常由 Qt 处理，暂不需要额外 API

def _set_click_through_windows(hwnd: int, enable: bool):
    """Windows 实现：修改窗口扩展样式"""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        # 获取当前样式
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        if enable:
            # 添加穿透样式
            new_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        else:
            # 移除穿透样式
            new_style = ex_style & ~WS_EX_TRANSPARENT
            
        if new_style != ex_style:
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            logger.debug(f"Windows窗口穿透设置: {'开启' if enable else '关闭'}")
            
    except Exception as e:
        logger.error(f"设置Windows点击穿透失败: {e}")

def _set_always_on_top_windows(hwnd: int, enable: bool):
    """Windows 实现：设置 TOPMOST 和相关样式"""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        if enable:
            # 1. SetWindowPos
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
            
            # 2. SetWindowLongW (设置 ToolWindow 和 NoActivate)
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex_style |= (WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
            
            logger.debug("已设置 Windows TOPMOST/TOOLWINDOW 属性")
            
    except Exception as e:
        logger.error(f"设置Windows置顶失败: {e}")

def _set_click_through_mac(ns_view_ptr: int, enable: bool):
    """macOS 实现：使用 Cocoa API"""
    try:
        # 动态导入，避免在非Mac环境报错
        import objc
        from AppKit import NSView, NSWindow
        
        # 将整数句柄转换为 objc 对象
        # 注意：PySide6 的 winId() 返回的是 NSView 指针
        ns_view = objc.objc_object(c_void_p=ns_view_ptr)
        
        # 获取对应的 NSWindow
        if hasattr(ns_view, 'window'):
            ns_window = ns_view.window()
        else:
            # 如果本身就是 window 或者无法获取
            logger.warning("无法从 view 获取 window")
            return

        if ns_window:
            # 设置 ignoresMouseEvents
            ns_window.setIgnoresMouseEvents_(enable)
            logger.debug(f"macOS窗口穿透设置: {'开启' if enable else '关闭'}")
        else:
            logger.warning("NSWindow 对象为空")
            
    except ImportError:
        # 这是一个常见情况，不应该总是 error，除非确实是在 Mac 上且没有库
        logger.warning("缺少 pyobjc 依赖，无法设置点击穿透 (非Mac环境请忽略)")
    except Exception as e:
        logger.error(f"设置macOS点击穿透失败: {e}")

def is_click_through_supported() -> bool:
    """检查当前环境是否支持点击穿透"""
    if SYSTEM == "Windows":
        return True
    elif SYSTEM == "Darwin":
        try:
            import objc
            return True
        except ImportError:
            return False
    return False