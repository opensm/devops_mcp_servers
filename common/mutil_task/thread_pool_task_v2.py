# -*- coding: utf-8 -*-
"""
去单例、可复用、防重复 shutdown 的调度器（已修复 RuntimeError）
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Hashable, Optional

from wechat_robot.models import WechatRobotQuestion
from common.loger import logger
from common.dify_workflow import DifyChatClient
from django.utils import timezone
from datetime import timedelta


class DeduplicateThreadPool:
    """
    通用去重线程池
    """

    def __init__(self, max_workers: int = 4, thread_name_prefix: str = "worker"):
        self._lock = threading.Lock()
        self._processing: set[Hashable] = set()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=thread_name_prefix)
        self._shutdown = False

    # ---------- 新增 ----------
    def is_shutdown(self) -> bool:
        with self._lock:
            return self._shutdown
    # -------------------------

    def submit_once(self, key: Hashable, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[Future[Any]]:
        with self._lock:
            if self._shutdown:
                logger.warning("池子已 shutdown，拒绝新任务 key=%s", key)
                return None
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
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
        logger.info("DeduplicateThreadPool 正在 shutdown...")
        self._executor.shutdown(wait=wait)
        logger.info("DeduplicateThreadPool 已停止。")


class RobotTask:
    def __init__(self, stream_id: int):
        self.stream_id = stream_id

    def __call__(self) -> None:
        logger.debug("[Thread %s] 开始处理机器人任务 id=%s", threading.get_ident(), self.stream_id)
        try:
            WechatRobotQuestion.objects.filter(stream=self.stream_id, status="pending").update(status="running")
            dify = DifyChatClient()
            dify.run_workflow(stream_id=self.stream_id)
            logger.debug("[Thread %s] 机器人任务 id=%s 处理完成", threading.get_ident(), self.stream_id)
        except Exception as e:
            logger.error("[Thread %s] 运行机器人任务 id=%s 失败：%s", threading.get_ident(), self.stream_id, e)
            WechatRobotQuestion.objects.filter(stream=self.stream_id).update(status="failed")


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


class DifyRobotScheduler:
    """
    非单例、可安全 shutdown 的调度器
    支持 with 语法
    """

    def __init__(self, max_workers: int = 4):
        self._pool = DeduplicateThreadPool(max_workers=max_workers, thread_name_prefix="robot_worker")
        logger.info("DifyRobotScheduler 初始化完成，线程池大小=%s", max_workers)

    # ---- 上下文管理器 ----
    def __enter__(self) -> "DifyRobotScheduler":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown(wait=True)

    # ---- 通用去重提交 ----
    def submit_once(self, key: Hashable, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[Future[Any]]:
        return self._pool.submit_once(key, fn, *args, **kwargs)

    # ---------- 新增 ----------
    def _safe_submit(self, key: Hashable, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """
        如果池子已关闭则直接返回 False，否则提交并返回 True
        方便调用方快速判断这一轮还能不能继续跑
        """
        fut = self._pool.submit_once(key, fn, *args, **kwargs)
        return fut is not None
    # -------------------------

    def modify_status_runner(self) -> None:
        if self._pool.is_shutdown():
            logger.debug("池子已关闭，跳过 modify_status_runner")
            return

        candidates = list(WechatRobotQuestion.objects.filter(finish=False)[:5])
        if not candidates:
            logger.debug("没有待处理机器人任务，本轮空跑。")
            return

        for o in candidates:
            ok = self._safe_submit(f"robot_status_{o.stream}", RobotTaskModifyStatus(o.stream))
            if not ok:          # 池子被关了，立即结束
                logger.debug("submit 被拒绝，提前退出 modify_status_runner")
                break

    def runner(self) -> None:
        if self._pool.is_shutdown():
            logger.debug("池子已关闭，跳过 runner")
            return

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
            ok = self._safe_submit(f"robot_{o.stream}", RobotTask(o.stream))
            if not ok:
                logger.debug("submit 被拒绝，提前退出 runner")
                break

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)