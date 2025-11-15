# utils/msg_crypt_helper.py
import base64
from common.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt  # 根据您实际使用的库导入
from common.loger import logger
import json


class MsgCryptHelper:
    def __init__(self, sToken, sEncodingAESKey, sReceiveId):
        """
        初始化消息加密解密助手
        :param sToken: 企业微信后台设置的Token
        :param sEncodingAESKey: 企业微信后台设置的EncodingAESKey
        :param sReceiveId: 企业微信的CorpId或者AppId
        """
        self.token = sToken
        self.encoding_aes_key = sEncodingAESKey
        self.receiveid = sReceiveId
        self.wxcpt_json = WXBizJsonMsgCrypt(sToken, sEncodingAESKey, sReceiveId)
        self.wxcpt = WXBizJsonMsgCrypt(sToken, sEncodingAESKey, sReceiveId)

    def decrypt_msg(self, encrypted_data, msg_signature, timestamp, nonce):
        """
        解密消息
        :param encrypted_data: 加密的消息体
        :param msg_signature: 消息签名
        :param timestamp: 时间戳
        :param nonce: 随机数
        :return: 解密后的明文消息
        """
        ret, decrypted_msg = self.wxcpt.DecryptMsg(
            encrypted_data,
            msg_signature,
            timestamp,
            nonce
        )
        if ret != 0:
            raise Exception(f'Decrypt message failed, error code: {ret}')
        return decrypted_msg

    def encrypt_message(self, receiveid, nonce, timestamp, data):
        """
        加密消息
        :param receiveid: 接收者ID
        :param nonce: 随机字符串
        :param timestamp: 时间戳
        :param data: 要加密的数据（字典或JSON字符串）
        :return: 加密后的消息
        """
        logger.info("开始加密消息，receiveid=%s, nonce=%s, timestamp=%s", receiveid, nonce, timestamp)

        # 确保数据是JSON字符串
        if isinstance(data, dict):
            stream = json.dumps(data)
        else:
            stream = data

        logger.debug("发送流消息: %s", stream)

        ret, resp = self.wxcpt_json.EncryptMsg(stream, nonce, timestamp)
        logger.debug("加密结果: %d %s", ret, resp)
        if ret != 0:
            logger.error("加密失败，错误码: %d", ret)
            return None

        # 记录加密完成信息
        try:
            data_dict = json.loads(stream)
            if 'stream' in data_dict and 'id' in data_dict['stream']:
                stream_id = data_dict['stream']['id']
                finish = data_dict['stream'].get('finish', False)
                logger.info("回调处理完成, 返回加密的流消息, stream_id=%s, finish=%s", stream_id, finish)
        except Exception as e:
            logger.warning("解析stream信息失败: %s", e)

        logger.debug("加密后的消息: %s", resp)
        return resp
