from rest_framework import serializers
from dify_workflow.models import *
from common.loger import logger
from uuid import UUID


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = '__all__'


class WorkflowRunDataSerializer(serializers.ModelSerializer):
    workflow_run = serializers.PrimaryKeyRelatedField(queryset=WorkflowTask.objects.all(), required=False)

    class Meta:
        model = WorkflowRunData
        fields = '__all__'
        extra_kwargs = {
            'workflow_run': {'validators': []},  # 把默认的 UniqueValidator 摘掉
        }


class WorkflowTaskSerializer(serializers.ModelSerializer):
    data = WorkflowRunDataSerializer(required=False)
    event = serializers.CharField(max_length=100, default="workflow_started")

    class Meta:
        model = WorkflowTask
        fields = '__all__'
        extra_kwargs = {'robot_task': {'validators': []}}

        # ---------------- 主入口 ----------------

    def create(self, validated_data: dict):
        logger.info(f"开始处理机器人任务 data={validated_data}")
        lookup_fields, defaults = self._split_fields(validated_data)
        self._coerce_types(lookup_fields)  # 仅对查询键做类型转换
        task, created = WorkflowTask.objects.update_or_create(
            defaults=defaults,
            **lookup_fields
        )
        logger.info(f"WorkflowTask {'新建' if created else '更新'}完成, id={task.id}")

        self._create_run_data(task, validated_data)
        return task

    # ---------- 辅助方法 ----------
    @staticmethod
    def _checkout_message_event(lookup_fields: dict, defaults: dict, event: str):

        try:
            if event != "message":
                return lookup_fields, defaults
            task = WorkflowTask.objects.get(**lookup_fields)
            if not defaults['answer'] and task.answer:
                defaults['answer'] = task.answer
            return lookup_fields, defaults
        except WorkflowTask.DoesNotExist:
            return lookup_fields, defaults

    def _split_fields(self, validated_data: dict):
        """返回 (用于查询的字段, 用于更新的字段)"""
        lookup_keys = {'conversation_id', 'message_id', 'task_id'}
        lookup_fields, defaults = {}, {}
        for field in self.Meta.model._meta.fields:
            if field.name in validated_data:
                target = lookup_fields if field.name in lookup_keys else defaults
                target[field.name] = validated_data[field.name]
        return self._checkout_message_event(lookup_fields, defaults, validated_data.get('event', ''))

    def _coerce_types(self, lookup: dict):
        """把字符串 UUID 转成 UUID 对象"""
        for key in ('conversation_id', 'message_id', 'task_id'):
            if key in lookup and isinstance(lookup[key], str):
                lookup[key] = UUID(lookup[key])

    def _get_attrs(self, validated_data: dict):
        """
        """
        message_data = validated_data.pop('data', {})
        for key in ('event', 'answer', 'metadata'):
            if key not in validated_data:
                continue
            if key == 'answer':
                message_data["output"] = {"answer": validated_data[key]}
            else:
                message_data[key] = validated_data.pop(key)
        return message_data

    def _create_run_data(self, task: WorkflowTask, validated_data: dict):
        """"""
        try:
            data = self._get_attrs(validated_data)
            if data == {}:
                raise ValueError("数据为空")
            data.update(dict(
                workflow_run=task.id
            ))
            serializer = WorkflowRunDataSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except Exception as e:
            logger.error(f"处理机器人任务失败：{e}")

    # def create(self, validated_data):
    #     """
    #     整个 JSON 里只有 Category + 它的 products。
    #     用 update_or_create 处理 Category，
    #     """
    #     logger.info(f"开始处理机器人任务 data={validated_data}")
    #     # 处理外部参数
    #     _task_params = dict()
    #     data = validated_data.pop('data', None)
    #     event = validated_data.pop('event', '')
    #     primary_fields_data = dict()
    #     for index in self.Meta.model._meta.get_fields():
    #         logger.debug(f"当前字段: {index.name}")
    #         if index.name in ['id', 'created_at', 'updated_at']:
    #             continue
    #         elif not hasattr(index, 'blank'):
    #             continue
    #         if not index.blank:
    #             if index.name not in validated_data.keys():
    #                 logger.error(f"参数 {index.name} 丢失")
    #                 continue
    #             primary_fields_data[index.name] = validated_data.pop(index.name)
    #             logger.debug(f"当前主键字段: {index.name} 值: {primary_fields_data[index.name]}")
    #         else:
    #             if index.name not in validated_data.keys():
    #                 continue
    #             _task_params[index.name] = validated_data.pop(index.name)
    #
    #     logger.info(f"获取到的外部参数: {_task_params},获得的主键参数: {primary_fields_data}")
    #     dify_task, _ = WorkflowTask.objects.update_or_create(
    #         defaults=_task_params,
    #         **primary_fields_data
    #     )
    #     try:
    #         if event == 'message':
    #             data = {"output": {"answer": _task_params['answer']}}
    #         else:
    #             if data is None: return dify_task
    #         data['workflow_run'] = dify_task
    #         data['event'] = event
    #         serializer = WorkflowRunDataSerializer(data=data)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         logger.info(f"处理机器人任务 id={dify_task.id}完成")
    #     except Exception as e:
    #         logger.error(f"处理机器人任务失败：{e}")
    #     return dify_task


__all__ = [
    'AgentLogSerializer',
    'WorkflowRunDataSerializer',
    'WorkflowTaskSerializer'
]
