from rest_framework import serializers
from wechat_robot.models import *


class WechatRobotQuestionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatRobotQuestionData
        fields = '__all__'


class WechatRobotQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatRobotQuestion
        fields = '__all__'
