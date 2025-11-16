import json
from rest_framework.generics import ListCreateAPIView
from wechat_robot.models import WechatRobotQuestionData, WechatRobotQuestion
from wechat_robot.serializers import WechatRobotQuestionDataSerializer, WechatRobotQuestionSerializer
from common.parsers import EncryptedDataParser
from common.renderers import EncryptedResponseRenderer
from common.loger import logger


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

    # def create(self, request, *args, **kwargs):
    #     logger.debug(f"创建请求数据: {request.data}")
    #     try:
    #         if request.data.get('msgtype', "") == "stream":
    #             stream_id = request.data.get('stream', {}).get('id', False)
    #             WechatRobotQuestion.objects.get(stream_id=stream_id)
    #             return super().create(request, *args, **kwargs)
    #         else:
    #             return super().create(request, *args, **kwargs)
    #     except WechatRobotQuestion.DoesNotExist:
    #         logger.warning(f"当前请求为流数据，但是未查询到数据: {request.data}")
    #         return super().create(request, *args, **kwargs)
    #     except Exception as e:
    #         logger.error(f"创建数据失败: {str(e)}")
    #         return super().create(request, *args, **kwargs)
    #
    # def perform_create(self, serializer):
    #     logger.debug(f"保存当前数据: {self.request.data}")
    #     if self.request.data.get('msgtype', '') == 'text':
    #         serializer.save()
