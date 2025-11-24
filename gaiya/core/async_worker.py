"""
GaiYa每日进度条 - 异步网络请求工作线程
解决同步网络请求导致UI假死的问题
"""
from PySide6.QtCore import QThread, Signal
from typing import Callable, Any, Dict


class AsyncNetworkWorker(QThread):
    """
    通用异步网络请求工作线程

    用法:
        worker = AsyncNetworkWorker(auth_client.login, email, password)
        worker.success.connect(on_success)
        worker.error.connect(on_error)
        worker.start()
    """
    # 成功信号(返回结果字典)
    success = Signal(dict)

    # 错误信号(返回错误信息)
    error = Signal(str)

    # 进度信号(可选,用于显示加载状态)
    progress = Signal(str)

    def __init__(self, func: Callable, *args, **kwargs):
        """
        初始化工作线程

        Args:
            func: 要执行的函数(如 auth_client.login)
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        """Execute network request in background thread

        Emits success signal with result dict on success, or error signal on failure.
        """
        try:
            # 发出进度信号
            func_name = self.func.__name__
            self.progress.emit(f"正在执行: {func_name}...")

            # 执行函数
            result = self.func(*self.args, **self.kwargs)

            # 检查结果类型
            if isinstance(result, dict):
                # 如果结果是字典,检查success字段
                if result.get("success", False):
                    self.success.emit(result)
                else:
                    error_msg = result.get("error", "未知错误")
                    self.error.emit(error_msg)
            else:
                # 如果结果不是字典,直接包装为成功结果
                self.success.emit({"success": True, "data": result})

        except Exception as e:
            # 捕获所有异常,通过error信号返回
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.error.emit(error_msg)


class AsyncAIWorker(QThread):
    """
    AI任务生成异步工作线程(保留向后兼容)

    用法:
        worker = AsyncAIWorker(ai_client, user_input)
        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        worker.start()
    """
    # 成功信号
    finished = Signal(dict)

    # 错误信号
    error = Signal(str)

    def __init__(self, ai_client, user_input: str):
        super().__init__()
        self.ai_client = ai_client
        self.user_input = user_input

    def run(self) -> None:
        """Execute AI request in background thread

        Emits finished signal with result dict on success, or error signal on failure.
        """
        try:
            result = self.ai_client.plan_tasks(self.user_input, parent_widget=None)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
