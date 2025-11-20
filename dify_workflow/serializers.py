from rest_framework import serializers
from dify_workflow.models import *
from common.loger import logger


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = '__all__'


class WorkflowRunDataSerializer(serializers.ModelSerializer):
    workflow_run = serializers.HiddenField(default=None)

    class Meta:
        model = WorkflowRunData
        fields = '__all__'
        # extra_kwargs = {
        #     'workflow_run': {'validators': []},  # 把默认的 UniqueValidator 摘掉
        # }


class WorkflowTaskSerializer(serializers.ModelSerializer):
    data = WorkflowRunDataSerializer(required=False)
    event = serializers.CharField(max_length=100, default="workflow_started")

    class Meta:
        model = WorkflowTask
        fields = '__all__'
        extra_kwargs = {'robot_task': {'validators': []}}

    def create(self, validated_data):
        """
        整个 JSON 里只有 Category + 它的 products。
        用 update_or_create 处理 Category，
        然后同步 products（先删后插）。
        """
        logger.info(f"开始处理机器人任务 data={validated_data}")
        data = validated_data.pop('data', None)
        conversation_id = validated_data.pop('conversation_id')
        message_id = validated_data.pop('message_id')
        task_id = validated_data.pop('task_id')
        workflow_run_id = validated_data.pop('workflow_run_id', None)
        event = validated_data.pop('event'),
        robot_task = validated_data.pop('robot_task')
        answer = validated_data.pop('answer', '')
        if workflow_run_id:
            _data = {"robot_task": robot_task, "workflow_run_id": workflow_run_id, 'answer': answer}
        else:
            _data = {"robot_task": robot_task, 'answer': answer}
        dify_task, _ = WorkflowTask.objects.update_or_create(
            conversation_id=conversation_id,
            message_id=message_id,
            task_id=task_id,
            defaults=_data
        )
        logger.info(f"1开始处理机器人任务 id={dify_task.id}, data={data}")
        if data is not None:
            data['workflow_run'] = dify_task
            # 再批量新建
            WorkflowRunData.objects.create(event=event, **data)
            logger.info(f"处理机器人任务 id={dify_task.id}完成")
        return dify_task


__all__ = [
    'AgentLogSerializer',
    'WorkflowRunDataSerializer',
    'WorkflowTaskSerializer'
]
