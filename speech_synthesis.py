# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#   合成小语种需要传输小语种文本、使用小语种发音人vcn、tte=unicode以及修改文本编码方式
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
import re

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"aue": "lame" , "sfl": 1, "auf": "audio/L16;rate=16000", "vcn": "xiaoyan", "tte": "utf8"}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
        #使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE""
        #self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}

    # 生成url
    def create_url(self):  # 这里需要正确的缩进
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 修正：使用正确的host
        signature_origin = "host: " + "tts-api.xfyun.cn" + "\n"  # 注意这里应该是tts-api而不是ws-api
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "tts-api.xfyun.cn"  # 修正host
        }
        
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        return url

# 生成安全的TTS文件名 - 这个函数应该在类外部
def generate_safe_tts_filename(text, base_dir="./static/file/"):
    """生成安全的TTS文件名"""
    # 确保目录存在
    os.makedirs(base_dir, exist_ok=True)
    
    # 生成安全的时间戳（无空格）
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    
    # 清理文本
    clean_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_-]', '', text)
    if not clean_text:
        clean_text = "speech"
    else:
        clean_text = clean_text[:20]
    
    filename = f"{timestamp}-{clean_text}.mp3"
    return os.path.join(base_dir, filename)



ws = None
def on_message(ws, message):
    try:
        message =json.loads(message)
        code = message["code"]
        sid = message["sid"]
        audio = message["data"]["audio"]
        audio = base64.b64decode(audio)
        status = message["data"]["status"]
        print(message)
        if status == 2:
            print("ws is closed")
            ws.close()
        if code != 0:
            errMsg = message["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:

            with open(ws.tts_file,mode='ab') as f:
                f.write(audio)

    except Exception as e:
        print("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        d = {"common": wsParam.CommonArgs,
             "business": wsParam.BusinessArgs,
             "data": wsParam.Data,
             }
        d = json.dumps(d)
        print("------>开始发送文本数据")
        ws.send(d)
        file_mp3 = [f for f in os.listdir('.') if f.endswith('.mp3')]
        for mp3 in file_mp3:
            try:
                os.remove(mp3)
                print(f'已经删去{mp3}')
            except Exception as e:
                print(e)
    thread.start_new_thread(run, ())
def tts_api_get_result(text, tts_file):
    global wsParam, ws
    
    # 添加文件路径检查和修复
    import os
    
    # 如果文件路径是相对路径，确保目录存在
    if not os.path.isabs(tts_file):
        # 确保目录存在
        os.makedirs(os.path.dirname(tts_file) if os.path.dirname(tts_file) else '.', exist_ok=True)
    
    print(f"TTS文件路径: {tts_file}")
    print(f"文本内容: {text}")
    
    try:
        wsParam = Ws_Param(APPID='f8d6553f', 
                          APISecret='NDczOThiNmRlODBhNzUxNTUzNjljY2Jj',
                          APIKey='03e81fa34a2056135af3d9c11a22f528',
                          Text=text)
        
        # 打印调试信息
        print("创建WebSocket URL...")
        wsUrl = wsParam.create_url()
        print(f"WebSocket URL创建成功: {wsUrl[:50]}...")  # 只显示前50个字符
        
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.tts_file = tts_file
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
    except Exception as e:
        print(f"TTS API调用异常: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    tts_api_get_result("你好，这是一个测试语音",tts_file='jsj.mp3')