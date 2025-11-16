from rest_framework import serializers
from wechat_robot.models import *
from django.utils import timezone
from common.loger import logger


class WechatRobotQuestionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatRobotQuestionData
        fields = '__all__'


class WechatRobotQuestionSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    finish = serializers.SerializerMethodField()

    def get_content(self, obj):
        logger.debug(f"类型数据为：{obj}")
        _time = (timezone.now() - obj.create_time).total_seconds()
        logger.debug(f"{obj.id} 数据时间差为：{_time},数据为：{obj.workflow_runs}")
        if not obj.workflow_runs and _time < 120:
            return "当前机器人正在处理中，请稍等"
        elif not obj.workflow_runs and _time >= 120:
            return "当前机器人没有处理该问题，请稍后再试"
        return "测试数据: {}".format(_time)

    def get_finish(self, obj):
        _time = (timezone.now() - obj.create_time).total_seconds()
        if not obj.workflow_runs and _time < 120:
            return False
        elif not obj.workflow_runs and _time >= 120:
            return True
        return False

    def to_internal_value(self, data):
        logger.debug(f"数据: {data}")
        stream = data.pop("stream")
        chat_from = data.pop("from")
        data.update({
            "stream": stream['id'],
            "chat_from": chat_from['userid']
        })
        return super().to_internal_value(data)

    def create(self, validated_data):
        logger.debug(f"保存数据: {validated_data}")
        if validated_data.get('msgtype', "") == "stream":
            try:
                stream_id = validated_data.get('stream', {}).get('id', False)
                robt_instance = WechatRobotQuestion.objects.get(stream=stream_id)
                return robt_instance
            except WechatRobotQuestion.DoesNotExist:
                logger.error(f"当前请求为流数据，但是未查询到数据: {validated_data}")
                raise serializers.ValidationError("当前请求为流数据，但是未查询到数据")
        else:
            logger.debug(f"保存数据: {validated_data}")
            return super().create(validated_data)

    class Meta:
        model = WechatRobotQuestion
        fields = '__all__'
