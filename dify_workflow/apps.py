from django.apps import AppConfig


class DifyWorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dify_workflow'
    #
    # def ready(self):
    #     from common.mutil_task.scheduled_task import start
    #     start()