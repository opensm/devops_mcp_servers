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
    chat_from = serializers.JSONField(source="chat_from", field_name="from")
    content = serializers.SerializerMethodField()
    finish = serializers.SerializerMethodField()

    def get_content(self, obj):
        import datetime
        _time = (obj.create_time - datetime.datetime.now()).total_seconds()
        if not obj.WechatRobotQuestion and _time < 120:
            return "当前机器人正在处理中，请稍等"
        elif not obj.WechatRobotQuestion and _time >= 120:
            return "当前机器人没有处理该问题，请稍后再试"
        return obj.WechatRobotQuestion.content

    def get_finish(self, obj):
        import datetime
        _time = (obj.create_time - datetime.datetime.now()).total_seconds()
        if not obj.WechatRobotQuestion and _time < 120:
            return False
        elif not obj.WechatRobotQuestion and _time >= 120:
            return True
        return True

    class Meta:
        model = WechatRobotQuestion
        fields = '__all__'
