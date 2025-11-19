import json
from dify_client import ChatClient
from django.core.serializers import serialize

from devops_mcp_servers.settings import DIFY_API_KEY, DIFY_API_URL
from common.loger import logger
from typing import Dict, Any
from wechat_robot.models import WechatRobotQuestion
from dify_workflow.serializers import WorkflowTaskSerializer


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

    def process_event(self, event: Dict[str, Any]):
        """
        处理Dify事件

        Args:
            event (Dict[str, Any]): Dify事件

        Returns:
            str: 处理结果
        """
        pass

    @staticmethod
    def process_stream_response(response, task_key, **kwargs):
        """
        处理流式响应数据

        Args:
            response: 流式响应对象
            task_key(str): 任务关键字
        """
        try:
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                # 检查是否为数据行
                if not line.startswith('data:') and not line.startswith('event:'):
                    logger.warning(f"当前任务存在异常数据：${line}，跳过！")
                    continue
                try:
                    # 提取JSON部分
                    if not line.startswith('data:'):
                        continue
                    json_data = line[5:].strip()
                    if not json_data:
                        logger.warning(f"当前任务:${task_key} 获取到的dify任务数据为空，跳过！")
                        continue
                    logger.debug(f"当前任务:${task_key} 获取到的dify任务数据为：{json_data}")
                    data = json.loads(json_data)
                    if data is None:
                        logger.warning(f"当前任务:${task_key} 获取到的dify任务数据为空，跳过！")
                        continue
                    if data.get('event') not in ['message', 'message_end', 'workflow_finished', 'node_finished']:
                        logger.debug(f"dify_收到当前返回的数据为：{data}")
                        continue
                    if "instance" not in kwargs.keys():
                        logger.error(f"当前任务:${task_key} 获取到的dify任务数据为空，跳过！")
                    instance = kwargs.get("instance", None)
                    if instance is None:
                        logger.error(f"当前任务:${task_key} 获取到的dify任务数据为空，跳过！")
                        continue
                    data["robot_task"] = instance
                    serializer = WorkflowTaskSerializer(data=data, many=False)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    json_dump_data = json.dumps(data, indent=4)
                    logger.info(f"当前任务:${task_key} 获取到的dify任务数据为：\n {json_dump_data}")
                except json.JSONDecodeError as e:
                    # 记录JSON解析错误但不中断流
                    logger.error(f"当前任务, [JSON解析错误: {e}]", end='')
        except Exception as e:
            logger.error(f"[流处理错误: {e}]")

        finally:
            print()

    def chat(self, query, task_key, user_id="user_id", inputs=None, **kwargs):
        """
        发送消息并处理响应的完整流程

        Args:
            query (str): 查询内容
            task_key(str): 任务关键字
            user_id (str): 用户ID
            inputs (dict): 输入参数
        """
        logger.debug(f"开始发送dify工作流请求: {query}, {kwargs}, {task_key}........")
        response = self.send_message(query=query, user_id=user_id, inputs=inputs)
        return self.process_stream_response(
            response=response,
            task_key=task_key,
            **kwargs
        )

    def run_workflow(self, stream_id):
        """
        运行工作流
        """
        try:
            rebot_data = WechatRobotQuestion.objects.get(stream=stream_id)
            logger.info(f"任务：{rebot_data.stream} 运行中...")
            self.chat(
                query=rebot_data.text,
                task_key=str(rebot_data.stream.bytes),
                user_id=rebot_data.chat_from,
                instance=rebot_data
            )
        except WechatRobotQuestion.DoesNotExist:
            logger.error(f"任务不存在：{stream_id}")
            return
