from django.db import models


# Create your models here.

class Workflow(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class WorkflowData(models.Model):
    event = models.CharField(max_length=30, default='message', verbose_name='事件类型')
    conversation_id = models.CharField(max_length=40, default='', verbose_name="会话ID")
    message_id = models.CharField(max_length=40, default="", verbose_name="消息唯一ID")
    task_id = models.CharField(max_length=100)
    workflow_run_id = models.CharField(max_length=100)
    data = models.JSONField()
