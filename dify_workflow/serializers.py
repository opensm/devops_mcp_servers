from rest_framework import serializers
from dify_workflow.models import *
from common.loger import logger


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = '__all__'


class WorkflowRunDataSerializer(serializers.ModelSerializer):
    agent_logs = AgentLogSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRunData
        fields = '__all__'


class WorkflowTaskSerializer(serializers.ModelSerializer):
    data = WorkflowRunDataSerializer()

    class Meta:
        model = WorkflowTask
        fields = '__all__'

    def create(self, validated_data):
        """
        整个 JSON 里只有 Category + 它的 products。
        用 update_or_create 处理 Category，
        然后同步 products（先删后插）。
        """
        data = validated_data.pop('data')
        conversation_id = validated_data.pop('conversation_id')
        message_id = validated_data.pop('message_id')
        task_id = validated_data.pop('task_id')
        workflow_run_id = validated_data.pop('workflow_run_id')
        event = validated_data.pop('event'),
        robot_task = validated_data.pop('robot_task')
        dify_task, _ = WorkflowTask.objects.update_or_create(
            conversation_id=conversation_id,
            message_id=message_id,
            task_id=task_id,
            workflow_run_id=workflow_run_id,
            defaults={"robot_task": robot_task}
        )
        if data:
            # 再批量新建
            logger.info(f"开始处理机器人任务 id={dify_task.id},data={data}")
            WorkflowRunData.objects.create(workflow_run=dify_task, event=event, **data)
        return dify_task


__all__ = [
    'AgentLogSerializer',
    'WorkflowRunDataSerializer',
    'WorkflowTaskSerializer'
]
