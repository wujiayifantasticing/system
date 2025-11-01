# coding: utf-8
import SparkApi
import time

# 移除硬编码的配置，改为从参数传入
# appid = "f8d6553f"     
# api_secret = "NDczOThiNmRlODBhNzUxNTUzNjljY2Jj"   
# api_key ="03e81fa34a2056135af3d9c11a22f528"    
# domain = "lite"         
# Spark_url = "wss://spark-api.xf-yun.com/v1.1/chat"

Spark_url_agent = 'ws(s)://spark-openapi.cn-huabei-1.xf-yun.com/v1/assistants/jwxdfblms1d2_v1' #智能体

# 模型配置字典（可选，可以作为默认配置）
MODEL_CONFIGS = {
    "lite": {
        "appid": "f8d6553f",
        "api_key": "03e81fa34a2056135af3d9c11a22f528",
        "api_secret": "NDczOThiNmRlODBhNzUxNTUzNjljY2Jj",
        "url": "wss://spark-api.xf-yun.com/v1.1/chat",
        "domain": "lite"
    },
    "x1": {
        "appid": "f8d6553f",
        "api_key": "03e81fa34a2056135af3d9c11a22f528", 
        "api_secret": "NDczOThiNmRlODBhNzUxNTUzNjljY2Jj",
        "url": "wss://spark-api.xf-yun.com/v1/x1",
        "domain": "x1"
    }
}

# 初始上下文内容
text = []

def getText(role, content):
    """添加对话内容到上下文"""
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

def getlength(text):
    """计算上下文总长度"""
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    """检查并限制上下文长度"""
    while (getlength(text) > 8000):
        del text[0]
    return text

def chat_with_model(question, model_type="lite", use_history=True):
    """
    使用指定模型进行聊天
    
    参数:
    question: 用户输入的问题
    model_type: 模型类型，'lite' 或 'x1'
    use_history: 是否使用对话历史
    
    返回:
    AI回复内容
    """
    try:
        # 获取模型配置
        if model_type in MODEL_CONFIGS:
            config = MODEL_CONFIGS[model_type]
        else:
            # 默认使用lite模型
            config = MODEL_CONFIGS["lite"]
            print(f"警告：未知模型类型 {model_type}，使用默认的Lite模型")
        
        # 构建问题
        if use_history:
            question_list = checklen(getText("user", question))
        else:
            # 不使用历史，只发送当前问题
            question_list = [{"role": "user", "content": question}]
        
        SparkApi.answer = ""
        print(f"使用{model_type}模型处理问题...")
        
        # 调用SparkApi
        SparkApi.main(
            config["appid"],
            config["api_key"], 
            config["api_secret"],
            config["url"],
            config["domain"],
            question_list
        )
        
        result = SparkApi.answer.strip() if SparkApi.answer else "抱歉，没有收到回复。"
        
        # 如果使用历史，将回复添加到上下文
        if use_history:
            getText("assistant", result)
        
        return result
        
    except Exception as e:
        error_msg = f"调用{model_type}模型时出现错误: {str(e)}"
        print(error_msg)
        return error_msg

def clear_history():
    """清空对话历史"""
    global text
    text = []
    print("对话历史已清空")

def get_history():
    """获取当前对话历史"""
    return text.copy()

def get_model_info(model_type="lite"):
    """获取模型信息"""
    if model_type in MODEL_CONFIGS:
        config = MODEL_CONFIGS[model_type]
        return {
            "model_type": model_type,
            "appid": config["appid"],
            "url": config["url"],
            "domain": config["domain"]
        }
    else:
        return None

# 兼容旧版本的chat函数
def chat():
    """旧版本聊天函数（兼容性保留）"""
    while True:
        try:
            Input = input("\n" + "我:")
            if Input.lower() in ['退出', 'exit', 'quit']:
                break
                
            question = checklen(getText("user", Input))
            SparkApi.answer = ""
            
            # 默认使用lite模型
            SparkApi.main(
                MODEL_CONFIGS["lite"]["appid"],
                MODEL_CONFIGS["lite"]["api_key"],
                MODEL_CONFIGS["lite"]["api_secret"], 
                MODEL_CONFIGS["lite"]["url"],
                MODEL_CONFIGS["lite"]["domain"],
                question
            )
            
            getText("assistant", SparkApi.answer)
            print("AI:", SparkApi.answer)
            
        except KeyboardInterrupt:
            print("\n对话结束")
            break
        except Exception as e:
            print(f"发生错误: {e}")

# 测试函数
def test_models():
    """测试所有模型"""
    test_question = "你好，请简单介绍一下你自己"
    
    print("开始测试所有模型...")
    for model_type in MODEL_CONFIGS.keys():
        print(f"\n=== 测试 {model_type} 模型 ===")
        start_time = time.time()
        
        # 不使用历史进行测试
        response = chat_with_model(test_question, model_type, use_history=False)
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        print(f"回复: {response}")
        print(f"响应时间: {response_time}ms")
        print(f"回复长度: {len(response)} 字符")

if __name__ == '__main__':
    # 可以选择运行测试或交互式聊天
    print("选择运行模式:")
    print("1. 测试所有模型")
    print("2. 交互式聊天")
    print("3. 使用X1模型交互")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_models()
    elif choice == "2":
        chat()
    elif choice == "3":
        # 使用X1模型进行交互
        print("使用X1模型进行对话（输入'退出'结束）:")
        while True:
            try:
                Input = input("\n" + "我:")
                if Input.lower() in ['退出', 'exit', 'quit']:
                    break
                    
                response = chat_with_model(Input, "x1", use_history=True)
                print("AI:", response)
                
            except KeyboardInterrupt:
                print("\n对话结束")
                break
            except Exception as e:
                print(f"发生错误: {e}")
    else:
        print("无效选择，运行默认交互模式")
        chat()