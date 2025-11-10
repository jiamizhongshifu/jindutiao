"""
文字颜色修复工具

自动将浅色背景下的白色文字改为深色文字。

用法：
    from gaiya.ui.text_color_fixer import fix_text_color

    # 自动检测背景并修复文字颜色
    label.setStyleSheet(fix_text_color(label.styleSheet()))
"""

import re
from gaiya.ui.theme_light import LightTheme as Theme


def fix_text_color(stylesheet: str, keep_white: bool = False) -> str:
    """
    修复样式表中的白色文字颜色

    Args:
        stylesheet: 原始样式表
        keep_white: 是否保留白色（用于深色背景的卡片）

    Returns:
        修复后的样式表
    """
    if keep_white:
        return stylesheet

    # 替换 color: white
    stylesheet = re.sub(
        r'color:\s*white;',
        f'color: {Theme.TEXT_PRIMARY};',
        stylesheet,
        flags=re.IGNORECASE
    )

    # 替换 color: #fff
    stylesheet = re.sub(
        r'color:\s*#fff;',
        f'color: {Theme.TEXT_PRIMARY};',
        stylesheet,
        flags=re.IGNORECASE
    )

    # 替换 color: rgba(255, 255, 255, x) 为深色半透明
    def replace_white_rgba(match):
        alpha = match.group(1)
        # 将白色半透明改为黑色半透明
        return f'color: rgba(51, 51, 51, {alpha});'

    stylesheet = re.sub(
        r'color:\s*rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([\d.]+)\s*\);',
        replace_white_rgba,
        stylesheet,
        flags=re.IGNORECASE
    )

    return stylesheet


def get_hint_text_style() -> str:
    """获取提示文字样式（灰色小字）"""
    return f"color: {Theme.TEXT_HINT}; font-size: {Theme.FONT_SMALL}px;"


def get_title_style() -> str:
    """获取标题样式"""
    return f"font-size: {Theme.FONT_TITLE}px; font-weight: bold; color: {Theme.TEXT_PRIMARY};"


def get_subtitle_style() -> str:
    """获取副标题样式"""
    return f"font-size: {Theme.FONT_SUBTITLE}px; font-weight: bold; color: {Theme.TEXT_SECONDARY};"


def get_body_style() -> str:
    """获取正文样式"""
    return f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_BODY}px;"


def get_groupbox_title_style() -> str:
    """获取分组框标题样式"""
    return f"QGroupBox::title {{ color: {Theme.TEXT_SECONDARY}; font-weight: bold; font-size: {Theme.FONT_SUBTITLE}px; }}"
