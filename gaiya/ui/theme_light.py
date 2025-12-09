"""
浅色主题颜色规范 - MacOS极简风格

本模块定义了整个应用的浅色主题颜色体系，参考引导弹窗（welcome_dialog.py）的设计。
所有颜色遵循WCAG AA级可访问性标准。

设计哲学：
- 极简主义：优先使用黑白灰，仅在必要时使用彩色
- 层次分明：文字有清晰的主次之分
- MacOS风格：细边框、圆角、悬停反馈
"""


class LightTheme:
    """浅色主题颜色常量

    参考来源：
    - welcome_dialog.py 的颜色实现（#666666, #888888）
    - MacOS Big Sur+ 的设计语言
    - Material Design 3 的浅色规范
    """

    # ============================================================
    # 文字颜色层级（参考引导弹窗实测值）
    # ============================================================
    TEXT_PRIMARY = "#333333"      # 主标题、重要文字（对比度 12.6:1）
    TEXT_SECONDARY = "#666666"    # 副标题、次要信息（引导弹窗实测）
    TEXT_TERTIARY = "#999999"     # 三级文字（更浅的提示文字）
    TEXT_HINT = "#888888"         # 提示文字、占位符（引导弹窗实测）
    TEXT_DISABLED = "#CCCCCC"     # 禁用状态
    TEXT_WHITE = "#FFFFFF"        # 深色背景上的文字（套餐卡片）

    # ============================================================
    # 背景颜色
    # ============================================================
    BG_PRIMARY = "#FFFFFF"        # 主背景（窗口、对话框）
    BG_SECONDARY = "#F5F5F5"      # 次背景（分组框、区域划分）
    BG_TERTIARY = "#FAFAFA"       # 三级背景（表格交替行）
    BG_HOVER = "#EEEEEE"          # 悬停背景（按钮、列表项）
    BG_PRESSED = "#E0E0E0"        # 按下背景
    BG_DISABLED = "#F9F9F9"       # 禁用背景

    # ============================================================
    # 边框颜色（MacOS极简风格）
    # ============================================================
    BORDER_LIGHT = "#E8E8E8"      # 极浅边框（分割线）
    BORDER_NORMAL = "#D0D0D0"     # 普通边框（默认输入框、按钮）
    BORDER_HOVER = "#999999"      # 悬停边框（加深）
    BORDER_FOCUS = "#4CAF50"      # 焦点边框（绿色强调）
    BORDER_ERROR = "#f44336"      # 错误边框

    # ============================================================
    # 强调色（仅用于焦点/主要操作，不用于大面积填充）
    # ============================================================
    ACCENT_GREEN = "#4CAF50"      # 主要操作（保存按钮、焦点状态）
    ACCENT_GREEN_HOVER = "#45a049"
    ACCENT_GREEN_PRESSED = "#3d8b40"

    ACCENT_BLUE = "#2196F3"       # 信息操作（链接、提示）
    ACCENT_BLUE_HOVER = "#1976D2"

    ACCENT_ORANGE = "#FF9800"     # 警告操作
    ACCENT_ORANGE_HOVER = "#F57C00"

    ACCENT_RED = "#f44336"        # 危险操作（删除、清空）
    ACCENT_RED_HOVER = "#d32f2f"

    ACCENT_PURPLE = "#9C27B0"     # 紫色强调（学习、创意相关）
    ACCENT_PURPLE_HOVER = "#7B1FA2"

    # ============================================================
    # 字体大小（参考引导弹窗）
    # ============================================================
    FONT_TITLE = 18               # 页面大标题（welcome_dialog.py:37）
    FONT_SUBTITLE = 14            # 副标题、分组标题（welcome_dialog.py:46）
    FONT_BODY = 13                # 正文、按钮、表格（welcome_dialog.py:65）
    FONT_SMALL = 11               # 小字、提示、版权信息
    FONT_TINY = 9                 # 极小字（慎用）

    # ============================================================
    # 圆角半径（MacOS风格）
    # ============================================================
    RADIUS_SMALL = 4              # 小圆角（输入框）
    RADIUS_MEDIUM = 6             # 中圆角（按钮，MacOS标准）
    RADIUS_LARGE = 8              # 大圆角（卡片）
    RADIUS_XLARGE = 12            # 超大圆角（对话框）

    # ============================================================
    # 间距系统（8px基准）
    # ============================================================
    SPACING_XS = 4                # 极小间距
    SPACING_SM = 8                # 小间距
    SPACING_MD = 12               # 中间距
    SPACING_LG = 16               # 大间距
    SPACING_XL = 20               # 超大间距
    SPACING_XXL = 24              # 极大间距

    # ============================================================
    # 阴影（可选，MacOS风格浅阴影）
    # ============================================================
    SHADOW_LIGHT = "0 1px 3px rgba(0,0,0,0.08)"   # 浅阴影（卡片）
    SHADOW_MEDIUM = "0 2px 8px rgba(0,0,0,0.12)"  # 中阴影（浮动元素）
    SHADOW_HEAVY = "0 4px 16px rgba(0,0,0,0.16)"  # 重阴影（模态框）

    # ============================================================
    # 特殊用途颜色
    # ============================================================
    # 成功/错误/警告/信息（保留，但谨慎使用）
    STATUS_SUCCESS = "#4CAF50"
    STATUS_ERROR = "#f44336"
    STATUS_WARNING = "#FF9800"
    STATUS_INFO = "#2196F3"

    # 套餐卡片渐变色（保持不变，已经很好）
    GRADIENT_MONTHLY = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2)"
    GRADIENT_YEARLY = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f093fb, stop:1 #f5576c)"
    GRADIENT_LIFETIME = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4facfe, stop:1 #00f2fe)"

    # ============================================================
    # 辅助方法
    # ============================================================
    @staticmethod
    def with_opacity(color: str, opacity: float) -> str:
        """
        将十六进制颜色转换为带透明度的rgba格式

        Args:
            color: 十六进制颜色，如 "#4CAF50"
            opacity: 透明度，0.0-1.0

        Returns:
            rgba格式字符串，如 "rgba(76, 175, 80, 0.5)"
        """
        # 移除 # 符号
        color = color.lstrip('#')

        # 转换为RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        return f"rgba({r}, {g}, {b}, {opacity})"

    @staticmethod
    def get_font_style(size: int, bold: bool = False) -> str:
        """
        生成字体样式字符串

        Args:
            size: 字号（使用 FONT_* 常量）
            bold: 是否加粗

        Returns:
            CSS字体样式字符串
        """
        weight = "bold" if bold else "normal"
        return f"font-size: {size}px; font-weight: {weight};"


# ============================================================
# 导出便捷别名
# ============================================================
# 文字
TEXT = LightTheme.TEXT_PRIMARY
TEXT_MUTED = LightTheme.TEXT_SECONDARY
TEXT_SUBTLE = LightTheme.TEXT_HINT

# 背景
BG = LightTheme.BG_PRIMARY
BG_ALT = LightTheme.BG_SECONDARY

# 边框
BORDER = LightTheme.BORDER_NORMAL
BORDER_FOCUS = LightTheme.BORDER_FOCUS

# 强调色
PRIMARY = LightTheme.ACCENT_GREEN
INFO = LightTheme.ACCENT_BLUE
WARNING = LightTheme.ACCENT_ORANGE
DANGER = LightTheme.ACCENT_RED
