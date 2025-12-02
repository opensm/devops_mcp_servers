import json
import time
from dify_client import ChatClient
from django.db import transaction, OperationalError

from devops_mcp_servers.settings import DIFY_API_KEY, DIFY_API_URL
from common.loger import logger
from typing import Dict, Any
from wechat_robot.models import WechatRobotQuestion
from dify_workflow.serializers import WorkflowTaskSerializer
from dify_workflow.models import WorkflowRunData
from django.utils import timezone
from devops_mcp_servers import settings
from common.error import DataKeyError, DataValueError, DataTypeError, DataNOtFound, DataBaseException


class DifyChatClient:
    """
    Dify聊天客户端类，用于与Dify API进行交互
    """

    def __init__(self):
        """
        初始化Dify聊天客户端
        Args:
        """
        self.chat_client = ChatClient(DIFY_API_KEY)
        self.chat_client.base_url = DIFY_API_URL

    def send_message(self, query, user_id="user_id", inputs=None, response_mode="streaming"):
        """
        发送消息到Dify API

        Args:
            query (str): 查询内容
            user_id (str): 用户ID
            inputs (dict): 输入参数
            response_mode (str): 响应模式

        Returns:
            response: API响应对象
        """
        if inputs is None:
            inputs = {}

        response = self.chat_client.create_chat_message(
            inputs=inputs,
            query=query,
            user=user_id,
            response_mode=response_mode
        )
        logger.debug("发送dify工作流请求........")
        response.raise_for_status()
        return response

    # ---------------- 批处理入口（串行） ----------------
    def modify_status_runner(self):
        candidates = list(
            WechatRobotQuestion.objects.filter(finish=False)[:5]
        )
        if not candidates:
            logger.debug("没有待处理机器人任务，本轮空跑。")
            return

        for candidate in candidates:
            try:
                # 单条任务一个事务，出错不影响别的
                with transaction.atomic():
                    self.modify_worker_status(candidate.stream)
            except OperationalError as e:
                # SQLite 锁冲突，等 200ms 再试一次
                logger.warning("SQLite locked, retry %s", candidate.stream)
                time.sleep(0.2)
                try:
                    with transaction.atomic():
                        self.modify_worker_status(candidate.stream)
                except Exception as e:
                    logger.exception("更新任务失败: %s", e)
            except Exception as e:
                logger.exception("更新任务失败: %s", e)

    # ---------------- 单条任务状态机 ----------------
    def modify_worker_status(self, stream_id: str) -> bool:
        # SQLite 下不再 select_for_update
        WechatRobotQuestion.objects.filter(stream=stream_id, status="failed").update(
            finish=True,
            status="failed",
            content="机器人处理失败，请稍后再试……"
        )

        try:
            task = WechatRobotQuestion.objects.get(stream=stream_id)
        except WechatRobotQuestion.DoesNotExist:
            logger.error("任务不存在 stream=%s", stream_id)
            return False

        if task.status in ("failed", "succeeded"):
            return True

        # 1. 超时失败
        timeout = int(getattr(settings, "ANSWER_TIMEOUT", 120))
        if (timezone.now() - task.create_time).total_seconds() > timeout:
            # 只写一次，减少锁冲突
            rows = WechatRobotQuestion.objects.filter(
                stream=stream_id, finish=False
            ).update(
                finish=True, status="failed",
                content="机器人处理超时，请稍后再试……"
            )
            if rows:  # 更新成功才打日志
                logger.info("stream=%s 已标为超时失败", stream_id)
            return True

        # 2. 中间节点失败
        if WorkflowRunData.objects.filter(
                workflow_run__robot_task_id=task.id,
                status="failed"
        ).exists():
            rows = WechatRobotQuestion.objects.filter(
                stream=stream_id, finish=False
            ).update(
                finish=True, status="failed",
                content="机器人执行失败，请稍后再试"
            )
            if rows:
                logger.info("stream=%s 存在中间节点失败，已标为失败", stream_id)
            return True

        # 3. message_end → 成功
        if WorkflowRunData.objects.filter(
                workflow_run__robot_task_id=task.id,
                event="message_end"
        ).exists():
            content = self._get_latest_content(task.id)
            rows = WechatRobotQuestion.objects.filter(
                stream=stream_id, finish=False
            ).update(
                finish=True, status="succeeded",
                content=content
            )
            if rows:
                logger.info("stream=%s 收到 message_end，已标为成功", stream_id)
            return True

        # 4. 运行中，仅刷新内容
        if task.status == "running":
            content = self._get_latest_content(task.id)
            # 只更新 content，不碰终态字段，减少锁时间
            WechatRobotQuestion.objects.filter(pk=task.id).update(content=content)
        return True

    # ---------------- 工具：拿最新内容 ----------------
    @staticmethod
    def _get_latest_content(task_id: int) -> str:
        """
        取当前机器人任务最后一条有效 answer：
        1. 优先拿 message_end 同一次 run 里最新一条 message；
        2. 没有则拿最新一条 message；
        3. 再没有才兜底。
        """
        # 先找到收到 message_end 的那条 run（可能不存在）
        end = (WorkflowRunData.objects.filter(
            workflow_run__robot_task_id=task_id,
            event="message_end").first())
        if end:
            # 同一次 run 里最新一条 message
            msg = (WorkflowRunData.objects
                   .filter(workflow_run_id=end.workflow_run_id, event="message")
                   .order_by("-id")
                   .first())
            if msg and msg.workflow_run.answer:
                return msg.workflow_run.answer

        # 没取到就退而求其次：最新任意一条 message
        latest_msg = (WorkflowRunData.objects
                      .select_related("workflow_run")
                      .filter(workflow_run__robot_task_id=task_id, event="message")
                      .order_by("-id")
                      .first())
        if latest_msg and latest_msg.workflow_run.answer:
            return latest_msg.workflow_run.answer
        # 兜底
        return "大模型正在处理中……"

    @staticmethod
    def process_stream_response(response, instance: WechatRobotQuestion, **kwargs):
        """
        处理流式响应数据

        Args:
            response: 流式响应对象
            instance(str): 任务关键字
        """
        if instance is None:
            return
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                # 提取JSON部分
                if not line.startswith('data:'):
                    raise DataTypeError("非工作流数据")
                json_data = line[5:].strip()
                if not json_data:
                    raise DataNOtFound(f"当前任务:${instance.stream} 获取到的dify任务数据为空，跳过！")
                data = json.loads(json_data)
                if data.get('event', '') not in ['message', 'message_end', 'workflow_finished', 'node_finished']:
                    raise DataTypeError(f"当前的事件类型为：{data.get('event', '')}")
                data["robot_task"] = instance.pk
                logger.info(f"当前任务:id {instance.pk} ${instance.stream} 获取到的dify任务数据为：\n {data}")
                serializer = WorkflowTaskSerializer(data=data, many=False)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                json_dump_data = json.dumps(data, indent=4)
                logger.debug(f"获取到的dify任务数据为：\n {json_dump_data}")
                logger.info(f"当前任务:${instance.stream}更新数据到系统成功！")
            except DataBaseException:
                continue
            except json.JSONDecodeError as e:
                # 记录JSON解析错误但不中断流
                logger.error(f"当前任务, [JSON解析错误: {e}]", end='')
                instance.status = 'failed'
                instance.save()
            except Exception as e:
                logger.error(f"[流处理错误: {e}]")
                instance.status = 'failed'
                instance.save()
            finally:
                print()

    def check_workflow_run(self, instance: WechatRobotQuestion):
        if not instance.workflow_runs:
            instance.status = 'failed'
            instance.stream = '大模型调用异常，请稍后再试……'
            instance.finish = True
            instance.save()
            return
        if not instance.workflow_runs.data.all():
            instance.status = 'failed'
            instance.stream = '大模型调用异常，请稍后再试……'
            instance.finish = True
            instance.save()
            return

    def chat(self, query, instance: WechatRobotQuestion, user_id="user_id", inputs=None, **kwargs):
        """
        发送消息并处理响应的完整流程

        Args:
            query (str): 查询内容
            instance(str): 机器人任务实例
            user_id (str): 用户ID
            inputs (dict): 输入参数
        """
        logger.debug(f"开始发送dify工作流请求: {query}, {kwargs}, {instance.stream}........")
        response = self.send_message(query=query, user_id=user_id, inputs=inputs)
        return self.process_stream_response(
            response=response,
            instance=instance,
            **kwargs
        )

    def run_workflow(self, stream_id):
        """
        运行工作流
        """
        try:
            rebot_data = WechatRobotQuestion.objects.get(stream=stream_id)
            self.chat(
                query=rebot_data.text,
                user_id=rebot_data.chat_from,
                instance=rebot_data
            )
        except WechatRobotQuestion.DoesNotExist:
            logger.error(f"任务不存在：{stream_id}")
            return
