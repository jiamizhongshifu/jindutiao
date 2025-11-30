"""
番茄钟面板和专注会话集成
此文件包含专注会话管理功能的扩展方法
"""

def get_focus_session_db(self):
    """获取数据库管理器实例（延迟导入）"""
    if self.focus_session_db is None:
        try:
            from gaiya.data.db_manager import db
            self.focus_session_db = db
        except ImportError as e:
            self.logger.error(f"无法导入数据库管理器: {e}")
            return None
    return self.focus_session_db

def create_focus_session(self):
    """创建专注会话"""
    if not self.time_block_id:
        return

    db = get_focus_session_db(self)
    if not db:
        return

    try:
        self.current_focus_session_id = db.create_focus_session(self.time_block_id)
        self.logger.info(f"创建专注会话: {self.current_focus_session_id}")
    except Exception as e:
        self.logger.error(f"创建专注会话失败: {e}")

def complete_focus_session(self):
    """完成专注会话"""
    if not self.current_focus_session_id:
        return

    db = get_focus_session_db(self)
    if not db:
        return

    try:
        db.complete_focus_session(self.current_focus_session_id)
        self.logger.info(f"完成专注会话: {self.current_focus_session_id}")
        self.current_focus_session_id = None
    except Exception as e:
        self.logger.error(f"完成专注会话失败: {e}")

def interrupt_focus_session(self):
    """中断专注会话"""
    if not self.current_focus_session_id:
        return

    db = get_focus_session_db(self)
    if not db:
        return

    try:
        db.interrupt_focus_session(self.current_focus_session_id)
        self.logger.info(f"中断专注会话: {self.current_focus_session_id}")
        self.current_focus_session_id = None
    except Exception as e:
        self.logger.error(f"中断专注会话失败: {e}")