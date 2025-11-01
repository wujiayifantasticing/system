import os
import json
import time
import wave
import threading
import base64
import hashlib
import hmac
import ssl
import websocket
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode, urlparse
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

# 自定义模块
from face_feature import xf_output
from face_compare import run
from speech_synthesis import tts_api_get_result
from speech_information import xf_yun
from speech_recognition import data
from SparkPythondemo import *

# 配置常量
UPLOAD_FOLDER = './file/'  # 文件存放路径
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'wav', 'mp3', 'ogg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 讯飞API配置
XFYUN_APPID = 'f8d6553f'
XFYUN_API_KEY = '03e81fa34a2056135af3d9c11a22f528'
XFYUN_API_SECRET = 'NDczOThiNmRlODBhNzUxNTUzNjljY2Jj'

# 语音年龄性别识别配置
IGR_APPID = '6f6ef97f'
IGR_API_KEY = '5438c60bc0264e55b27752eb38e39f8e'
IGR_API_SECRET = 'YWY4ZDE4MWE3NmE0ZGEzZTcxZjRkNzA3'

# 星火X1配置 - 使用与X1_ws.py相同的配置
SPARK_APPID = "f8d6553f"
SPARK_API_KEY = "03e81fa34a2056135af3d9c11a22f528"
SPARK_API_SECRET = "NDczOThiNmRlODBhNzUxNTUzNjljY2Jj"
SPARK_URL = "wss://spark-api.xf-yun.com/v1/x1"

# 星火聊天配置（用于文本聊天）
SPARK_CHAT_APPID = "1d18d09b"
SPARK_CHAT_API_KEY = "8a9d4a16b90d51a92fe49ba23d5b8e8c"
SPARK_CHAT_API_SECRET = "ODhmZDMxZjc1ZjVmY2I1ZDU5YmFmOTFm"
SPARK_CHAT_URL = "wss://spark-api.xf-yun.com/v1.1/chat"
SPARK_CHAT_DOMAIN = "lite"
SIMULATION_MODE = True
# ==================== 模型选择配置 ====================
MODEL_CONFIGS = {
    "lite": {
        "name": "星火Lite模型",
        "appid": SPARK_CHAT_APPID,
        "api_key": SPARK_CHAT_API_KEY,
        "api_secret": SPARK_CHAT_API_SECRET,
        "url": SPARK_CHAT_URL,
        "domain": SPARK_CHAT_DOMAIN
    },
    "x1": {
        "name": "星火X1模型", 
        "appid": SPARK_APPID,
        "api_key": SPARK_API_KEY,
        "api_secret": SPARK_API_SECRET,
        "url": SPARK_URL,
        "domain": "x1"
    }
}

# 默认模型
DEFAULT_MODEL = "lite"

def get_model_config(model_type="lite"):
    """获取模型配置"""
    return MODEL_CONFIGS.get(model_type, MODEL_CONFIGS[DEFAULT_MODEL])

def call_spark_api(question, model_type="lite"):
    """调用星火API - 支持多模型选择"""
    try:
        model_config = get_model_config(model_type)
        
        # 构建问题格式
        question_list = [{"role": "user", "content": question}]
        
        from SparkPythondemo import SparkApi
        
        SparkApi.answer = ""
        SparkApi.main(
            model_config["appid"],
            model_config["api_key"], 
            model_config["api_secret"],
            model_config["url"],
            model_config["domain"],
            question_list
        )
        
        result = SparkApi.answer.strip() if SparkApi.answer else "抱歉，没有收到回复。"
        print(f"{model_config['name']}回复: {result}")
        return result
        
    except Exception as e:
        print(f"调用{model_config['name']}异常: {e}")
        import traceback
        traceback.print_exc()
        return f"抱歉，{model_config['name']}服务暂时不可用。"

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('./static/file/', exist_ok=True)


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 配置文件路径
app.config['UPLOAD_FEATURE_IMAGE'] = os.path.join(UPLOAD_FOLDER, 'feature.jpg')
app.config['UPLOAD_COMPARE1_IMAGE'] = os.path.join(UPLOAD_FOLDER, 'face1.jpg')
app.config['UPLOAD_COMPARE2_IMAGE'] = os.path.join(UPLOAD_FOLDER, 'face2.jpg')

