from rest_framework.generics import ListCreateAPIView
from wechat_robot.models import WechatRobotQuestionData, WechatRobotQuestion
from wechat_robot.serializers import WechatRobotQuestionDataSerializer, WechatRobotQuestionSerializer
from common.req_libs.parsers import EncryptedDataParser
from common.req_libs.renderers import EncryptedResponseRenderer
from django.http import HttpResponse


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


def health_check(request, *args, **kwargs):
    return HttpResponse(content="OK", status=200)
