# fields.py
from rest_framework import serializers
from common.req_libs.msg_crypt_helper import MsgCryptHelper
from django.conf import settings


class EncryptedField(serializers.CharField):
    """
    自定义字段，用于解密加密的数据
    """

    def to_internal_value(self, data):
        # 获取请求上下文
        request = self.context.get('request')

        if request and isinstance(data, str) and data.startswith('encrypted:'):
            # 从查询参数获取解密所需参数
            msg_signature = request.query_params.get('msg_signature')
            timestamp = request.query_params.get('timestamp')
            nonce = request.query_params.get('nonce')

            if all([msg_signature, timestamp, nonce]):
                # 初始化解密工具
                msg_crypt_helper = MsgCryptHelper(
                    sToken=settings.WECHAT_TOKEN,
                    sEncodingAESKey=settings.WECHAT_ENCODING_AES_KEY,
                    sReceiveId=settings.WECHAT_CORP_ID_OR_APP_ID
                )

                # 解密数据
                try:
                    encrypted_data = data.replace('encrypted:', '')
                    decrypted_msg = msg_crypt_helper.decrypt_msg(
                        encrypted_data,
                        msg_signature,
                        timestamp,
                        nonce
                    )

                    # 返回解密后的数据
                    return decrypted_msg
                except Exception as e:
                    # 解密失败，返回原始数据
                    pass

        return super().to_internal_value(data)