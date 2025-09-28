import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
import json


class WorkflowRun(models.Model):
    """存储工作流运行的基本信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.CharField(max_length=100, verbose_name="事件", default="workflow_started")
    conversation_id = models.UUIDField(verbose_name="运行ID")
    message_id = models.UUIDField(verbose_name="消息ID")
    task_id = models.UUIDField(verbose_name="任务ID")
    workflow_run_id = models.UUIDField(verbose_name="工作流运行ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['task_id']),
            models.Index(fields=['workflow_id']),
            models.Index(fields=['created_at']),
        ]


class NodeExecution(models.Model):
    """存储节点执行信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name='nodes')
    node_id = models.CharField(max_length=100)
    node_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    index = models.IntegerField()
    predecessor_node_id = models.CharField(max_length=100, blank=True)
    inputs = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    process_data = models.TextField(blank=True)
    outputs = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    status = models.CharField(max_length=20, default='running')  # running, succeeded, failed
    error = models.TextField(blank=True)
    elapsed_time = models.FloatField(default=0.0)
    execution_metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # 并行执行相关字段
    parallel_id = models.CharField(max_length=100, blank=True)
    parallel_start_node_id = models.CharField(max_length=100, blank=True)
    parent_parallel_id = models.CharField(max_length=100, blank=True)
    parent_parallel_start_node_id = models.CharField(max_length=100, blank=True)
    iteration_id = models.CharField(max_length=100, blank=True)
    loop_id = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['workflow_run', 'node_id']),
            models.Index(fields=['workflow_run', 'index']),
        ]
        ordering = ['workflow_run', 'index']


class AgentLog(models.Model):
    """存储代理执行日志"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_execution = models.ForeignKey(NodeExecution, on_delete=models.CASCADE, related_name='agent_logs')
    node_execution_id = models.UUIDField()  # 原始日志中的ID
    label = models.CharField(max_length=200)
    parent_id = models.UUIDField(null=True, blank=True)
    error = models.TextField(blank=True)
    status = models.CharField(max_length=20)  # start, success, error
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['node_execution']),
            models.Index(fields=['parent_id']),
        ]
        ordering = ['node_execution', 'created_at']


__all__ = [
    'AgentLog',
    'NodeExecution',
    'WorkflowRun'
]
