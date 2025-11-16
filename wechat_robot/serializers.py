from rest_framework import serializers
from wechat_robot.models import *
from django.utils import timezone
from common.loger import logger


class WechatRobotQuestionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatRobotQuestionData
        fields = '__all__'


class WechatRobotQuestionSerializer(serializers.ModelSerializer):
    # msgid = serializers.CharField(max_length=36, source="msg_id")
    # aibotid = serializers.CharField(max_length=36, source="aibot_id")
    # chatid = serializers.CharField(max_length=36, source="chat_id")
    # chattype = serializers.CharField(max_length=36, source="chat_type")
    # # from = serializers.JSONField(source="from")
    # msgtype = serializers.ChoiceField(choices=(("text", "text"), ("stream", "stream")), source="msg_type")
    # chat_from = serializers.JSONField(source="chat_from")
    content = serializers.SerializerMethodField()
    finish = serializers.SerializerMethodField()

    def get_content(self, obj):
        _time = (timezone.now() - obj.create_time).total_seconds()
        logger.debug(f"{obj.id} 数据时间差为：{_time},数据为：{obj.workflow_runs}")
        if not obj.workflow_runs and _time < 120:
            return "当前机器人正在处理中，请稍等"
        elif not obj.workflow_runs and _time >= 120:
            return "当前机器人没有处理该问题，请稍后再试"
        return "测试数据"

    def get_finish(self, obj):
        _time = (timezone.now() - obj.create_time).total_seconds()
        if not obj.workflow_runs and _time < 120:
            return False
        elif not obj.workflow_runs and _time >= 120:
            return True
        return False

    class Meta:
        model = WechatRobotQuestion
        fields = '__all__'
