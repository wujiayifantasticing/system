import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import threading  # 新增
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket

# 全局变量
answer = ""
isFirstcontent = False
completion_event = threading.Event()

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        return self.Spark_url + '?' + urlencode(v)

def on_error(ws, error):
    print("### error:", error)
    completion_event.set()

def on_close(ws, one, two):
    print("连接关闭")
    completion_event.set()

def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)

def on_message(ws, message):
    global answer, completion_event
    try:
        data = json.loads(message)
        code = data['header']['code']
        
        if code != 0:
            print(f'请求错误: {code}, {data}')
            completion_event.set()
            ws.close()
            return
            
        choices = data["payload"]["choices"]
        status = choices["status"]
        text = choices['text'][0]
        
        if 'reasoning_content' in text and text['reasoning_content']:
            reasoning_content = text["reasoning_content"]
            global isFirstcontent
            isFirstcontent = True

        if 'content' in text and text['content']:
            content = text["content"]
            if isFirstcontent:
                print(content, end="")
            isFirstcontent = False
            answer += content
            
        if status == 2:
            completion_event.set()
            ws.close()
            
    except Exception as e:
        print(f"消息处理错误: {e}")
        completion_event.set()

def gen_params(appid, domain, question):
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234",
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 1.2,
                "max_tokens": 32768
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data

def main(appid, api_key, api_secret, Spark_url, domain, question):
    global answer, completion_event
    answer = ""  # 重置答案
    completion_event.clear()  # 重置完成事件
    
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = appid
    ws.question = question
    ws.domain = domain
    
    # 在新线程中运行WebSocket
    ws_thread = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
    ws_thread.daemon = True
    ws_thread.start()
    
    # 等待回复完成
    completion_event.wait(timeout=30)
    return answer
text = []


def getText(role, content):
    jsoncon = {"role": role, "content": content}
    text.append(jsoncon)
    return text

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text

if __name__ == '__main__':
    # 测试代码
    appid = "74ce783f"
    api_secret = "Yzg1NmQwOTBiNjA0YjBmZjQ4MmYwYzRh"
    api_key = "92f5432492acbb48b84017ada23c0a56"
    domain = "x1"
    Spark_url = "wss://spark-api.xf-yun.com/v1/x1"

    while True:
        Input = input("\n" + "我:")
        question = checklen(getText("user", Input))
        print("星火:", end="")
        result = main(appid, api_key, api_secret, Spark_url, domain, question)
        getText("assistant", result)
        print(result)  # 显示完整回复