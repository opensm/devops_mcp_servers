# parsers.py
import json
from rest_framework import parsers
from common.msg_crypt_helper import MsgCryptHelper
from django.conf import settings


class EncryptedDataParser(parsers.JSONParser):
    """
    自定义解析器，用于解密加密的请求数据
    """

    def parse(self, stream, media_type=None, parser_context=None):
        # 先调用父类方法解析原始JSON数据
        parsed_data = super().parse(stream, media_type, parser_context)

        # 获取请求对象
        request = parser_context['request']

        # 从查询参数获取解密所需参数
        msg_signature = request.query_params.get('msg_signature')
        timestamp = request.query_params.get('timestamp')
        nonce = request.query_params.get('nonce')

        if not all([msg_signature, timestamp, nonce]):
            return parsed_data  # 如果没有必要参数，返回原始数据

        # 检查数据是否加密
        if 'encrypt' in parsed_data:
            # 初始化解密工具
            msg_crypt_helper = MsgCryptHelper(
                sToken=settings.WECHAT_TOKEN,
                sEncodingAESKey=settings.WECHAT_ENCODING_AES_KEY,
                sReceiveId=settings.WECHAT_CORP_ID_OR_APP_ID
            )

            # 解密数据
            try:
                encrypted_data = parsed_data['encrypt']
                decrypted_msg = msg_crypt_helper.decrypt_msg(
                    encrypted_data,
                    msg_signature,
                    timestamp,
                    nonce
                )

                # 解析解密后的JSON数据
                decrypted_data = json.loads(decrypted_msg)

                # 返回解密后的数据
                return decrypted_data
            except Exception as e:
                # 解密失败，返回原始数据
                return parsed_data

        return parsed_data