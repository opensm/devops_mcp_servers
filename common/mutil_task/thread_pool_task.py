import time
import threading
from concurrent.futures import ThreadPoolExecutor
from wechat_robot.models import WechatRobotQuestion
from common.loger import logger
from common.dify_workflow import DifyChatClient
from django.utils import timezone
from datetime import timedelta

# 全局内存锁 + 已处理集合（线程安全）
lock = threading.Lock()
processing = set()  # 存放正在被处理的机器人任务 id


def _process_one(stream_id: int):
    """真正耗时的工作，放锁外执行"""
    logger.info('[Thread %s] 开始处理机器人任务 id=%s', threading.get_ident(), stream_id)
    try:
        dify = DifyChatClient()
        dify.run_workflow(stream_id=stream_id)
        # 更新数据库（乐观更新即可）
        WechatRobotQuestion.objects.filter(stream=stream_id, status='pending').update(status='running')
        logger.info('[Thread %s] 机器人任务 id=%s 处理完成', threading.get_ident(), stream_id)
    except Exception as e:
        logger.error('[Thread %s] 运行机器人任务 id=%s 失败：%s', threading.get_ident(), stream_id, e)

    # 处理完从集合里去掉
    with lock:
        processing.discard(stream_id)


def crontab_run_dify_job():
    """主调度函数，每 5 秒跑一次"""
    logger.info('=== 新一轮调度开始 ===')
    # 1. 先快速捞一批 pending（不锁行）
    candidates = list(WechatRobotQuestion.objects.filter(
        status='pending',
        create_time__gt=(timezone.now() - timedelta(seconds=120))
    )[:5])
    if not candidates:
        logger.info('没有待处理机器人任务，本轮空跑。')
        return

    # 2. 用内存锁决定“谁”真正要处理
    to_handle = []
    with lock:
        for o in candidates:
            if o.stream not in processing:  # 未被其它线程抢
                processing.add(o.stream)
                to_handle.append(o.stream)

    if not to_handle:
        logger.info('本轮候选机器人任务都已在处理，直接返回。')
        return

    # 3. 丢给线程池异步做真正耗时的工作
    for oid in to_handle:
        executor.submit(_process_one, oid)


# 全局线程池：最大 4 个并发线程
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='robot_worker')
