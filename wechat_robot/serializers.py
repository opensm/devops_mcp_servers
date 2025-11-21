from rest_framework import serializers
from wechat_robot.models import *
from django.utils import timezone
from common.loger import logger
from devops_mcp_servers import settings
from dify_workflow.models import WorkflowRunData
from django.core.exceptions import ImproperlyConfigured
from datetime import datetime


class WechatRobotQuestionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WechatRobotQuestionData
        fields = '__all__'


class WechatRobotQuestionSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    # ------------------- 只改这一坨 -------------------
    def get_content(self, obj: WechatRobotQuestion) -> str:
        timeout = int(getattr(settings, 'WECHAT_BOT_ANSWER_TIMEOUT', 120))

        # 1. 取最新含 answer 的节点
        latest_data = (
            WorkflowRunData.objects
            .filter(
                workflow_run__robot_task=obj,
                status='succeeded',
                outputs__has_key='answer'
            )
            .order_by('-index')
            .only('outputs', 'event')
            .first()
        )

        if latest_data:  # ① 有答案
            # 原子性关单（只写一次，并发安全）
            WechatRobotQuestion.objects.filter(
                pk=obj.pk, finish=False
            ).update(finish=True, status='finished')
            # 内存对象也同步，免得后面再用 serializer 时状态不对
            obj.finish, obj.status = True, 'finished'
            return latest_data.outputs['answer']

        # 2. 无答案 → 超时关单
        elapsed = (timezone.now() - obj.create_time).total_seconds()
        if elapsed > timeout:
            WechatRobotQuestion.objects.filter(
                pk=obj.pk, finish=False
            ).update(finish=True, status='failed')
            obj.finish, obj.status = True, 'failed'
            return '当前机器人没有处理该问题，请稍后再试'

        # 3. 未超时
        return '请等待，大模型正在思考中 {}'.format(datetime.now().second % 60 * ".")

    def to_internal_value(self, data):
        logger.debug(f"数据: {data}")
        if "stream" in data:
            stream = data.pop("stream")
            data.update({
                "stream": stream['id'],
            })
        if "text" in data.keys():
            text = data.pop("text")
            data.update({
                "text": text['content']
            })
        chat_from = data.pop("from")
        data.update({
            "chat_from": chat_from['userid'],

        })
        return super().to_internal_value(data)

    def create(self, validated_data):
        logger.debug(f"保存数据: {validated_data}")
        if validated_data.get('msgtype', '') == "stream":
            try:
                stream_id = validated_data.get('stream', '')
                robt_instance = WechatRobotQuestion.objects.get(stream=stream_id)
                robt_instance.update_time = timezone.now()
                robt_instance.save()
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
        extra_kwargs = {
            'stream': {'validators': []},  # 把默认的 UniqueValidator 摘掉
        }
