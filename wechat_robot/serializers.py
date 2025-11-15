from rest_framework import serializers
from wechat_robot.models import *


class WechatRobotQuestionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatRobotQuestionData
        fields = '__all__'


class WechatRobotQuestionSerializer(serializers.ModelSerializer):
    msg_id = serializers.CharField(max_length=36, source="msgid")
    aibot_id = serializers.CharField(max_length=36, source="aibotid")
    chat_id = serializers.CharField(max_length=36, source="chatid")
    chat_type = serializers.CharField(max_length=36, source="chattype")
    chat_from = serializers.JSONField(source="from")
    msg_type = serializers.ChoiceField(choices=(("text", "text"), ("stream", "stream")), source="msgtype")

    class Meta:
        model = WechatRobotQuestion
        fields = '__all__'
