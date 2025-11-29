from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from common.dify_workflow import WorkStatusManager


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'dify')
    modify_status = WorkStatusManager()

    scheduler.add_job(
        modify_status.modify_task_status,
        trigger='interval',
        seconds=1,
        id='crontab_modify_status_job',
        replace_existing=True
    )
    scheduler.start()
