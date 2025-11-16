from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView, ListCreateAPIView
#
# from dify_workflow.models import Workflow, WorkflowData
# from dify_workflow.serializers import WorkflowSerializer, LLMAgentLogsSerializer
#
#
# class WorkflowDataView(ListCreateAPIView):
#     serializer_class = WorkflowSerializer
#     model = WorkflowData
#
#
# class WorkflowView(ListAPIView):
#     serializer_class = WorkflowSerializer
#     model = Workflow
#
#
# class LLMAgentLogs(ListCreateAPIView):
#     serializer_class = LLMAgentLogsSerializer
#     model = ListCreateAPIView
#
#
# __all__ = [
#     'WorkflowDataView',
#     'WorkflowView',
#     'LLMAgentLogs'
# ]
