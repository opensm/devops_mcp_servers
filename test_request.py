#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信 AI 机器人模拟器
用于本地测试 demo_server.py
"""

import base64
import json
import time
import random
import hashlib
import requests
import os
from urllib.parse import urlencode

# 与 demo_server 使用完全相同的加密库
from common.req_libs.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt

# ========= 配置区 =========
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
BOTID = os.getenv("BOTID", "")
TOKEN = os.getenv("TOKEN", "")
ENCODING_AES_KEY = os.getenv("ENCODING_AES_KEY", "")

# ===========================

VERIFY_URL = f"{HOST}:{PORT}/ai-bot/callback/demo/{BOTID}"
RECV_ID = ""  # 企业微信机器人 receiveid 为空串


def gen_params():
    """生成时间戳、随机串"""
    return str(int(time.time())), str(random.randint(100000, 999999))


def calc_signature(token, ts, nonce, encrypt):
    """手工计算签名，用于验证 URL"""
    arr = [token, ts, nonce, encrypt]
    arr.sort()
    s = "".join(arr)
    return hashlib.sha1(s.encode()).hexdigest()


def verify_url():
    """Step1: 模拟企业微信的验证 URL GET 请求"""
    ts, nonce = gen_params()
    echo = base64.b64encode(b"hello").decode()  # 任意 base64
    sig = calc_signature(TOKEN, ts, nonce, echo)

    params = {"msg_signature": sig, "timestamp": ts, "nonce": nonce, "echostr": echo}
    resp = requests.get(VERIFY_URL, params=params)
    print("[verify] status:", resp.status_code, "echo:", resp.text)


def encrypt_msg(msg_json: str):
    """用官方库加密一条明文 json"""
    wxcpt = WXBizJsonMsgCrypt(TOKEN, ENCODING_AES_KEY, RECV_ID)
    ts, nonce = gen_params()
    ret, cipher = wxcpt.EncryptMsg(msg_json, nonce, ts)
    assert ret == 0, "加密失败"
    return cipher, ts, nonce


def decrypt_msg(cipher_json: str):
    """解密服务器回包"""
    wxcpt = WXBizJsonMsgCrypt(TOKEN, ENCODING_AES_KEY, RECV_ID)
    d = json.loads(cipher_json)
    ret, plain = wxcpt.DecryptMsg(cipher_json, d["msgsignature"], d["timestamp"], d["nonce"])
    assert ret == 0, "解密失败"
    return json.loads(plain)


def send_text(content: str):
    """模拟用户发送文本消息"""
    plain = {"msgtype": "text", "text": {"content": content}}
    cipher, ts, nonce = encrypt_msg(json.dumps(plain, ensure_ascii=False))
    sig = calc_signature(TOKEN, ts, nonce, json.loads(cipher)["encrypt"])

    params = {"msg_signature": sig, "timestamp": ts, "nonce": nonce}
    resp = requests.post(VERIFY_URL, params=params, data=cipher.encode())
    return decrypt_msg(resp.text)


def pull_stream(stream_id: str):
    """持续拉取流式回答"""
    while True:
        plain = {"msgtype": "stream", "stream": {"id": stream_id}}
        cipher, ts, nonce = encrypt_msg(json.dumps(plain, ensure_ascii=False))
        sig = calc_signature(TOKEN, ts, nonce, json.loads(cipher)["encrypt"])

        params = {"msg_signature": sig, "timestamp": ts, "nonce": nonce}
        resp = requests.post(VERIFY_URL, params=params, data=cipher.encode())
        back = decrypt_msg(resp.text)

        print("[stream] content:", back["stream"]["content"])
        if back["stream"]["finish"]:
            break
        time.sleep(1)


def send_image(img_path: str):
    """模拟用户上传加密图片（这里偷懒，直接传 base64 假装已加密）"""
    with open(img_path, "rb") as f:
        fake_cipher = base64.b64encode(f.read()).decode()
    plain = {"msgtype": "image", "image": {"url": "data:image/jpeg;base64," + fake_cipher}}
    cipher, ts, nonce = encrypt_msg(json.dumps(plain, ensure_ascii=False))
    sig = calc_signature(TOKEN, ts, nonce, json.loads(cipher)["encrypt"])

    params = {"msg_signature": sig, "timestamp": ts, "nonce": nonce}
    resp = requests.post(VERIFY_URL, params=params, data=cipher.encode())
    back = decrypt_msg(resp.text)
    print("[image] server returned an image, len=", len(back["stream"]["msg_item"][0]["image"]["base64"]))


def main():
    verify_url()

    print("\n====== 文本对话测试 ======")
    ret = send_text("今天深圳天气如何？")
    stream_id = ret["stream"]["id"]
    pull_stream(stream_id)

    print("\n====== 图片回显测试 ======")
    # 任意找一张小图即可
    send_image("test.jpg")


if __name__ == "__main__":
    main()
