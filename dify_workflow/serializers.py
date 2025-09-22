from rest_framework import serializers
from dify_workflow.models import *


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = '__all__'


class NodeExecutionSerializer(serializers.ModelSerializer):
    agent_logs = AgentLogSerializer(many=True, read_only=True)

    class Meta:
        model = NodeExecution
        fields = '__all__'


class WorkflowRunSerializer(serializers.ModelSerializer):
    nodes = NodeExecutionSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRun
        fields = '__all__'


__all__ = [
    'AgentLogSerializer',
    'NodeExecutionSerializer',
    'WorkflowRunSerializer'
]
