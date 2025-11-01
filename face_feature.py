# -*- coding: utf-8 -*-
import json
from tkinter import Image

import requests
import time
import hashlib
import base64
import os
""" 
  人脸特征分析年龄WebAPI接口调用示例接口文档(必看)：https://doc.xfyun.cn/rest_api/%E4%BA%BA%E8%84%B8%E7%89%B9%E5%BE%81%E5%88%86%E6%9E%90-%E5%B9%B4%E9%BE%84.html
  图片属性：png、jpg、jpeg、bmp、tif图片大小不超过800k
  (Very Important)创建完webapi应用添加服务之后一定要设置ip白名单，找到控制台--我的应用--设置ip白名单，如何设置参考：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=41891
  错误码链接：https://www.xfyun.cn/document/error-code (code返回错误码时必看)
  @author iflytek
"""

# 人脸特征分析年龄webapi接口地址
URL = "http://tupapi.xfyun.cn/v1/"
# 应用ID  (必须为webapi类型应用，并人脸特征分析服务，参考帖子如何创建一个webapi应用：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=36481)
APPID = 'f8d6553f'
# 接口密钥(webapi类型应用开通人脸特征分析服务后，控制台--我的应用---人脸特征分析---服务的apikey)
API_KEY = '03e81fa34a2056135af3d9c11a22f528'
ImageName = "img.jpg"
ImageUrl = "http://hbimg.b0.upaiyun.com/a09289289df694cd6157f997ffa017cc44d4ca9e288fb-OehMYA_fw658"
# 图片数据可以通过两种方式上传，第一种在请求头设置image_url参数，第二种将图片二进制数据写入请求体中。若同时设置，以第一种为准。
# 此demo使用第一种方式进行上传图片地址，如果想使用第二种方式，将图片二进制数据写入请求体即可。

def getHeader(image_name, image_url=None):
    curTime = str(int(time.time()))
    param = "{\"image_name\":\"" + image_name + "\",\"image_url\":\"" + image_url + "\"}"
    paramBase64 = base64.b64encode(param.encode('utf-8'))
    tmp = str(paramBase64, 'utf-8')

    m2 = hashlib.md5()
    m2.update((API_KEY + curTime + tmp).encode('utf-8'))
    checkSum = m2.hexdigest()

    header = {
        'X-CurTime': curTime,
        'X-Param': paramBase64,
        'X-Appid': APPID,
        'X-CheckSum': checkSum,
    }
    return header

def getBody(filePath):
    binfile = open(filePath, 'rb')
    data = binfile.read()
    return data

def xf_transport(url,filePath):
    image_name = os.path.basename(filePath)
    if filePath == " ":
        r = requests.post(url,headers=getHeader(ImageName, ImageUrl))
        str = json.loads(r.text)
        label = str['data']['fileList'][0]['label']  #这里是int型
        #print(type(label))
        return label
    else:
        r = requests.post(url, data=getBody(filePath=filePath),headers=getHeader(image_name=image_name, image_url=""))
        str = json.loads(r.text)
        label = str['data']['fileList'][0]['label'] #这里是int型
        #print(type(label))
        return label

#用于不同接口
def xf_tuputech(filePath):
    list = ['age','sex','expression','face_score']
    out = []
    for name in list:
        url = URL + name
        out.append(xf_transport(url, filePath))
    return out

#匹配不同信息
def xf_output(filePath):
    age_list = ['0-1', '2-5', '6-10', '11-15', '16-20', '21-25', '31-40', '41-50', '51-60', '61-80', '80以上', '其他',
                '26-30']

    sex_list = ['男人','女人','难以辨认','多人']
    expression_list = ['其他','其他表情','喜悦','愤怒','悲伤','惊恐','厌恶','中性']
    face_score_list = ['漂亮','好看','普通','难看','其他','半人脸','多人']
    out_labels = [age_list,sex_list,expression_list,face_score_list]

    in_labels = xf_tuputech(filePath)

    information=[]
    for index,label in enumerate(in_labels):
        out = out_labels[index][label]
        information.append(out)
    desc = ['年龄','性别','表情','颜值']
    out_put = dict(zip(desc,information))
    # josn = json.dumps(out_put)
    return out_put
#
# if __name__ == '__main__':
#     ou=xf_output("2.jpg")
#     print(ou)


# #从视频中获取
# import cv2
# cap = cv2.VideoCapture(0)
# cap_image = []
# while True:
#     ret, frame = cap.read()
#     cv2.imshow('frame',frame)
#     if cv2.waitKey(4000) & 0xFF == ord('q'):
#         break
#     cap_image.append(frame)
# cap.release()
# cv2.destroyAllWindows()
# for idx,image in enumerate(cap_image):
#     cv2.imwrite(f"captured_image_{idx + 1}.jpg", image)
#     xf_output(f"captured_image_{idx + 1}.jpg")


#
# import cv2
# # 读取图片
# image = cv2.imread("zhang.jpg")
#
#
#
# # 获取原始图像的尺寸
# height, width = image.shape[:2]
# print(f"原始图像尺寸: {width}x{height}")
#
#
#
# # 设置新的尺寸，例如将宽度和高度缩小到原来的一半
# new_width = width // 2
# new_height = height // 2
#
#
# # 调整图像大小
# resized_image = cv2.resize(image, (new_width, new_height))
#
# # 保存调整后的图像
# cv2.imwrite("z.jpg", resized_image)


# # 显示调整后的图像
# cv2.imshow("Resized Image", resized_image)
# cv2.waitKey(0)  # 等待按键
# cv2.destroyAllWindows()

