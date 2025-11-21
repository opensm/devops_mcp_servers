from django.urls import path
from wechat_robot.views import WechatRobotQuestionView
from wechat_robot.views import health_check

url_list = [
    path('callback/demo/1111', WechatRobotQuestionView.as_view()),
    path('healthy', health_check),
]
