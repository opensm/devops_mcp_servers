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

    def create(self, request, *args, **kwargs):
        logger.debug(f"创建请求数据: {request.data}")
        try:
            stream_id = request.data.get('stream').get('id')
            WechatRobotQuestion.objects.get(stream_id=stream_id)
        except WechatRobotQuestion.DoesNotExist:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"创建数据失败: {str(e)}")
            return None