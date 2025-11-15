# renderers.py
import json
from rest_framework import renderers
from common.msg_crypt_helper import MsgCryptHelper
from django.conf import settings
from common.loger import logger


class EncryptedResponseRenderer(renderers.JSONRenderer):
    """
    自定义渲染器，用于加密响应数据
    """
    media_type = 'application/json'
    format = 'json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # 获取请求和响应对象
        request = renderer_context['request']
        response = renderer_context['response']
        logger.debug(f"返回数据: {data}")
        logger.debug(f"返回数据: {data}, media type {accepted_media_type} context {renderer_context}")
        # 从查询参数获取加密所需参数
        nonce = request.query_params.get('nonce')
        timestamp = request.query_params.get('timestamp')
        logger.debug(f"请求参数: {nonce}, {timestamp}")

        # 获取receiveid，可以从URL参数、请求头或设置中获取
        # 这里假设receiveid在URL参数中，如果没有则使用默认值
        receiveid = request.query_params.get('receiveid', '')

        # 检查是否需要加密响应
        should_encrypt = all([nonce, timestamp]) and request.method in ['POST', 'PUT', 'PATCH']
        logger.debug(f"是否需要加密响应: {should_encrypt}")

        if should_encrypt:
            # 初始化加密工具
            msg_crypt_helper = MsgCryptHelper(
                sToken=settings.WECHAT_TOKEN,
                sEncodingAESKey=settings.WECHAT_ENCODING_AES_KEY,
                sReceiveId=settings.WECHAT_CORP_ID_OR_APP_ID
            )
            logger.debug(f"初始化加密工具: {msg_crypt_helper}")

            # 加密响应数据
            try:
                encrypted_data = msg_crypt_helper.encrypt_message(
                    receiveid, nonce, timestamp, data
                )
                logger.debug(f"加密后的数据: {encrypted_data}")

                if encrypted_data:
                    # 返回加密后的数据
                    response['Content-Type'] = 'application/json'
                    return super().render(encrypted_data, accepted_media_type, renderer_context)
            except Exception as e:
                # 加密失败，记录错误但继续返回明文
                logger.error(f"响应加密失败: {str(e)}")

        # 如果不需要加密或加密失败，返回原始JSON数据
        return super().render(data, accepted_media_type, renderer_context)
