#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人回调模拟器
与Django视图（@csrf_exempt + request.body）配套测试
"""
import base64, json, time, random, hashlib, requests, os
from common.req_libs.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt
import random
import string

# ================= 配置 =================
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
BOTID = os.getenv("BOTID", "1111")
TOKEN = os.getenv("WECHAT_TOKEN", "")
ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY", "")
assert TOKEN and ENCODING_AES_KEY, "请先设置 WECHAT_TOKEN 和 WECHAT_ENCODING_AES_KEY"
HOST = f"http://{HOST}:{PORT}"
RECVID = ""  # 机器人receiveid为空

# ============= 新增日志 ============
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ====================================

def gen_ts_nonce():
    ts, nonce = str(int(time.time())), str(random.randint(100000, 999999))
    logger.debug("gen_ts_nonce: ts=%s, nonce=%s", ts, nonce)
    return ts, nonce


def calc_sig(token, ts, nonce, encrypt):
    arr = [token, ts, nonce, encrypt]
    arr.sort()
    sig = hashlib.sha1("".join(arr).encode()).hexdigest()
    logger.debug("calc_sig: input=%s, sig=%s", arr, sig)
    return sig


def encrypt_msg(plain_json: str):
    ts, nonce = gen_ts_nonce()
    wxcpt = WXBizJsonMsgCrypt(TOKEN, ENCODING_AES_KEY, RECVID)
    ret, cipher = wxcpt.EncryptMsg(plain_json, nonce, ts)
    assert ret == 0, "加密失败"
    logger.debug("encrypt_msg: plain=%s, cipher=%s", plain_json, cipher)
    return cipher, ts, nonce


def decrypt_msg(cipher_text: str):
    d = json.loads(cipher_text)
    wxcpt = WXBizJsonMsgCrypt(TOKEN, ENCODING_AES_KEY, RECVID)
    ret, plain = wxcpt.DecryptMsg(cipher_text, d["msgsignature"], d["timestamp"], d["nonce"])
    assert ret == 0, f"解密失败 ret={ret}"
    logger.debug("decrypt_msg: cipher=%s, plain=%s", cipher_text, plain)
    return json.loads(plain)


def post_plain(cipher_text: str):
    url = f"{HOST}/ai-bot/callback/demo/{BOTID}"
    ts, nonce = gen_ts_nonce()
    sig = calc_sig(TOKEN, ts, nonce, json.loads(cipher_text)["encrypt"])
    params = {"msg_signature": sig, "timestamp": ts, "nonce": nonce}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/4.0"
    }
    logger.debug("post_plain: url=%s, params=%s, headers=%s, body=%s",
                 url, params, headers, cipher_text)
    r = requests.post(url, params=params, data=cipher_text, headers=headers)
    logger.debug("post_plain: status=%s, response=%s", r.status_code, r.text)
    return r


def generate_hex_string(length=32):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))


# def send_text(content: str):
#     plain = {"msgtype": "text", "text": {"content": content}}
#     cipher, _, _ = encrypt_msg(json.dumps(plain, ensure_ascii=False))
#     resp = post_plain(cipher)
#     return decrypt_msg(resp.text)

def send_text(content: str):
    """模拟用户发送文本消息"""
    url = f"{HOST}/ai-bot/callback/demo/{BOTID}"
    msg_id = generate_hex_string()
    robot_id = "aibrGalbJc-O4nrQRGAGLjNTIk8P"
    chat_id = "wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ"
    chat_type = "single"
    chat_from = {'userid': 'ky005509'}
    plain = {
        'msgid': msg_id, 'aibotid': robot_id,
        'chattype': 'single', 'from': {'userid': 'ky005509'}, 'msgtype': 'text',
        'text': {'content': content}
    }
    cipher, ts, nonce = encrypt_msg(json.dumps(plain, ensure_ascii=False))
    sig = calc_sig(TOKEN, ts, nonce, json.loads(cipher)["encrypt"])

    params = {"msg_signature": sig, "timestamp": ts, "nonce": nonce}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/4.0"
    }
    resp = requests.post(url, params=params, data=cipher.encode(), headers=headers)
    return decrypt_msg(resp.text), msg_id


def pull_stream(stream_id: str, msg_id):
    while True:
        msg_id = generate_hex_string()
        plain = {
            "msgid": msg_id,
            "chattype": "single",
            "from": {"userid": "ky005509"},
            "msgtype": "stream",
            "stream": {"id": stream_id},
            "chatid": "wrck4BDQAAWHKnqDvlif4Mp9tYXHMuuQ",
            "aibotid": "aibrGalbJc-O4nrQRGAGLjNTIk8P"
        }
        cipher, _, _ = encrypt_msg(json.dumps(plain, ensure_ascii=False))
        resp = post_plain(cipher)
        back = decrypt_msg(resp.text)
        logger.info("[STREAM] %s", back["stream"]["content"])
        if back["stream"]["finish"]:
            break
        time.sleep(1)


def main():
    logger.info("=== 文本对话 ===")
    back, msg_id = send_text("你好，你是谁，你能做什么？")
    pull_stream(back["stream"]["id"], msg_id)


if __name__ == "__main__":
    main()
