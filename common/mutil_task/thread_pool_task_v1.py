# -*- coding: utf-8 -*-
"""
多类职责拆分版：
- DeduplicateThreadPool : 通用去重线程池
- RobotTask             : 机器人任务封装
- DifyRobotScheduler    : 调度器 + submit_once
"""
from __future__ import annotations

import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Hashable

from wechat_robot.models import WechatRobotQuestion
from common.loger import logger
from common.dify_workflow import DifyChatClient
from django.utils import timezone
from datetime import timedelta


# ---------- 1. 通用去重线程池 ----------
class DeduplicateThreadPool:
    """
    线程池 + 按 key 全局去重
    """

    def __init__(self, max_workers: int = 4, thread_name_prefix: str = "worker"):
        self._lock = threading.Lock()
        self._processing: set[Hashable] = set()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )

    def submit_once(
            self, key: Hashable, fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Future[Any] | None:
        with self._lock:
            if key in self._processing:
                logger.warning("key=%s 的任务已在执行，跳过", key)
                return None
            self._processing.add(key)

        def _wrapper() -> Any:
            try:
                return fn(*args, **kwargs)
            finally:
                with self._lock:
                    self._processing.discard(key)

        return self._executor.submit(_wrapper)

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)


# ---------- 2. 机器人任务封装 ----------
class RobotTask:
    """
    把「处理一条机器人任务」封装成可调用对象，方便丢进线程池
    """

    def __init__(self, stream_id: int):
        self.stream_id = stream_id

    def __call__(self) -> None:
        logger.debug(
            "[Thread %s] 开始处理机器人任务 id=%s",
            threading.get_ident(),
            self.stream_id,
        )
        try:
            WechatRobotQuestion.objects.filter(
                stream=self.stream_id, status="pending"
            ).update(status="running")

            dify = DifyChatClient()
            dify.run_workflow(stream_id=self.stream_id)

            logger.debug(
                "[Thread %s] 机器人任务 id=%s 处理完成",
                threading.get_ident(),
                self.stream_id,
            )
        except Exception as e:
            logger.error(
                "[Thread %s] 运行机器人执行任务 id=%s 失败：%s",
                threading.get_ident(),
                self.stream_id,
                e,
            )
            WechatRobotQuestion.objects.filter(
                stream=self.stream_id
            ).update(status="failed")


# ---------- 2. 机器人任务封装 ----------
class RobotTaskModifyStatus:
    """
    把「处理一条机器人任务」封装成可调用对象，方便丢进线程池
    """

    def __init__(self, stream_id: int):
        self.stream_id = stream_id

    def __call__(self) -> None:
        logger.debug(
            "[Thread %s] 开始处理机器人任务 id=%s",
            threading.get_ident(),
            self.stream_id,
        )
        try:
            dify = DifyChatClient()
            dify.modify_worker_status(stream_id=self.stream_id)

            logger.debug(
                "[Thread %s] 机器人任务状态 id=%s 处理完成",
                threading.get_ident(),
                self.stream_id,
            )
        except Exception as e:
            logger.error(
                "[Thread %s] 运行机器人修改状态任务 id=%s 失败：%s",
                threading.get_ident(),
                self.stream_id,
                e,
            )


# ---------- 3. 调度器 ----------
class DifyRobotScheduler:
    """
    单例调度器
    """
    _instance: "DifyRobotScheduler | None" = None
    _inst_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "DifyRobotScheduler":
        if cls._instance is None:
            with cls._inst_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_workers: int = 4, thread_name_prefix: str = "robot_worker") -> None:
        if hasattr(self, "_inited"):
            return
        self._inited: bool = True

        # 底层复用通用去重线程池
        self._pool = DeduplicateThreadPool(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )
        logger.info("DifyRobotScheduler 初始化完成，线程池大小=%s，前缀=%s", max_workers, thread_name_prefix)

    # ---- 对外暴露的通用去重提交接口 ----
    def submit_once(
            self, key: Hashable, fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Future[Any] | None:
        """
        任何业务函数都可全局去重提交
        """
        return self._pool.submit_once(key, fn, *args, **kwargs)

    # ---- 原有调度逻辑 ----
    def runner(self) -> None:
        logger.debug("=== 新一轮调度开始 ===")

        candidates = list(
            WechatRobotQuestion.objects.filter(
                finish=False,
                status="pending",
                create_time__gt=(timezone.now() - timedelta(seconds=120)),
            )[:5]
        )
        if not candidates:
            logger.debug("没有待处理机器人任务，本轮空跑。")
            return

        for o in candidates:
            # 用 stream_id 作为去重 key
            self._pool.submit_once(
                f"robot_runner_{o.stream}", RobotTask(o.stream)
            )  # 返回 Future 此处忽略

    def modify_status_runner(self):
        """

        """
        candidates = list(
            WechatRobotQuestion.objects.filter(
                finish=False
            )[:5]
        )
        if not candidates:
            logger.debug("没有待处理机器人任务，本轮空跑。")
            return

        for o in candidates:
            # 用 stream_id 作为去重 key
            self._pool.submit_once(
                f"robot_status_{o.stream}", RobotTaskModifyStatus(o.stream)
            )  # 返回 Future 此处忽略

    # ---- 优雅关闭 ----
    def shutdown(self, wait: bool = True) -> None:
        logger.info("正在关闭 DifyRobotScheduler……")
        self._pool.shutdown(wait=wait)
        logger.info("DifyRobotScheduler 已停止。")

# def crontab_run_dify_job():
#     scheduler = DifyRobotScheduler()
#     scheduler.runner()
#     scheduler.modify_status_runner()

# ---------------- 使用示例 ----------------
# if __name__ == "__main__":
#     import requests
#
#
#     def my_business_task(url: str) -> int:
#         resp = requests.get(url, timeout=10)
#         logger.info("业务任务完成，状态码=%s", resp.status_code)
#         return resp.status_code
#
#
#     scheduler = DifyRobotScheduler()
#
#     # 1. 去重提交业务任务
#     future1 = scheduler.submit_once("example_com", my_business_task, "https://www.example.com")
#     if future1:
#         logger.info("业务任务返回码=%s", future1.result())
#
#     # 2. 重复 key 将跳过
#     future2 = scheduler.submit_once("example_com", my_business_task, "https://www.example.com")
#     logger.info("重复 key 提交结果=%s", future2)  # None
#
#     # 3. 原机器人调度继续用
#     scheduler.run()
