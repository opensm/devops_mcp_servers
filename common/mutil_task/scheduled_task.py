from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from common.mutil_task.thread_pool_task import crontab_run_dify_job


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'dify')
    scheduler.add_job(
        crontab_run_dify_job,
        trigger='interval',
        seconds=1,
        id='crontab_run_dify_job',
        replace_existing=True
    )
    scheduler.start()
