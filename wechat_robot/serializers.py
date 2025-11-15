from rest_framework import serializers
from wechat_robot.models import *


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

    class Meta:
        model = WechatRobotQuestion
        fields = '__all__'
