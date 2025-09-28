from django.contrib.gis.geometry import json_regex
from django.db import models


class WechatRobotQuestionBase(models.Model):
    msg_id = models.CharField(max_length=36, unique=True, primary_key=True)
    aibot_id = models.CharField(max_length=36, name="机器人id", default="", null=False)
    chat_id = models.CharField(max_length=36, name="聊天id", default="", null=False)
    chat_type = models.CharField(max_length=36, choices=(("群", "group"),), default="group", null=False)
    chat_from = models.JSONField(default=dict(), null=False, blank=False)
    msg_type = models.CharField(
        max_length=36, choices=(("文字", "text"), ("数据流", "stream")), default="text", null=False
    )


# { "msgid":"74ac2a01537faf17e83e248a1ac7fd4c","aibotid":"aibrGalbJc-O4nrQRGAGLjNTIk8PpdhpCje",
# "chatid":"wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ","chattype":"group","from":
# {"userid":"ky005509"},"msgtype":"text","text":{"content":"@姚绍强 你好"}}

class WechatRobotQuestion(WechatRobotQuestionBase):
    text = models.JSONField(default={}, null=False, blank=False)
    stream_id = models.CharField(max_length=36, null=True, default="")


# {'msgid': '2cea1e14656ba7c3810a3c6841e18a68', 'aibotid': 'aibrGalbJc-O4nrQRGAGLjNTIk8PpdhpCje',
# 'chatid': 'wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ', 'chattype': 'group', 'from': {'userid': 'ky005509'},
# 'msgtype': 'stream', 'stream': {'id': 'dify::aibrGalbJc-O4nrQRGAGLjNTIk8PpdhpCje:wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ:V8hgz9vBFW'
# }}
class WechatRobotQuestionData(WechatRobotQuestionBase):
    stream = models.JSONField(default={}, null=False, blank=False)
