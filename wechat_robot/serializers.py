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

    def get_content(self, obj: WechatRobotQuestion) -> str:
        """
        返回机器人最新答案；若超时且仍无答案则标记结束并返回提示语。
        整条链路仅 1~2 条 SQL，无 N+1。
        """
        # 0. 取超时阈值
        try:
            timeout = int(getattr(settings, 'WECHAT_BOT_ANSWER_TIMEOUT', 120))
        except (TypeError, ValueError):
            raise ImproperlyConfigured('WECHAT_BOT_ANSWER_TIMEOUT 必须为正整数')

        # 1. 一次性取出含 answer 的最新节点数据
        latest_data = (
            WorkflowRunData.objects
            .filter(
                workflow_run__robot_task=obj,  # ← 这里是 obj 不是 self
                event='node_finished',
                status='succeeded',
                outputs__has_key='answer'
            )
            .order_by('-index')
            .only('outputs')
            .first()
        )

        if latest_data:  # ① 有答案
            return latest_data.outputs['answer']

        # 2. 无答案 → 判断是否超时
        elapsed = (timezone.now() - obj.create_time).total_seconds()
        if elapsed > timeout:
            # 3. 超时关单（原子性）
            WechatRobotQuestion.objects.filter(pk=obj.pk, finish=False).update(
                finish=True, status='failed'
            )
            return '当前机器人没有处理该问题，请稍后再试'

        # 4. 未超时
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
