# #
# # 人脸比对 WebAPI 接口调用示例
# # 运行前：请先填写Appid、APIKey、APISecret以及图片路径
# # 运行方法：直接运行 main 即可 
# # 结果： 控制台输出结果信息
# # 
# # 接口文档（必看）：https://www.xfyun.cn/doc/face/xffaceComparisonRecg/API.html
# #


from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import os
import traceback
import json
import requests


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


# 进行sha256加密和base64编码
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)

def gen_body(appid, img1_path, img2_path, server_id):
    with open(img1_path, 'rb') as f:
        img1_data = f.read()
    with open(img2_path, 'rb') as f:
        img2_data = f.read()
    body = {
        "header": {
            "app_id": appid,
            "status": 3
        },
        "parameter": {
            server_id: {
                "service_kind": "face_compare",
                "face_compare_result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "input1": {
                "encoding": "jpg",
                "status": 3,
                "image": str(base64.b64encode(img1_data), 'utf-8')
            },
            "input2": {
                "encoding": "jpg",
                "status": 3,
                "image": str(base64.b64encode(img2_data), 'utf-8')
            }
        }
    }
    return json.dumps(body)


def run(img1_path, img2_path):
    server_id = 's67c9c78c'
    appid = '78b581df'
    apisecret = 'OTZjZDc0YmMxODQwNTNmN2UxNWEwZWU4'
    apikey = 'f1beea21dc33fb06e9c355932180598e'
    url = 'http://api.xf-yun.com/v1/private/{}'.format(server_id)
    request_url = assemble_ws_auth_url(url, "POST", apikey, apisecret)
    headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'app_id': appid}
    print(request_url)
    response = requests.post(request_url, data=gen_body(appid, img1_path, img2_path, server_id), headers=headers)
    print(response)
    resp_data = json.loads(response.content.decode('utf-8'))
    print("resp_data-->>",resp_data)
    
    # 解码返回的文本数据
    out = base64.b64decode(resp_data['payload']['face_compare_result']['text']).decode()
    print("解码后的结果:", out)
    
    try:
        out_new = json.loads(out)
        
        # 检查返回码 - 0表示成功，非0表示错误
        if 'ret' in out_new:
            ret_code = out_new['ret']
            
            # 错误码映射
            error_messages = {
                20004: "服务调用失败，请检查图片质量或重新上传",
                20005: "图片中未检测到人脸",
                20006: "图片格式不支持",
                20007: "图片大小超过限制",
                20008: "服务内部错误",
                20009: "无效的参数",
                20010: "服务调用超时"
            }
            
            if ret_code != 0:  # 非0表示错误
                error_msg = error_messages.get(ret_code, f"未知错误，错误码: {ret_code}")
                raise Exception(error_msg)
            else:
                # ret为0表示成功，继续处理score
                if 'score' in out_new:
                    score = out_new['score']
                    print("比对分数:", score)
                    compare_result = ["同一个人", "不是同一个人"]
                    out = {}
                    out['score'] = score
                    if score > 0.67:
                        out["desc"] = compare_result[0]
                    else:
                        out["desc"] = compare_result[1]
                    print("最终结果:", out)
                    return out
                else:
                    raise Exception("API返回数据格式异常，缺少score字段")
        else:
            raise Exception("API返回数据格式异常，缺少ret字段")
            
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        raise Exception("API返回数据格式异常")
    except Exception as e:
        print(f"处理API响应时出错: {e}")
        raise

# if __name__ == '__main__':
#     ou = run(img1_path="1.jpg", img2_path="2.jpg")