"""
GaiYa Config Modules - Account Manager
Handles account-related functionality including login, logout, and subscription management.

Extracted from config_gui.py to improve maintainability.
"""
import logging
from typing import Optional, Dict, Any, Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication


class AccountManager(QObject):
    """Manages account-related operations.

    Signals:
        login_success: Emitted when login succeeds (with user_info dict)
        logout_success: Emitted when logout completes
        subscription_updated: Emitted when subscription status is refreshed (with tier string)
        error: Emitted on any error (with error message)
    """

    # Signals for account events
    login_success = Signal(dict)  # user_info
    logout_success = Signal()
    subscription_updated = Signal(str)  # new_tier
    error = Signal(str)  # error_message

    def __init__(self, parent_widget: QWidget, auth_client=None, ai_client=None, i18n=None):
        """Initialize AccountManager.

        Args:
            parent_widget: Parent widget for dialogs
            auth_client: AuthClient instance for authentication operations
            ai_client: AI client instance for tier synchronization
            i18n: Internationalization translator instance
        """
        super().__init__(parent_widget)
        self._parent = parent_widget
        self._auth_client = auth_client
        self._ai_client = ai_client
        self._i18n = i18n

        # Worker references (prevent garbage collection)
        self._refresh_worker = None
        self._logout_worker = None
        self._loading_dialog = None

    def set_auth_client(self, auth_client):
        """Set or update the auth client instance.

        Args:
            auth_client: AuthClient instance
        """
        self._auth_client = auth_client

    def set_ai_client(self, ai_client):
        """Set or update the AI client instance.

        Args:
            ai_client: AI client instance
        """
        self._ai_client = ai_client

    def tr(self, key: str, **kwargs) -> str:
        """Translate a key using i18n if available.

        Args:
            key: Translation key
            **kwargs: Format arguments

        Returns:
            Translated string
        """
        if self._i18n:
            return self._i18n.tr(key, **kwargs)
        return key

    def get_user_email(self) -> str:
        """Get current user's email.

        Returns:
            User email or "未登录" if not logged in
        """
        if self._auth_client:
            return self._auth_client.get_user_email() or "未登录"
        return "未登录"

    def get_user_tier(self) -> str:
        """Get current user's tier.

        Returns:
            User tier string (e.g., "free", "pro", "lifetime")
        """
        if self._auth_client:
            return self._auth_client.get_user_tier()
        return "free"

    def is_logged_in(self) -> bool:
        """Check if user is logged in.

        Returns:
            True if logged in, False otherwise
        """
        if self._auth_client:
            return self._auth_client.is_logged_in()
        return False

    def show_login_dialog(self):
        """Display the login/registration dialog."""
        from gaiya.ui.auth_ui import AuthDialog

        # Create login dialog
        dialog = AuthDialog(self._parent, self._auth_client)

        # Connect login success signal
        dialog.login_success.connect(self._on_login_success)

        # Show dialog
        dialog.exec()

    def _on_login_success(self, user_info: dict):
        """Handle successful login.

        Args:
            user_info: User information dictionary
        """
        user_tier = user_info.get('user_tier', 'free')

        # Update AI client tier
        if self._ai_client:
            self._ai_client.user_tier = user_tier
            logging.info(f"[AccountManager] Updated ai_client.user_tier: {user_tier}")

        # Emit signal for parent to update UI
        self.login_success.emit(user_info)

        # Determine tier message
        if user_tier == 'free':
            tier_message = "您当前是免费用户。升级高级版可解锁更多功能。"
        elif user_tier == 'premium' or user_tier == 'pro':
            tier_message = "您是高级版用户，可以使用所有功能。"
        elif user_tier == 'lifetime':
            tier_message = "您是终身会员，尊享所有高级功能。"
        else:
            tier_message = "您的账户信息已更新。"

        # Show success message
        QMessageBox.information(
            self._parent,
            "登录成功",
            self.tr("config.membership.welcome_back", user_email=user_info.get('email', 'User')) + "\n"
            f"{tier_message}"
        )

    def refresh_account(self, on_complete: Callable = None):
        """Refresh account subscription status.

        Args:
            on_complete: Optional callback when refresh completes
        """
        from gaiya.core.async_worker import AsyncNetworkWorker

        if not self._auth_client:
            logging.error("[AccountManager] auth_client not initialized, cannot refresh")
            self.error.emit("认证客户端未初始化")
            return

        logging.info("[AccountManager] Refreshing subscription status...")

        # Show loading dialog
        self._loading_dialog = QMessageBox(self._parent)
        self._loading_dialog.setWindowTitle("刷新中")
        self._loading_dialog.setText("正在刷新会员状态,请稍候...")
        self._loading_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self._loading_dialog.setIcon(QMessageBox.Icon.Information)
        self._loading_dialog.show()

        # Force UI update
        QApplication.processEvents()

        # Store callback
        self._on_refresh_complete = on_complete

        # Create async worker
        self._refresh_worker = AsyncNetworkWorker(self._auth_client.get_subscription_status)
        self._refresh_worker.success.connect(self._on_refresh_success)
        self._refresh_worker.error.connect(self._on_refresh_error)
        self._refresh_worker.start()

    def _on_refresh_success(self, result: dict):
        """Handle successful subscription refresh.

        Args:
            result: API response with subscription status
        """
        # Close loading dialog
        if self._loading_dialog:
            self._loading_dialog.close()
            self._loading_dialog.deleteLater()
            self._loading_dialog = None
            QApplication.processEvents()

        if result.get("success"):
            user_tier = result.get("user_tier", "free")
            is_active = result.get("is_active", False)

            logging.info(f"[AccountManager] Subscription refreshed: tier={user_tier}, active={is_active}")

            # Update AI client tier
            if self._ai_client:
                self._ai_client.user_tier = user_tier
                logging.info(f"[AccountManager] Updated ai_client.user_tier: {user_tier}")

            # Emit signal
            self.subscription_updated.emit(user_tier)

            # Call completion callback
            if hasattr(self, '_on_refresh_complete') and self._on_refresh_complete:
                self._on_refresh_complete()

            QMessageBox.information(
                self._parent,
                "刷新成功",
                f"会员状态已更新！\n\n当前等级: {user_tier.upper()}"
            )
        else:
            error_msg = result.get("error", "未知错误")
            logging.error(f"[AccountManager] Refresh failed: {error_msg}")

            self.error.emit(error_msg)

            QMessageBox.warning(
                self._parent,
                "刷新失败",
                f"无法获取最新会员状态：{error_msg}\n\n请稍后重试或联系客服。"
            )

    def _on_refresh_error(self, error_msg: str):
        """Handle subscription refresh error.

        Args:
            error_msg: Error message
        """
        # Close loading dialog
        if self._loading_dialog:
            self._loading_dialog.close()
            self._loading_dialog.deleteLater()
            self._loading_dialog = None
            QApplication.processEvents()

        logging.error(f"[AccountManager] Refresh error: {error_msg}")

        self.error.emit(error_msg)

        QMessageBox.warning(
            self._parent,
            "刷新失败",
            f"网络错误：{error_msg}\n\n请检查网络连接后重试。"
        )

    def logout(self, confirm: bool = True):
        """Log out the current user.

        Args:
            confirm: Whether to show confirmation dialog
        """
        from gaiya.core.async_worker import AsyncNetworkWorker

        if confirm:
            # Confirmation dialog
            reply = QMessageBox.question(
                self._parent,
                "确认退出",
                "确定要退出当前账号吗？\n\n退出后将以游客身份继续使用，免费用户功能将受到限制。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        logging.info("[AccountManager] Logging out...")

        # Create async worker
        if self._auth_client:
            self._logout_worker = AsyncNetworkWorker(self._auth_client.signout)
            self._logout_worker.success.connect(self._on_logout_success)
            self._logout_worker.error.connect(self._on_logout_error)
            self._logout_worker.start()
        else:
            # No auth client, just emit success
            self._on_logout_success({})

    def _on_logout_success(self, result: dict):
        """Handle successful logout.

        Args:
            result: API response (usually empty)
        """
        logging.info("[AccountManager] Logout successful")

        QMessageBox.information(
            self._parent,
            "退出成功",
            "已退出当前账号。\n\n请重新启动应用以切换到游客模式。"
        )

        self.logout_success.emit()

    def _on_logout_error(self, error_msg: str):
        """Handle logout error (still considered success since local token is cleared).

        Args:
            error_msg: Error message
        """
        logging.warning(f"[AccountManager] Logout API error (local token cleared): {error_msg}")

        # Even on API error, local token is cleared, so treat as success
        QMessageBox.information(
            self._parent,
            "退出成功",
            "已退出当前账号。\n\n请重新启动应用以切换到游客模式。"
        )

        self.logout_success.emit()

    def check_login_and_guide(self, feature_name: str = None) -> bool:
        """Check if user is logged in, show login dialog if not.

        Args:
            feature_name: Optional feature name to show in the guidance message

        Returns:
            True if logged in, False if not (dialog shown)
        """
        if self.is_logged_in():
            return True

        # Show guidance message
        message = "此功能需要登录账号才能使用。"
        if feature_name:
            message = f"「{feature_name}」功能需要登录账号才能使用。"

        reply = QMessageBox.question(
            self._parent,
            "需要登录",
            f"{message}\n\n是否现在登录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.show_login_dialog()

        return False

    def get_tier_display_name(self, tier: str = None) -> str:
        """Get display name for a tier.

        Args:
            tier: Tier string, or None to use current user's tier

        Returns:
            Translated tier display name
        """
        if tier is None:
            tier = self.get_user_tier()

        return self.tr(f"account.tiers.{tier}", fallback=tier)

    def cleanup(self):
        """Clean up resources before destruction."""
        if self._loading_dialog:
            self._loading_dialog.close()
            self._loading_dialog = None
