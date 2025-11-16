from django.contrib.gis.geometry import json_regex
from django.db import models


class WechatRobotQuestionBase(models.Model):
    msgid = models.CharField(max_length=36, unique=True, verbose_name="消息id")
    aibotid = models.CharField(max_length=36, verbose_name="机器人id", default="", null=False)
    chatid = models.CharField(max_length=36, verbose_name="聊天id", default="", null=False)
    chattype = models.CharField(max_length=36, choices=(("group", "群"), ("single", "个人")), default="group",
                                null=False)
    chat_from = models.JSONField(default=dict(), null=False, blank=False, db_column="from")
    msgtype = models.CharField(
        max_length=36, choices=(("text", "文字"), ("stream", "数据流")), default="text", null=False
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True


# { "msgid":"74ac2a01537faf17e83e248a1ac7fd4c","aibotid":"aibrGalbJc-O4nrQRGAGLjNTIk8PpdhpCje",
# "chatid":"wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ","chattype":"group","from":
# {"userid":"ky005509"},"msgtype":"text","text":{"content":"@姚绍强 你好"}}

class WechatRobotQuestion(WechatRobotQuestionBase):
    import uuid
    text = models.JSONField(default="", null=False, blank=False)
    stream_id = models.UUIDField(null=False, blank=False, default=uuid.uuid4, unique=True, editable=False)


# {'msgid': '2cea1e14656ba7c3810a3c6841e18a68', 'aibotid': 'aibrGalbJc-O4nrQRGAGLjNTIk8PpdhpCje',
# 'chatid': 'wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ', 'chattype': 'group', 'from': {'userid': 'ky005509'},
# 'msgtype': 'stream', 'stream': {'id': 'dify::aibrGalbJc-O4nrQRGAGLjNTIk8PpdhpCje:wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ:V8hgz9vBFW'
# }}
class WechatRobotQuestionData(WechatRobotQuestionBase):
    stream = models.JSONField(default=dict(), null=False, blank=False)
