import json
from rest_framework.generics import ListCreateAPIView
from wechat_robot.models import WechatRobotQuestionData, WechatRobotQuestion
from wechat_robot.serializers import WechatRobotQuestionDataSerializer, WechatRobotQuestionSerializer
from common.parsers import EncryptedDataParser
from common.renderers import EncryptedResponseRenderer
from common.loger import logger
from django.db import transaction


class WechatRobotQuestionDataView(ListCreateAPIView):
    serializer_class = WechatRobotQuestionDataSerializer
    queryset = WechatRobotQuestionData.objects.all()
    model = WechatRobotQuestionData
    renderer_classes = [EncryptedResponseRenderer]


class WechatRobotQuestionView(ListCreateAPIView):
    queryset = WechatRobotQuestion.objects.all()
    serializer_class = WechatRobotQuestionSerializer
    parser_classes = [EncryptedDataParser]
    renderer_classes = [EncryptedResponseRenderer]

    @transaction.atomic  # 可选，保证并发安全
    def perform_create(self, serializer):
        if serializer.validated_data.get('msgtype', "") == "stream":
            try:
                stream_id = serializer.validated_data.get('stream', {}).get('id', False)
                robt_instance = WechatRobotQuestion.objects.get(stream=stream_id)
            except WechatRobotQuestion.DoesNotExist:
                logger.error(f"当前请求为流数据，但是未查询到数据: {serializer.validated_data}")
        else:
            logger.debug(f"保存数据: {serializer.validated_data}")
            serializer.save()

        # # 利用唯一索引，先查是否存在
        # if WechatRobotQuestion.objects.filter(sku_code=sku_code).exists():
        #     # 已存在 -> 静默跳过，不再 save
        #     return
        # # 不存在 -> 真正创建
        # serializer.save()