# 语音聊天相关配置
app.config['AUDIO_STATIC_DIR'] = os.path.join('static', 'audio')
os.makedirs(app.config['AUDIO_STATIC_DIR'], exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否合法"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_file(file_path):
    """安全删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"删除文件时出错 {file_path}: {str(e)}")
    return False

def clear_feature_files():
    """清空人脸特征相关文件"""
    clear_file(app.config['UPLOAD_FEATURE_IMAGE'])

def clear_compare_files():
    """清空人脸比对相关文件"""
    clear_file(app.config['UPLOAD_COMPARE1_IMAGE'])
    clear_file(app.config['UPLOAD_COMPARE2_IMAGE'])

def handle_upload(file, file_type):
    """处理文件上传的通用函数"""
    if not file or file.filename == '':
        return None, '没有收到文件'

    if not allowed_file(file.filename):
        return None, '不支持的文件类型'

    # 根据类型确定保存路径
    if file_type == 'feature':
        filename = 'feature.jpg'
        path = app.config['UPLOAD_FEATURE_IMAGE']
    elif file_type == 'compare1':
        filename = 'face1.jpg'
        path = app.config['UPLOAD_COMPARE1_IMAGE']
    elif file_type == 'compare2':
        filename = 'face2.jpg'
        path = app.config['UPLOAD_COMPARE2_IMAGE']
    else:
        # 对于其他文件类型，使用安全文件名
        filename = secure_filename(file.filename)
        path = os.path.join('./static/file/', filename)

    # 确保目录存在
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 清除旧文件并保存新文件
    clear_file(path)
    file.save(path)

    return path, None

# ==================== 语音年龄性别识别功能 ====================

class IGR_Param:
    """语音年龄性别识别参数类"""
    def __init__(self, appid, api_key, api_secret, audio_file):
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        self.AudioFile = audio_file
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"ent": "igr", "aue": "raw", "rate": 16000}

    def create_url(self):
        """生成语音年龄性别识别WebSocket URL"""
        url = 'wss://ws-api.xfyun.cn/v2/igr'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = f"host: ws-api.xfyun.cn\ndate: {date}\nGET /v2/igr HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        return url + '?' + urlencode(v)

def voice_age_gender_recognition(audio_path):
    """语音年龄性别识别函数"""
    print(f"开始语音年龄性别识别: {audio_path}")
    
    # 首先验证和转换音频格式
    validated_path = validate_and_convert_audio(audio_path)
    
    recognition_result = {"age": "", "gender": "", "age_prob": 0, "gender_prob": 0}
    recognition_done = threading.Event()
    
    if not os.path.exists(validated_path):
        print(f"音频文件不存在: {validated_path}")
        return None
    
    # 检查文件大小
    file_size = os.path.getsize(validated_path)
    print(f"音频文件大小: {file_size} 字节")
    
    if file_size < 100:
        print("音频文件太小，可能为空")
        return None
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            print(f"收到识别结果: {data}")
            
            # 检查是否有错误
            if data.get("code") != 0:
                print(f"语音年龄性别识别错误: {data.get('message')}")
                recognition_done.set()
                return
            
            # 提取年龄和性别数据
            if 'data' in data and 'result' in data['data']:
                age_data = data['data']['result']['age']
                gender_data = data['data']['result']['gender']
                
                # 定义年龄和性别的键
                age_keys = ['child', 'middle', 'old']
                gender_keys = ['female', 'male']
                
                # 找到概率最大的年龄
                max_age_prob = -1
                max_age_key = None
                for key in age_keys:
                    prob = float(age_data[key])
                    if prob > max_age_prob:
                        max_age_prob = prob
                        max_age_key = key
                
                # 找到概率最大的性别
                max_gender_prob = -1
                max_gender_key = None
                for key in gender_keys:
                    prob = float(gender_data[key])
                    if prob > max_gender_prob:
                        max_gender_prob = prob
                        max_gender_key = key
                
                # 映射到中文
                age_mapping = {'child': '儿童(0-12岁)', 'middle': '中年(13-40岁)', 'old': '老年(40岁以上)'}
                gender_mapping = {'female': '女性', 'male': '男性'}
                
                recognition_result["age"] = age_mapping.get(max_age_key, "未知")
                recognition_result["gender"] = gender_mapping.get(max_gender_key, "未知")
                recognition_result["age_prob"] = max_age_prob
                recognition_result["gender_prob"] = max_gender_prob
                
                print(f"识别结果 - 年龄: {recognition_result['age']} (概率: {max_age_prob:.2f})")
                print(f"识别结果 - 性别: {recognition_result['gender']} (概率: {max_gender_prob:.2f})")
            
            if data.get("data", {}).get("status") == 2:
                print("语音年龄性别识别完成")
                recognition_done.set()
                
        except Exception as e:
            print(f"语音年龄性别识别消息处理错误: {e}")
            recognition_done.set()

    def on_error(ws, error):
        print(f"语音年龄性别识别WebSocket错误: {error}")
        recognition_done.set()

    def on_close(ws, *args):
        print("语音年龄性别识别连接关闭")
        recognition_done.set()

    def on_open(ws):
        def run():
            try:
                frameSize = 5000  # 每一帧的音频大小
                status = 0  # 第一帧的标识

                with open(validated_path, "rb") as fp:
                    while True:
                        buf = fp.read(frameSize)
                        # 文件结束
                        if not buf:
                            status = 2  # 最后一帧
                        
                        # 第一帧处理
                        if status == 0:
                            d = {
                                "common": ws.param.CommonArgs,
                                "business": ws.param.BusinessArgs,
                                "data": {
                                    "status": 0,
                                    "format": "audio/L16;rate=16000",
                                    "audio": base64.b64encode(buf).decode('utf-8'),
                                    "encoding": "raw"
                                }
                            }
                            ws.send(json.dumps(d))
                            status = 1  # 中间帧
                        
                        # 中间帧处理
                        elif status == 1:
                            d = {
                                "data": {
                                    "status": 1,
                                    "format": "audio/L16;rate=16000",
                                    "audio": base64.b64encode(buf).decode('utf-8'),
                                    "encoding": "raw"
                                }
                            }
                            ws.send(json.dumps(d))
                        
                        # 最后一帧处理
                        elif status == 2:
                            d = {
                                "data": {
                                    "status": 2,
                                    "format": "audio/L16;rate=16000",
                                    "audio": "",
                                    "encoding": "raw"
                                }
                            }
                            ws.send(json.dumps(d))
                            time.sleep(1)
                            break
                
                print("音频数据发送完成")
                
            except Exception as e:
                print(f"发送音频数据错误: {e}")
                recognition_done.set()

        threading.Thread(target=run, daemon=True).start()

    try:
        ws_param = IGR_Param(IGR_APPID, IGR_API_KEY, IGR_API_SECRET, validated_path)
        ws_url = ws_param.create_url()
        
        print(f"连接语音年龄性别识别WebSocket: {ws_url}")
        
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.param = ws_param
        ws.on_open = on_open
        
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}, daemon=True)
        ws_thread.start()
        
        if recognition_done.wait(timeout=60):
            if recognition_result["age"] and recognition_result["gender"]:
                print(f"语音年龄性别识别最终结果: {recognition_result}")
                return recognition_result
            else:
                print("语音年龄性别识别无结果")
                return None
        else:
            print("语音年龄性别识别超时")
            return None
            
    except Exception as e:
        print(f"语音年龄性别识别异常: {e}")
        return None

# ==================== 其他功能（保持原有代码不变）====================

class AudioToTextParam:
    """语音识别参数类"""
    def __init__(self, appid, api_key, api_secret, audio_file):
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        self.AudioFile = audio_file
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {
            "domain": "iat",
            "language": "zh_cn",
            "accent": "mandarin",
            "vinfo": 1,
            "vad_eos": 10000
        }

    def create_url(self):
        """生成语音识别WebSocket URL"""
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = f"host: ws-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        return url + '?' + urlencode(v)

class TTS_Param:
    """语音合成参数类"""
    def __init__(self, appid, api_key, api_secret, text):
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        self.Text = text
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {
            "aue": "raw", 
            "auf": "audio/L16;rate=16000", 
            "vcn": "x4_yezi", 
            "tte": "utf8"
        }
        self.Data = {
            "status": 2, 
            "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")
        }

    def create_url(self):
        """生成语音合成WebSocket URL"""
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = f"host: tts-api.xfyun.cn\ndate: {date}\nGET /v2/tts HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": "tts-api.xfyun.cn"
        }
        return url + '?' + urlencode(v)

def validate_and_convert_audio(input_path):
    """验证并转换音频格式为讯飞要求的格式"""
    try:
        # 首先检查文件头
        with open(input_path, 'rb') as f:
            header = f.read(4)
            print(f"文件头: {header}")
            
            # 如果不是WAV文件，尝试转换
            if header != b'RIFF':
                print("检测到非WAV格式，尝试转换...")
                return convert_audio_to_wav(input_path)
        
        # 如果是WAV文件，检查参数
        with wave.open(input_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            
            print(f"音频信息: 采样率={rate}Hz, 声道数={channels}, 位深度={sampwidth*8}bit, 帧数={frames}")
            
            # 检查是否符合讯飞要求
            if rate != 16000 or channels != 1 or sampwidth != 2:
                print("音频格式不符合要求，进行转换...")
                return convert_wav_format(input_path)
            
            print("音频格式符合要求，无需转换")
            return input_path
            
    except Exception as e:
        print(f"音频验证失败: {e}")
        # 如果WAV文件损坏，尝试转换
        return convert_audio_to_wav(input_path)

def convert_audio_to_wav(input_path):
    """将任意音频格式转换为WAV格式"""
    try:
        from pydub import AudioSegment
        
        output_path = input_path.replace('.wav', '_converted.wav')
        
        # 根据文件扩展名加载音频
        if input_path.endswith('.webm'):
            audio = AudioSegment.from_file(input_path, format="webm")
        elif input_path.endswith('.mp3'):
            audio = AudioSegment.from_file(input_path, format="mp3")
        elif input_path.endswith('.ogg'):
            audio = AudioSegment.from_file(input_path, format="ogg")
        else:
            # 尝试自动检测格式
            audio = AudioSegment.from_file(input_path)
        
        # 转换为讯飞要求的格式：16kHz, 单声道, 16bit
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(output_path, format="wav")
        
        print(f"音频格式转换完成: {output_path}")
        return output_path
        
    except ImportError:
        print("警告: 未安装pydub，无法进行音频格式转换")
        return input_path
    except Exception as e:
        print(f"音频转换失败: {e}")
        return input_path

def convert_wav_format(input_path):
    """转换WAV文件格式"""
    try:
        with wave.open(input_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            frames_data = wav_file.readframes(frames)
        
        output_path = input_path.replace('.wav', '_converted.wav')
        
        # 创建符合要求的WAV文件
        with wave.open(output_path, 'wb') as out_file:
            out_file.setnchannels(1)
            out_file.setsampwidth(2)  # 16bit
            out_file.setframerate(16000)
            out_file.writeframes(frames_data)
        
        print(f"WAV格式转换完成: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"WAV格式转换失败: {e}")
        return input_path

def audio_to_text(audio_path):
    """语音识别函数"""
    print(f"开始语音识别: {audio_path}")
    
    # 首先验证和转换音频格式
    validated_path = validate_and_convert_audio(audio_path)
    
    recognized_text = [""]
    recognition_done = threading.Event()
    
    if not os.path.exists(validated_path):
        print(f"音频文件不存在: {validated_path}")
        return None
    
    # 检查文件大小
    file_size = os.path.getsize(validated_path)
    print(f"音频文件大小: {file_size} 字节")
    
    if file_size < 100:
        print("音频文件太小，可能为空")
        return None
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            code = data.get("code")
            if code != 0:
                print(f"语音识别错误: {data.get('message')}")
                recognition_done.set()
                return
            
            ws_data = data.get("data", {}).get("result", {}).get("ws", [])
            current_text = ""
            for item in ws_data:
                for cw in item.get("cw", []):
                    if cw.get("w") not in ",。?!":
                        current_text += cw.get("w", "")
            
            if current_text:
                recognized_text[0] += current_text
                print(f"当前识别: {current_text}")
            
            if data.get("data", {}).get("status") == 2:
                print("语音识别完成")
                recognition_done.set()
                
        except Exception as e:
            print(f"语音识别消息处理错误: {e}")
            recognition_done.set()

    def on_error(ws, error):
        print(f"语音识别WebSocket错误: {error}")
        recognition_done.set()

    def on_close(ws, *args):
        print("语音识别连接关闭")
        recognition_done.set()

    def on_open(ws):
        def run():
            try:
                with open(validated_path, "rb") as f:
                    audio_data = f.read()
                
                print(f"发送音频数据: {len(audio_data)} 字节")
                
                # 发送第一帧
                first_frame = {
                    "common": ws.param.CommonArgs,
                    "business": ws.param.BusinessArgs,
                    "data": {
                        "status": 0,
                        "format": "audio/L16;rate=16000",
                        "audio": base64.b64encode(audio_data).decode('utf-8'),
                        "encoding": "raw"
                    }
                }
                ws.send(json.dumps(first_frame))
                
                # 发送结束帧
                end_frame = {
                    "data": {
                        "status": 2,
                        "format": "audio/L16;rate=16000",
                        "audio": "",
                        "encoding": "raw"
                    }
                }
                ws.send(json.dumps(end_frame))
                
                print("音频数据发送完成")
                
            except Exception as e:
                print(f"发送音频数据错误: {e}")
                recognition_done.set()

        threading.Thread(target=run, daemon=True).start()

    try:
        ws_param = AudioToTextParam(XFYUN_APPID, XFYUN_API_KEY, XFYUN_API_SECRET, validated_path)
        ws_url = ws_param.create_url()
        
        print(f"连接语音识别WebSocket: {ws_url}")
        
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.param = ws_param
        ws.on_open = on_open
        
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}, daemon=True)
        ws_thread.start()
        
        if recognition_done.wait(timeout=60):
            result = recognized_text[0] if recognized_text[0] else None
            print(f"语音识别最终结果: {result}")
            return result
        else:
            print("语音识别超时")
            return None
            
    except Exception as e:
        print(f"语音识别异常: {e}")
        return None

def text_to_speech_ws(text):
    """语音合成函数（WebSocket版本）"""
    if not text or len(text.strip()) == 0:
        print("❌ 语音合成错误：文本内容为空")
        return None
    
    # 限制文本长度，避免过长
    if len(text) > 500:
        text = text[:500] + "..."
    
    timestamp = int(time.time() * 1000)
    filename = f"tts_{timestamp}.wav"
    wav_path = os.path.join(app.config['AUDIO_STATIC_DIR'], filename)
    
    print(f"🎯 开始语音合成")
    print(f"   文本: {text}")
    print(f"   目标文件: {wav_path}")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(wav_path), exist_ok=True)
    
    synthesis_done = threading.Event()
    audio_data = []
    synthesis_success = False
    error_message = None
    file_saved = False  # 新增：标记文件是否已保存

    def on_message(ws, message):
        nonlocal synthesis_success, error_message
        try:
            data = json.loads(message)
            code = data.get("code")
            
            print(f"📨 收到TTS消息 - code: {code}")
            
            if code != 0:
                error_message = data.get('message', '未知错误')
                print(f"❌ TTS API错误 [{code}]: {error_message}")
                synthesis_done.set()
                return
                
            # 检查音频数据
            audio_chunk = data.get("data", {}).get("audio", "")
            if audio_chunk:
                try:
                    decoded_audio = base64.b64decode(audio_chunk)
                    audio_data.append(decoded_audio)
                    print(f"   收到音频数据: {len(decoded_audio)} 字节")
                except Exception as e:
                    print(f"❌ 音频数据解码错误: {e}")
                    error_message = str(e)
            else:
                print("⚠️  无音频数据")
            
            # 检查状态
            status = data.get("data", {}).get("status")
            print(f"   状态: {status}")
            
            if status == 2:
                print("✅ 语音合成完成")
                synthesis_success = True
                
        except Exception as e:
            error_message = f"消息处理错误: {e}"
            print(f"❌ {error_message}")
            synthesis_done.set()

    def on_error(ws, error):
        nonlocal error_message
        error_message = f"WebSocket错误: {error}"
        print(f"❌ {error_message}")
        synthesis_done.set()

    def on_close(ws, close_status_code, close_msg):
        nonlocal file_saved
        print(f"🔌 TTS连接关闭: {close_status_code} - {close_msg}")
        
        if audio_data and synthesis_success:
            try:
                total_audio = b''.join(audio_data)
                print(f"💾 保存音频文件，总大小: {len(total_audio)} 字节")
                
                with wave.open(wav_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(total_audio)
                
                # 验证文件
                if os.path.exists(wav_path):
                    file_size = os.path.getsize(wav_path)
                    print(f"✅ 文件保存成功: {wav_path} ({file_size} 字节)")
                    file_saved = True  # 标记文件已保存
                else:
                    print("❌ 文件保存失败")
                    
            except Exception as e:
                error_message = f"文件保存错误: {e}"
                print(f"❌ {error_message}")
        else:
            print(f"❌ 合成失败 - 成功: {synthesis_success}, 数据量: {len(audio_data)}")
            if error_message:
                print(f"   错误信息: {error_message}")
        
        synthesis_done.set()

    def on_open(ws):
        print("🔗 TTS WebSocket连接已建立")
        data_to_send = {
            "common": ws.param.CommonArgs,
            "business": ws.param.BusinessArgs,
            "data": ws.param.Data
        }
        print("📤 发送合成请求...")
        ws.send(json.dumps(data_to_send))

    try:
        # 检查TTS配置
        print(f"🔑 TTS配置检查 - APPID: {XFYUN_APPID}")
        
        ws_param = TTS_Param(XFYUN_APPID, XFYUN_API_KEY, XFYUN_API_SECRET, text)
        ws_url = ws_param.create_url()
        
        print(f"🌐 连接TTS WebSocket...")
        
        ws = websocket.WebSocketApp(ws_url, 
                                  on_message=on_message, 
                                  on_error=on_error, 
                                  on_close=on_close)
        ws.param = ws_param
        ws.on_open = on_open
        
        ws_thread = threading.Thread(target=ws.run_forever, 
                                   kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}, 
                                   daemon=True)
        ws_thread.start()
        
        # 等待合成完成
        wait_success = synthesis_done.wait(timeout=30)
        print(f"⏰ 合成等待结果: {wait_success}")
        
        if wait_success:
            # 关键修改：给文件保存一点时间，然后检查
            time.sleep(0.5)  # 等待500ms确保文件保存完成
            
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:  # 文件至少100字节
                relative_path = f"audio/{filename}"
                print(f"🎉 语音合成完全成功: {relative_path}")
                return relative_path
            else:
                print("❌ 合成失败: 输出文件无效")
                print(f"   文件存在: {os.path.exists(wav_path)}")
                if os.path.exists(wav_path):
                    print(f"   文件大小: {os.path.getsize(wav_path)}")
                if error_message:
                    print(f"   最终错误: {error_message}")
                return None
        else:
            print("❌ 合成超时")
            return None
            
    except Exception as e:
        error_message = f"合成异常: {e}"
        print(f"❌ {error_message}")
        import traceback
        traceback.print_exc()
        return None
            
    except Exception as e:
        error_message = f"合成异常: {e}"
        print(f"❌ {error_message}")
        import traceback
        traceback.print_exc()
        return None
# ==================== 路由定义 ====================

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """上传文件接口"""
    try:
        if 'fileInput' not in request.files:
            return jsonify({'success': False, 'error': '没有文件部分'}), 400

        file = request.files['fileInput']
        file_type = request.form.get('type')

        if not file_type or file_type not in ['feature', 'compare1', 'compare2']:
            return jsonify({'success': False, 'error': '无效的类型参数'}), 400

        path, error = handle_upload(file, file_type)
        if error:
            return jsonify({'success': False, 'error': error}), 400

        return jsonify({'success': True, 'path': path})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/feature', methods=['GET', 'POST'])
def feature():
    """人脸特征分析页面和处理"""
    if request.method == 'GET':
        clear_feature_files()
        return render_template('feature.html')

    response = {'flag': 'false'}

    if not os.path.exists(app.config['UPLOAD_FEATURE_IMAGE']):
        response['msg'] = '请上传图片'
        return jsonify(response)

    try:
        filepath = app.config['UPLOAD_FEATURE_IMAGE']
        result = xf_output(filePath=filepath)
        response['flag'] = 'true'
        response['data'] = result
    except Exception as e:
        response['msg'] = f'分析失败：{str(e)}'
        print(f"人脸特征分析错误: {str(e)}")

    return jsonify(response)

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    """人脸比对页面和处理"""
    if request.method == 'GET':
        clear_compare_files()
        return render_template('compare.html')

    response = {'flag': 'false'}

    if not os.path.exists(app.config['UPLOAD_COMPARE1_IMAGE']):
        response['msg'] = '请上传左边的图片'
    elif not os.path.exists(app.config['UPLOAD_COMPARE2_IMAGE']):
        response['msg'] = '请上传右边的图片'
    else:
        try:
            result = run(
                app.config['UPLOAD_COMPARE1_IMAGE'],
                app.config['UPLOAD_COMPARE2_IMAGE']
            )
            response['flag'] = 'true'
            response['data'] = result
        except Exception as e:
            error_msg = str(e)
            if "服务调用失败" in error_msg or "未检测到人脸" in error_msg:
                response['msg'] = f'{error_msg}，请确保：\n1. 图片包含清晰的人脸\n2. 人脸大小合适\n3. 光线充足\n4. 没有过度遮挡'
            else:
                response['msg'] = f'比对失败：{error_msg}'
            print(f"人脸比对错误: {error_msg}")

    return jsonify(response)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """聊天页面和处理"""
    if request.method == 'GET':
        return render_template('chat.html')
    
    user_message = request.json.get('message', '')
    model_type = request.json.get('model_type', 'lite')  # 获取模型类型
    
    if not user_message:
        return jsonify({"response": "请输入消息"})

    try:
        # 使用新的多模型调用函数
        ai_response = call_spark_api(user_message, model_type)
        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"聊天处理错误: {str(e)}")
        return jsonify({"response": "抱歉，处理您的请求时出现了问题"})

@app.route('/voice_chat')
def voice_chat_page():
    """语音聊天页面"""
    return render_template('voice_chat.html')

def test_audio_file(audio_path):
    """测试音频文件是否有效"""
    try:
        if not os.path.exists(audio_path):
            print(f"错误：文件不存在 {audio_path}")
            return False
            
        file_size = os.path.getsize(audio_path)
        if file_size < 100:
            print(f"错误：文件太小 {file_size} 字节")
            return False
        
        with open(audio_path, 'rb') as f:
            header = f.read(4)
            print(f"文件头: {header}")
            if header != b'RIFF':
                print(f"错误：文件不是有效的WAV格式")
                return False
        
        with wave.open(audio_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            
            duration = frames / float(rate)
            
            print(f"音频测试结果:")
            print(f"  时长: {duration:.2f}秒")
            print(f"  采样率: {rate}Hz")
            print(f"  声道数: {channels}")
            print(f"  位深度: {sampwidth * 8}bit")
            print(f"  总帧数: {frames}")
            
            return duration > 0.5
    except Exception as e:
        print(f"音频测试失败: {e}")
        return False

@app.route('/api/voice_chat', methods=['POST'])
def voice_chat_api():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '没有收到音频文件'}), 400
        
        audio_file = request.files['audio']
        if not audio_file or audio_file.filename == '':
            return jsonify({'success': False, 'error': '无效的音频文件'}), 400
        
        timestamp = int(time.time() * 1000)
        audio_filename = f"voice_chat_{timestamp}.wav"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        audio_file.save(audio_path)
        
        print(f"收到音频文件: {audio_path}")
        
        if not os.path.exists(audio_path):
            print(f"错误：文件保存失败 {audio_path}")
            return jsonify({'success': False, 'error': '文件保存失败'}), 500
            
        file_size = os.path.getsize(audio_path)
        print(f"文件大小: {file_size} 字节")
        
        if file_size == 0:
            print("错误：音频文件为空")
            return jsonify({'success': False, 'error': '音频文件为空'}), 400
        
        if not test_audio_file(audio_path):
            print("音频文件格式无效，尝试转换...")
            converted_path = validate_and_convert_audio(audio_path)
            if converted_path != audio_path and test_audio_file(converted_path):
                print("音频转换成功，使用转换后的文件")
                audio_path = converted_path
            else:
                return jsonify({'success': False, 'error': '音频文件格式无效或太短'}), 400
        
        print("开始语音识别...")
        recognized_text = audio_to_text(audio_path)
        
        if not recognized_text:
            print("语音识别返回空结果")
            return jsonify({'success': False, 'error': '语音识别失败，未识别到有效内容'}), 500
        
        print(f"识别结果: {recognized_text}")
        
        print("调用星火模型生成回复...")
        model_type = request.form.get('model_type', 'lite')  # 获取模型类型
        ai_reply = call_spark_api(recognized_text, model_type)
        if not ai_reply:
            print("AI模型返回空结果")
            return jsonify({'success': False, 'error': 'AI回复生成失败'}), 500
        
        print(f"AI回复: {ai_reply}")
        
        print("🎯 开始语音合成流程...")
        audio_relative_path = text_to_speech_ws(ai_reply)
        
        response_data = {
            'success': True,
            'recognized_text': recognized_text,
            'ai_reply': ai_reply
        }
        
        if audio_relative_path:
            # 给文件保存一点时间
            time.sleep(0.5)
            
            # 验证文件可访问性
            static_dir = os.path.abspath(app.static_folder)
            audio_full_path = os.path.join(static_dir, audio_relative_path)
            
            print(f"📁 文件验证:")
            print(f"   静态目录: {static_dir}")
            print(f"   相对路径: {audio_relative_path}") 
            print(f"   完整路径: {audio_full_path}")
            print(f"   文件存在: {os.path.exists(audio_full_path)}")
            if os.path.exists(audio_full_path):
                file_size = os.path.getsize(audio_full_path)
                print(f"   文件大小: {file_size} 字节")
            
            audio_url = url_for('static', filename=audio_relative_path, _external=True)
            print(f"🌐 生成URL: {audio_url}")
            
            response_data['audio_url'] = audio_url
        else:
            print("❌ 语音合成返回空路径")
            response_data['audio_url'] = None
        
        def cleanup():
            time.sleep(10)
            for temp_file in [audio_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"已清理临时文件: {temp_file}")
            # 清理转换文件
            converted_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if '_converted.wav' in f]
            for cf in converted_files:
                cf_path = os.path.join(app.config['UPLOAD_FOLDER'], cf)
                if os.path.exists(cf_path):
                    os.remove(cf_path)
                    print(f"已清理转换文件: {cf_path}")
        
        threading.Thread(target=cleanup, daemon=True).start()
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"语音聊天处理异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """切换模型接口"""
    try:
        model_type = request.json.get('model_type', 'lite')
        
        if model_type not in MODEL_CONFIGS:
            return jsonify({'success': False, 'error': '不支持的模型类型'})
        
        model_config = get_model_config(model_type)
        return jsonify({
            'success': True,
            'model_type': model_type,
            'model_name': model_config['name'],
            'message': f'已切换到{model_config["name"]}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/speech_information', methods=['GET', 'POST'])
def age_gender_recognition():
    """语音信息识别页面和处理"""
    if request.method == 'GET':
        return render_template('speech_information.html', age_result={}, gender_result={})

    if 'file' not in request.files:
        return jsonify({
            'success': False, 
            'error': "请选择文件"
        })

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({
            'success': False, 
            'error': "请选择有效文件"
        })

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join('./static/file/', filename)
        file.save(file_path)

        # 调用语音信息识别函数
        age, gender = xf_yun(file_path)
        age_labels = ['12~40岁', '0~12岁', '40以上']
        gender_labels = ['女', '男']

        age_result = age_labels[age] if age < len(age_labels) else "未知"
        gender_result = gender_labels[gender] if gender < len(gender_labels) else "未知"

        # 返回JSON格式的响应
        return jsonify({
            'success': True,
            'age_result': age_result,
            'gender_result': gender_result
        })

    except Exception as e:
        print(f"语音信息识别错误: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f"语音信息识别失败: {str(e)}"
        })

@app.route('/speech_synthesis', methods=['GET', 'POST'])
def speech_synthesis():
    """语音合成页面和处理"""
    if request.method == 'GET':
        return render_template('speech_synthesis.html')
    
    # 处理POST请求 - 语音合成
    text = request.form.get('TEXT', '')
    if not text:
        return render_template('speech_synthesis.html', error="请输入要合成的文本")
    
    try:
        # 生成安全的文件名
        timestamp = int(time.time() * 1000)
        filename = f"tts_{timestamp}.mp3"
        output_path = os.path.join('./static/file/', filename)
        
        # 调用语音合成函数
        tts_api_get_result(text, output_path)
        
        # 检查文件是否生成成功
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            # 返回相对路径（去掉./static/前缀）
            result_path = output_path.replace('./static/', '')
            return render_template('speech_synthesis.html', 
                                 text=text, 
                                 result=result_path)
        else:
            return render_template('speech_synthesis.html', 
                                 text=text, 
                                 error="语音合成失败，请重试")
            
    except Exception as e:
        print(f"语音合成错误: {str(e)}")
        return render_template('speech_synthesis.html', 
                             text=text, 
                             error=f"语音合成失败: {str(e)}")

@app.route('/speech_recognition', methods=['GET', 'POST'])
def speech_to_text():
    """语音识别页面和处理"""
    if request.method == 'GET':
        return render_template('speech_recognition.html', result={})

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': "请选择文件"})

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': "请选择有效文件"})

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join('./static/file/', filename)
        file.save(file_path)
        
        # 验证文件
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': "文件保存失败"})
            
        file_size = os.path.getsize(file_path)
        if file_size < 100:
            return jsonify({'success': False, 'error': "音频文件太小或损坏"})

        print(f"开始语音识别，文件: {file_path}, 大小: {file_size}字节")
        
        # 使用真实的语音识别
        result = audio_to_text(file_path)
        
        if not result:
            # 如果真实识别失败，尝试使用备用的 data 函数
            print("音频识别失败，尝试备用识别方法...")
            result = data(filename=file_path)
            
        if not result:
            return jsonify({'success': False, 'error': "语音识别无结果，请检查音频文件格式和内容"})
        
        print(f"识别结果: {result}")
        
        return jsonify({
            'success': True, 
            'result': result
        })

    except Exception as e:
        print(f"语音识别错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({'success': False, 'error': f"处理失败: {str(e)}"})

def call_x1_api(question, timeout=15):
    """使用星火Lite模型替代X1模型"""
    try:
        # 构建问题格式
        question_list = [{"role": "user", "content": question}]
        
        # 使用星火Lite模型（这个APPID有权限）
        from SparkPythondemo import SparkApi
        
        SparkApi.answer = ""
        SparkApi.main(
            SPARK_CHAT_APPID,  # 使用聊天模型的APPID: 1d18d09b
            SPARK_CHAT_API_KEY,
            SPARK_CHAT_API_SECRET,
            SPARK_CHAT_URL, 
            SPARK_CHAT_DOMAIN,
            question_list
        )
        
        result = SparkApi.answer.strip() if SparkApi.answer else "抱歉，没有收到回复。"
        print(f"星火Lite模型回复: {result}")
        return result
        
    except Exception as e:
        print(f"调用星火模型异常: {e}")
        import traceback
        traceback.print_exc()
        return "抱歉，AI服务暂时不可用。"

# 错误处理
@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': '文件太大'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500
@app.route('/test_model_permission')
def test_model_permission():
    """测试模型权限"""
    test_cases = [
        {
            'name': '星火Lite模型',
            'appid': SPARK_CHAT_APPID,
            'api_key': SPARK_CHAT_API_KEY,
            'api_secret': SPARK_CHAT_API_SECRET,
            'url': SPARK_CHAT_URL,
            'domain': SPARK_CHAT_DOMAIN
        },
        {
            'name': '星火X1模型',
            'appid': SPARK_APPID,
            'api_key': SPARK_API_KEY,
            'api_secret': SPARK_API_SECRET,
            'url': SPARK_URL,
            'domain': 'general'  # X1通常使用general域
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"测试 {test_case['name']}...")
            
            # 构建测试问题
            question_list = [{"role": "user", "content": "你好，请回复'测试成功'"}]
            
            from SparkPythondemo import SparkApi
            SparkApi.answer = ""
            
            # 尝试调用
            SparkApi.main(
                test_case['appid'],
                test_case['api_key'],
                test_case['api_secret'],
                test_case['url'],
                test_case['domain'],
                question_list
            )
            
            if SparkApi.answer and "测试成功" in SparkApi.answer:
                results.append({
                    'model': test_case['name'],
                    'status': '✅ 有权限',
                    'response': SparkApi.answer
                })
            else:
                results.append({
                    'model': test_case['name'],
                    'status': '⚠️ 响应异常',
                    'response': SparkApi.answer
                })
                
        except Exception as e:
            results.append({
                'model': test_case['name'],
                'status': '❌ 无权限或配置错误',
                'error': str(e)
            })
    
    # 生成测试报告
    html_report = "<h1>模型权限测试报告</h1>"
    for result in results:
        html_report += f"""
        <div style="margin: 20px; padding: 15px; border: 1px solid #ccc; border-radius: 5px;">
            <h3>{result['model']}</h3>
            <p><strong>状态:</strong> {result['status']}</p>
            {f"<p><strong>回复:</strong> {result.get('response', '')}</p>" if 'response' in result else ''}
            {f"<p><strong>错误:</strong> {result.get('error', '')}</p>" if 'error' in result else ''}
        </div>
        """
    
    return html_report
@app.route('/model_test')
def model_test():
    """模型测试页面"""
    return render_template('model_test.html')

@app.route('/api/test_model', methods=['POST'])
def test_model_api():
    """测试模型API"""
    try:
        model_type = request.json.get('model_type', 'lite')
        test_message = request.json.get('message', '你好，请简单介绍一下你自己')
        
        model_config = get_model_config(model_type)
        
        # 测试调用
        start_time = time.time()
        response = call_spark_api(test_message, model_type)
        end_time = time.time()
        
        response_time = round((end_time - start_time) * 1000, 2)  # 毫秒
        
        return jsonify({
            'success': True,
            'model_type': model_type,
            'model_name': model_config['name'],
            'response': response,
            'response_time': response_time,
            'test_message': test_message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # 生产环境设置
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    # 生产环境设置
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='127.0.0.1', port=5000, debug=True)