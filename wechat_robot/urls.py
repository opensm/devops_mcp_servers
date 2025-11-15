from django.urls import path
from wechat_robot.views import WechatRobotQuestionView

url_list = [
    path('/callback/demo/1111', WechatRobotQuestionView.as_view()),
]
