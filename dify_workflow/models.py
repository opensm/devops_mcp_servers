import uuid
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from wechat_robot.models import WechatRobotQuestion


class WorkflowTask(models.Model):
    """存储工作流运行的基本信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    robot_task = models.ForeignKey(
        WechatRobotQuestion,
        verbose_name="机器人ID", on_delete=models.CASCADE, related_name='workflow_runs', null=True
    )
    conversation_id = models.UUIDField(verbose_name="运行ID")
    message_id = models.UUIDField(verbose_name="消息ID")
    task_id = models.UUIDField(verbose_name="任务ID")
    workflow_run_id = models.UUIDField(verbose_name="工作流运行ID", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['task_id']),
            models.Index(fields=['workflow_run_id']),
            models.Index(fields=['created_at']),
        ]


class WorkflowRunData(models.Model):
    """存储节点执行信息"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_run = models.ForeignKey(WorkflowTask, on_delete=models.CASCADE, related_name='data')
    event = models.CharField(max_length=100, verbose_name="事件", default="workflow_started")
    node_id = models.CharField(max_length=100, blank=True, null=True)
    node_type = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    index = models.IntegerField(blank=True, null=True)
    predecessor_node_id = models.CharField(max_length=100, blank=True, null=True)
    inputs = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    process_data = models.TextField(blank=True, null=True)
    outputs = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    status = models.CharField(max_length=20, default='running', blank=True, null=True)  # running, succeeded, failed
    error = models.TextField(blank=True, null=True)
    elapsed_time = models.FloatField(default=0.0, blank=True, null=True)
    execution_metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True, verbose_name="模型数据")
    created_at = models.BigIntegerField(null=True, blank=True)
    finished_at = models.BigIntegerField(null=True, blank=True)

    # 并行执行相关字段
    parallel_id = models.CharField(max_length=100, blank=True, null=True)
    parallel_start_node_id = models.CharField(max_length=100, blank=True, null=True)
    parent_parallel_id = models.CharField(max_length=100, blank=True, null=True)
    parent_parallel_start_node_id = models.CharField(max_length=100, blank=True, null=True)
    iteration_id = models.CharField(max_length=100, blank=True, null=True)
    loop_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['workflow_run', 'node_id']),
            models.Index(fields=['workflow_run', 'index']),
        ]
        ordering = ['workflow_run', 'index']


class AgentLog(models.Model):
    """存储代理执行日志"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_execution_id = models.UUIDField()  # 原始日志中的ID
    label = models.CharField(max_length=200, blank=True, default="")
    node_id = models.CharField(max_length=100, blank=True, default="")
    parent_id = models.UUIDField(null=True, blank=True)
    error = models.TextField(blank=True)
    status = models.CharField(max_length=20)  # start, success, error
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['node_execution_id']),
            models.Index(fields=['parent_id']),
        ]
        ordering = ['node_execution_id', 'created_at']


__all__ = [
    'AgentLog',
    'WorkflowRunData',
    'WorkflowTask'
]
