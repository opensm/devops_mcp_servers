from rest_framework import serializers
from dify_workflow.models import *

class WorkflowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ['id']


class WorkflowDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowData
        fields = '__all__'
        read_only_fields = ['id']


class LLMAgentLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMAgentLogs
        fields = '__all__'
        read_only_fields = ['id']
