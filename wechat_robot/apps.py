# wechat_robot/apps.py
from django.apps import AppConfig
from common.loger import logger
import os


class WechatRobotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wechat_robot'
    scheduler = None
    dify_scheduler_runner = None
    dify_scheduler_status = None

    def ready(self):
        # ✅ 防止 autoreloader 重复启动
        if os.environ.get('RUN_MAIN') != 'true':
            return

        # ✅ 延迟导入，避免 AppRegistryNotReady
        from apscheduler.schedulers.background import BackgroundScheduler
        from django_apscheduler.jobstores import DjangoJobStore
        from common.mutil_task.thread_pool_task_v1 import DifyRobotScheduler
        import atexit

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore(DjangoJobStore(), 'dify')

        self.dify_scheduler_runner = DifyRobotScheduler(max_workers=4, thread_name_prefix="runner")
        self.dify_scheduler_status = DifyRobotScheduler(max_workers=1, thread_name_prefix="status")

        self.scheduler.add_job(
            self.dify_scheduler_runner.runner,
            trigger='interval',
            seconds=5,
            max_instances=1
        )
        self.scheduler.add_job(
            self.dify_scheduler_status.modify_status_runner,
            trigger='interval',
            seconds=5,
            max_instances=1
        )

        self.scheduler.start()
        logger.info("✅ APS 调度器已启动")

        # ✅ 注册 shutdown 钩子
        atexit.register(self.shutdown_scheduler)

    def shutdown_scheduler(self):
        """
        关闭调度器
        """
        logger.info("APS 停止中...")
        if hasattr(self, 'scheduler'):
            self.scheduler.shutdown(wait=True)
            logger.info("🛑 APS 调度器已关闭")
        if hasattr(self, 'dify_scheduler_runner'):
            self.dify_scheduler_runner.shutdown(wait=True)
            logger.info("🛑 DifyRobotScheduler 已关闭")
