from rest_framework import serializers
from dify_workflow.models import *
from common.loger import logger


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = '__all__'


class WorkflowRunDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRunData
        fields = '__all__'
        # extra_kwargs = {
        #     'workflow_run': {'validators': []},  # 把默认的 UniqueValidator 摘掉
        # }


class WorkflowTaskSerializer(serializers.ModelSerializer):
    # data = WorkflowRunDataSerializer()
    event = serializers.CharField(max_length=100, default="workflow_started")

    class Meta:
        model = WorkflowTask
        fields = '__all__'

    def create(self, validated_data):
        """
        整个 JSON 里只有 Category + 它的 products。
        用 update_or_create 处理 Category，
        然后同步 products（先删后插）。
        """
        logger.info(f"保存数据: 1")
        data = validated_data.pop('data', None)
        logger.info(f"保存数据: 2")
        conversation_id = validated_data.pop('conversation_id')
        logger.info(f"保存数据: 3")
        message_id = validated_data.pop('message_id')
        logger.info(f"保存数据: 4")
        task_id = validated_data.pop('task_id')
        logger.info(f"保存数据: 5")
        workflow_run_id = validated_data.pop('workflow_run_id')
        logger.info(f"保存数据: 5")
        event = validated_data.pop('event'),
        logger.info(f"保存数据: 6")
        robot_task = validated_data.pop('robot_task')
        logger.info(f"保存数据: 7")
        dify_task, _ = WorkflowTask.objects.update_or_create(
            conversation_id=conversation_id,
            message_id=message_id,
            task_id=task_id,
            workflow_run_id=workflow_run_id,
            defaults={"robot_task": robot_task}
        )
        logger.info(f"保存数据: 8")
        logger.info(f"1开始处理机器人任务 id={dify_task.id}, data={data}")
        if data is not None:
            # 再批量新建
            logger.info(f"2开始处理机器人任务 id={dify_task.id}, data={data}")
            WorkflowRunData.objects.create(workflow_run=dify_task, event=event, **data)
            logger.info(f"处理机器人任务 id={dify_task.id}完成")
        return dify_task


__all__ = [
    'AgentLogSerializer',
    'WorkflowRunDataSerializer',
    'WorkflowTaskSerializer'
]
