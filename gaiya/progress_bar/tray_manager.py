"""
GaiYa Progress Bar - Tray Manager
系统托盘图标和菜单管理模块

从 main.py 提取，提高代码可维护性。
"""
import logging
from typing import TYPE_CHECKING, Optional, Callable

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QAction, QIcon

# Type checking only import to avoid circular imports
if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

# i18n support
try:
    from i18n import tr
except ImportError:
    def tr(key, fallback=None, **kwargs):
        return fallback or key


class TrayManager:
    """系统托盘图标和菜单管理器。

    负责创建和管理系统托盘图标、右键菜单及其交互。
    通过回调函数与主窗口通信，保持松耦合。

    Attributes:
        tray_icon: QSystemTrayIcon 实例
        edit_mode_action: 编辑模式菜单项
        save_edit_action: 保存编辑菜单项
        cancel_edit_action: 取消编辑菜单项
        focus_work_action: 开启专注模式菜单项
        adjust_focus_action: 调整专注时长菜单项
        end_focus_action: 结束专注菜单项
        skip_break_action: 跳过休息菜单项
    """

    # 托盘菜单样式
    MENU_STYLE = """
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 6px;
            padding: 6px 0;
        }
        QMenu::item {
            padding: 8px 30px 8px 20px;
            color: #333333;
        }
        QMenu::item:selected {
            background-color: #F5F5F5;
        }
        QMenu::separator {
            height: 1px;
            background-color: #E0E0E0;
            margin: 8px 12px;
        }
    """

    def __init__(self, parent: 'QWidget', logger: Optional[logging.Logger] = None):
        """初始化托盘管理器。

        Args:
            parent: 父窗口（用于获取样式和作为菜单父对象）
            logger: 日志记录器实例
        """
        self._parent = parent
        self._logger = logger or logging.getLogger(__name__)

        # 托盘图标和菜单
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._tray_menu: Optional[QMenu] = None

        # 动态菜单项引用
        self.edit_mode_action: Optional[QAction] = None
        self.save_edit_action: Optional[QAction] = None
        self.cancel_edit_action: Optional[QAction] = None
        self.focus_work_action: Optional[QAction] = None
        self.adjust_focus_action: Optional[QAction] = None
        self.end_focus_action: Optional[QAction] = None
        self.skip_break_action: Optional[QAction] = None

        # 回调函数（由主窗口设置）
        self._callbacks = {}

    def set_callback(self, name: str, callback: Callable) -> None:
        """设置回调函数。

        Args:
            name: 回调名称
            callback: 回调函数
        """
        self._callbacks[name] = callback

    def set_callbacks(self, callbacks: dict) -> None:
        """批量设置回调函数。

        Args:
            callbacks: 回调函数字典 {name: callback}
        """
        self._callbacks.update(callbacks)

    def _get_callback(self, name: str) -> Optional[Callable]:
        """获取回调函数。"""
        return self._callbacks.get(name)

    def init_tray(self) -> None:
        """初始化系统托盘图标和菜单。"""
        self.tray_icon = QSystemTrayIcon(self._parent)

        # 设置图标
        self._setup_icon()

        # 创建菜单
        self._create_menu()

        # 绑定点击事件
        self.tray_icon.activated.connect(self._on_activated)

        self.tray_icon.show()
        self._logger.info("系统托盘初始化完成")

    def _setup_icon(self) -> None:
        """设置托盘图标。"""
        from gaiya.utils.path_utils import get_resource_path

        icon_path = get_resource_path("gaiya-logo2-wbk.png")
        icon = QIcon(str(icon_path))

        if icon.isNull():
            # 使用Qt内置图标作为后备
            icon = self._parent.style().standardIcon(
                self._parent.style().StandardPixmap.SP_ComputerIcon
            )
            self._logger.warning("自定义图标加载失败，使用默认图标")

        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(tr('tray.tooltip'))

    def _create_menu(self) -> None:
        """创建托盘右键菜单。"""
        self._tray_menu = QMenu()
        self._tray_menu.setStyleSheet(self.MENU_STYLE)

        # === 编辑模式相关 ===
        self.edit_mode_action = QAction(tr('menu.edit_task_time'), self._parent)
        self.edit_mode_action.triggered.connect(
            lambda: self._invoke_callback('toggle_edit_mode')
        )
        self._tray_menu.addAction(self.edit_mode_action)

        self.save_edit_action = QAction(tr('menu.save_changes'), self._parent)
        self.save_edit_action.triggered.connect(
            lambda: self._invoke_callback('save_edit_changes')
        )
        self.save_edit_action.setVisible(False)
        self._tray_menu.addAction(self.save_edit_action)

        self.cancel_edit_action = QAction(tr('menu.cancel_edit'), self._parent)
        self.cancel_edit_action.triggered.connect(
            lambda: self._invoke_callback('cancel_edit')
        )
        self.cancel_edit_action.setVisible(False)
        self._tray_menu.addAction(self.cancel_edit_action)

        self._tray_menu.addSeparator()

        # === 配置和功能 ===
        config_action = QAction(tr('menu.config'), self._parent)
        config_action.triggered.connect(
            lambda: self._invoke_callback('open_config_gui')
        )
        self._tray_menu.addAction(config_action)

        time_review_action = QAction("⏰ 今日时间回放", self._parent)
        time_review_action.triggered.connect(
            lambda: self._invoke_callback('show_time_review_window')
        )
        self._tray_menu.addAction(time_review_action)

        # === 专注模式相关 ===
        self.focus_work_action = QAction("🔥 开启红温专注仓", self._parent)
        self.focus_work_action.triggered.connect(
            lambda: self._invoke_callback('start_focus_from_tray')
        )
        self._tray_menu.addAction(self.focus_work_action)

        self.adjust_focus_action = QAction("⏱️ 调整专注时长", self._parent)
        self.adjust_focus_action.triggered.connect(
            lambda: self._invoke_callback('adjust_focus_duration')
        )
        self.adjust_focus_action.setVisible(False)
        self._tray_menu.addAction(self.adjust_focus_action)

        self.end_focus_action = QAction("⏹️ 结束专注", self._parent)
        self.end_focus_action.triggered.connect(
            lambda: self._invoke_callback('end_focus_mode')
        )
        self.end_focus_action.setVisible(False)
        self._tray_menu.addAction(self.end_focus_action)

        self.skip_break_action = QAction("⏭️ 跳过休息", self._parent)
        self.skip_break_action.triggered.connect(
            lambda: self._invoke_callback('skip_break')
        )
        self.skip_break_action.setVisible(False)
        self._tray_menu.addAction(self.skip_break_action)

        # === 统计和编辑器 ===
        statistics_action = QAction(tr('menu.statistics'), self._parent)
        statistics_action.triggered.connect(
            lambda: self._invoke_callback('show_statistics')
        )
        self._tray_menu.addAction(statistics_action)

        scene_editor_action = QAction(tr('menu.scene_editor'), self._parent)
        scene_editor_action.triggered.connect(
            lambda: self._invoke_callback('open_scene_editor')
        )
        self._tray_menu.addAction(scene_editor_action)

        self._tray_menu.addSeparator()

        # === 系统操作 ===
        reload_action = QAction(tr('menu.reload_config'), self._parent)
        reload_action.triggered.connect(
            lambda: self._invoke_callback('reload_all')
        )
        self._tray_menu.addAction(reload_action)

        self._tray_menu.addSeparator()

        quit_action = QAction(tr('menu.quit'), self._parent)
        quit_action.triggered.connect(QApplication.quit)
        self._tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(self._tray_menu)

    def _invoke_callback(self, name: str) -> None:
        """调用回调函数。"""
        callback = self._get_callback(name)
        if callback:
            callback()
        else:
            self._logger.warning(f"未设置回调函数: {name}")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """托盘图标点击事件处理。

        Args:
            reason: 点击类型
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._logger.info("托盘图标左键点击：打开配置管理器")
            self._invoke_callback('open_config_gui')
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._logger.info("托盘图标双击：打开配置管理器")
            self._invoke_callback('open_config_gui')

    def update_for_edit_mode(self, in_edit_mode: bool) -> None:
        """更新编辑模式相关菜单项可见性。

        Args:
            in_edit_mode: 是否处于编辑模式
        """
        if self.edit_mode_action:
            self.edit_mode_action.setText(
                tr('menu.exit_edit_mode') if in_edit_mode else tr('menu.edit_task_time')
            )
        if self.save_edit_action:
            self.save_edit_action.setVisible(in_edit_mode)
        if self.cancel_edit_action:
            self.cancel_edit_action.setVisible(in_edit_mode)

    def update_for_focus_mode(self, in_focus_mode: bool, is_break: bool = False) -> None:
        """更新专注模式相关菜单项可见性。

        Args:
            in_focus_mode: 是否处于专注模式
            is_break: 是否处于休息阶段
        """
        if self.focus_work_action:
            self.focus_work_action.setVisible(not in_focus_mode)
        if self.adjust_focus_action:
            self.adjust_focus_action.setVisible(in_focus_mode and not is_break)
        if self.end_focus_action:
            self.end_focus_action.setVisible(in_focus_mode)
        if self.skip_break_action:
            self.skip_break_action.setVisible(in_focus_mode and is_break)

    def show_message(self, title: str, message: str,
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
                     duration: int = 5000) -> None:
        """显示托盘通知消息。

        Args:
            title: 标题
            message: 消息内容
            icon: 图标类型
            duration: 显示时长（毫秒）
        """
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, duration)

    def cleanup(self) -> None:
        """清理资源。"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        self._tray_menu = None
        self._logger.info("托盘管理器资源已清理")
