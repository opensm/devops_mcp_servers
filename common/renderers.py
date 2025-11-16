# renderers.py
import json
from rest_framework import renderers
from common.msg_crypt_helper import MsgCryptHelper
from django.conf import settings
from common.loger import logger


class FormattedResponseRenderer:
    """
    自定义渲染器，用于格式化响应数据
    """
    encode_object = MsgCryptHelper(
        sToken=settings.WECHAT_TOKEN,
        sEncodingAESKey=settings.WECHAT_ENCODING_AES_KEY,
        sReceiveId=""
    )

    def format_wechat_response(self, data, receiveid, nonce, timestamp, **kwargs):
        """
        :params data
        """
        if isinstance(data, dict):
            # 获取响应数据中的msgid
            stream_id = data.get('stream_id')
            # 获取响应数据中的aibotid
            finish = data.get('finish')
            # 获取响应数据中的chatid
            content = data.get('content')
        else:
            stream_id = "error_"
            content = "系统错误，请联系管理员"
            finish = True

        response_data = {
            "msgtype": "stream",
            "stream": {
                "id": stream_id,
                "finish": finish,
                "content": content,
            }
        }
        _data = self.encode_object.encrypt_message(
            receiveid=receiveid,
            nonce=nonce,
            timestamp=timestamp,
            data=response_data
        )
        return _data

    def format_other_data(self, content, stream_id, finish, receiveid, nonce, timestamp, **kwargs):
        """

        """
        data = {
            "msgtype": "stream",
            "stream": {
                "id": stream_id,
                "finish": finish,
                "content": content,
            }
        }
        _data = self.encode_object.encrypt_message(
            receiveid=receiveid,
            nonce=nonce,
            timestamp=timestamp,
            data=data
        )
        return _data


class EncryptedResponseRenderer(renderers.JSONRenderer, FormattedResponseRenderer):
    """
    自定义渲染器，用于加密响应数据
    """
    media_type = 'application/json'
    format = 'json'

    _error_message = "系统错误，请联系管理员"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # 获取请求和响应对象
        request = renderer_context['request']
        response = renderer_context['response']
        logger.debug(f"返回数据: {data}, media type {accepted_media_type} context {renderer_context}")
        # 从查询参数获取加密所需参数
        nonce = request.query_params.get('nonce')
        timestamp = request.query_params.get('timestamp')
        logger.debug(f"请求参数: {nonce}, {timestamp}")

        # 获取receiveid，可以从URL参数、请求头或设置中获取
        # 这里假设receiveid在URL参数中，如果没有则使用默认值
        receiveid = request.query_params.get('receiveid', '')

        # 设置响应头
        response['Content-Type'] = 'application/json'

        # 检查是否需要加密响应
        should_encrypt = all([nonce, timestamp]) and request.method in ['POST', 'PUT', 'PATCH']
        logger.debug(f"是否需要加密响应: {should_encrypt}")
        if not should_encrypt:
            logger.debug("请求类型不对，不需要加密响应")
            _data = self.format_other_data(
                content=self._error_message,
                stream_id="",
                finish=True,
                receiveid=receiveid,
                nonce=nonce,
                timestamp=timestamp
            )
            # 不需要加密，返回原始JSON数据
            return super().render(_data, accepted_media_type, renderer_context)
        # 加密响应数据
        try:
            encrypted_data = self.format_wechat_response(
                data,
                receiveid,
                nonce,
                timestamp
            )
            logger.debug(f"加密后的数据: {encrypted_data}")

            time_ = self.encode_object.decrypt_msg(
                encrypted_data='{"encrypt":"IOjxfCKyT1cn8zHF+2S0cN7oK+Cfq5UZTXr/0Tfdedddzs0BtvMM2WSh7KT4Ext7IuxrDVYg3OLs+TFAID7NPliXWZrsZv39ug5RLUDe84HS9emuOYR+rLFNMAJpFoItVAM1p5HkbncpOpsoKpriyPjChwy42Qc3bR8lnVebhWRNe7xiKxyNP1je12LzxqFK9YoVS3Hmv0gnnxnzVZIatCakLUBmts2rsfQIZL76HJDju1lQoBk6RuCWXEeSf8uogvx3PEKNQSYFtkw4dQSh5vOtDEFwOKf1np0TwK7em9/YbO7WA3vrb29rYSKGhu/JK7nNcH5p76aohNl9p1zil63dzhUSB/G++xodGW6jiTQOpTPDs36XOYVgUUn7t7xVfLAIGrmBQZ0PRyfTEJgqJehkibYMN8fNBVALK/RURQcjrp6k6Q7UHwF1PyLCSfg+5TOy61IYrN9ft9KwLGD9cj7DKVJtcBvUPC4hZhNoPxElaKR6oeHTBRGWtAv9wUafUfFdDrz0+eDL96U8YZqN0rSuvW0vzQFFN/8CXoqgCV0="}',
                msg_signature="6536e7a4e5b95a95567bff1030c3f32982765216",
                timestamp="1763271890",
                nonce="1762761344"
            )
            logger.debug(f"解密后的数据: {time_}")

            if not encrypted_data:
                # 返回加密后的数据
                raise Exception("加密失败，请联系管理员")
            return super().render(encrypted_data, accepted_media_type, renderer_context)
        except Exception as e:
            # 加密失败，记录错误但继续返回明文
            logger.error(f"响应加密失败: {str(e)}")
            # 如果不需要加密或加密失败，返回原始JSON数据
            _data = self.format_other_data(
                content=str(e),
                stream_id="",
                finish=True,
                receiveid=receiveid,
                nonce=nonce,
                timestamp=timestamp
            )
            return super().render(_data, accepted_media_type, renderer_context)
