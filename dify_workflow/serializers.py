from rest_framework import serializers
from dify_workflow.models import *


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
    data = WorkflowRunDataSerializer(many=True)

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
            workflow_data = [
                WorkflowRunData(category=dify_task, event=event, **p)
                for p in data
            ]
            WorkflowRunData.objects.bulk_create(workflow_data, batch_size=1000, ignore_conflicts=False)
        return dify_task


__all__ = [
    'AgentLogSerializer',
    'WorkflowRunDataSerializer',
    'WorkflowTaskSerializer'
]
