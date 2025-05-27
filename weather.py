import os
import time
import json
import hashlib
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logger import setup_logger, log_request, log_response
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

class ImageHandler(FileSystemEventHandler):
    def __init__(self, webhook_url, monitored_path, app_id, app_secret):
        self.webhook_url = webhook_url
        self.monitored_path = monitored_path
        self.app_id = app_id
        self.app_secret = app_secret
        self.processed_files = {}  # 用于存储已处理过的文件信息，实现去重
        self.token_info = {
            "token": None,
            "expires_at": 0  # 过期时间戳
        }
        # 设置日志器
        self.logger = setup_logger()
        self.logger.info("ImageHandler 初始化完成")
        
        # 初始化飞书SDK客户端
        self.lark_client = lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        self.logger.info("飞书SDK客户端初始化完成")
    
    def on_created(self, event):
        # 仅处理新增的jpg文件
        if not event.is_directory and event.src_path.lower().endswith('.jpg'):
            self.logger.info(f"检测到新创建的jpg文件: {event.src_path}")
            self.process_image(event.src_path)
    
    def on_modified(self, event):
        # 也可以监听文件修改事件，看实际需要决定是否启用
        if not event.is_directory and event.src_path.lower().endswith('.jpg'):
            self.logger.info(f"检测到jpg文件修改: {event.src_path}")
            self.process_image(event.src_path)
    
    def process_image(self, file_path):
        # 获取文件信息
        file_name = os.path.basename(file_path)
        current_time = time.time()
        
        self.logger.info(f"开始处理图片: {file_name}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return
            
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            self.logger.warning(f"文件大小为0字节，跳过处理: {file_path}")
            return
            
        self.logger.info(f"文件大小: {file_size} 字节")
        
        # 计算文件哈希，用于去重
        file_hash = self._calculate_file_hash(file_path)
        file_key = f"{file_name}_{file_hash}"
        
        # 检查是否已处理过（去重逻辑）
        if file_key in self.processed_files:
            last_process_time = self.processed_files[file_key]
            # 如果同一个文件在60秒内已经处理过，则跳过
            if current_time - last_process_time < 60:
                self.logger.info(f"跳过已处理过的文件: {file_name}")
                return
        
        # 上传图片到飞书云存储
        image_key = self.upload_image_to_feishu(file_path)
        if image_key:
            # 发送消息到飞书群
            self.send_message_to_feishu(file_name, image_key)
            # 记录已处理的文件
            self.processed_files[file_key] = current_time
            self.logger.info(f"文件 {file_name} 处理完成")
        else:
            self.logger.error(f"文件 {file_name} 处理失败，未能获取image_key")
    
    def _calculate_file_hash(self, file_path):
        """计算文件的MD5哈希值，用于去重"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_tenant_access_token(self):
        """获取tenant_access_token"""
        current_time = time.time()
        
        # 检查token是否存在且有效
        if self.token_info["token"] and current_time < self.token_info["expires_at"]:
            remaining_time = int(self.token_info["expires_at"] - current_time)
            self.logger.info(f"使用缓存的token，有效性：有效，剩余有效期：{remaining_time}秒")
            return self.token_info["token"]
            
        try:
            # 调用飞书API获取tenant_access_token
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            self.logger.info("开始获取tenant_access_token")
            log_request(self.logger, "POST", url, headers, json_data=data)
            
            response = requests.post(url, headers=headers, json=data)
            log_response(self.logger, response)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    token = result.get("tenant_access_token")
                    # 设置token的有效期为2小时（减去5分钟作为安全裕度）
                    expires_in = result.get("expire") - 300  # 默认为7200秒(2小时)
                    
                    self.token_info = {
                        "token": token,
                        "expires_at": current_time + expires_in
                    }
                    
                    # 打印token是否有效
                    self.logger.info("成功获取tenant_access_token")
                    self.logger.info(f"Token有效性：有效")
                    self.logger.info(f"Token有效期：{expires_in}秒 (约{expires_in/60:.1f}分钟)")
                    self.logger.info(f"Token过期时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.token_info['expires_at']))}")
                    
                    # 打印token的一部分（安全考虑只显示前10个字符）
                    if token:
                        token_preview = token[:10] + "..." if len(token) > 10 else token
                        self.logger.info(f"Token预览：{token_preview}")
                    
                    return token
                else:
                    self.logger.error(f"获取token失败: {result.get('msg')}")
                    self.logger.info("Token有效性：无效")
            else:
                self.logger.error(f"获取token请求失败，状态码: {response.status_code}")
                self.logger.info("Token有效性：无效")
                
            return None
        except Exception as e:
            self.logger.exception(f"获取token时出错: {str(e)}")
            self.logger.info("Token有效性：无效")
            return None
    
    def upload_image_to_feishu(self, image_path):
        """
        使用飞书SDK上传图片到飞书云存储
        参考官方示例: feishu_upPic.py
        """
        try:
            self.logger.info(f"开始上传图片: {os.path.basename(image_path)}")
            
            # 检查文件后缀
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.png']:
                self.logger.error(f"文件格式可能不受支持: {file_ext}，飞书只支持JPG和PNG格式")
                
            # 检查文件大小
            file_size = os.path.getsize(image_path)
            if file_size > 5 * 1024 * 1024:  # 5MB
                self.logger.warning(f"文件大小({file_size/1024/1024:.2f}MB)超过5MB，可能会上传失败")
            
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_content = f.read()
            
            # 检查是否成功读取文件内容
            if not image_content or len(image_content) == 0:
                self.logger.error("读取图片内容失败，文件可能为空或损坏")
                return None
                
            self.logger.info(f"已读取图片数据，大小: {len(image_content)} 字节")
            
            # 尝试使用请求库直接上传（不使用SDK，因为可能有兼容性问题）
            try:
                # 获取tenant_access_token
                token = self.get_tenant_access_token()
                if not token:
                    self.logger.error("未能获取有效的token，无法上传图片")
                    return None
                    
                # 飞书图片上传API
                upload_url = "https://open.feishu.cn/open-apis/im/v1/images"
                
                # 设置请求头，包含认证信息
                headers = {
                    'Authorization': f'Bearer {token}'
                }
                
                # 准备文件数据
                files = {
                    'image': (os.path.basename(image_path), image_content, 'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else 'image/png'),
                    'image_type': (None, 'message')  # 注意这里用image_type而不是type
                }
                
                self.logger.info("使用requests库直接上传图片")
                response = requests.post(url=upload_url, headers=headers, files=files)
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        image_key = result.get('data', {}).get('image_key')
                        self.logger.info(f"图片直接上传成功，image_key: {image_key}")
                        return image_key
                    else:
                        self.logger.error(f"图片直接上传失败，错误代码: {result.get('code')}, 错误信息: {result.get('msg')}")
                else:
                    self.logger.error(f"图片直接上传请求失败，状态码: {response.status_code}")
                    self.logger.debug(f"响应内容: {response.text}")
                
                self.logger.warning("直接上传失败，尝试使用SDK上传...")
            except Exception as direct_upload_error:
                self.logger.exception(f"直接上传时出错: {str(direct_upload_error)}")
                self.logger.warning("尝试使用SDK上传...")
            
            # 使用SDK上传（备选方案）
            # 构造请求对象
            # request = CreateImageRequest.builder() \
            #     .request_body(CreateImageRequestBody.builder()
            #         .image_type("message")
            #         .image(image_content)
            #         .build()) \
            #     .build()
            
            # # 发起请求
            # self.logger.info("调用飞书SDK上传图片")
            # response = self.lark_client.im.v1.image.create(request)
            
            # # 处理失败返回
            # if not response.success():
            #     self.logger.error(
            #         f"SDK上传图片失败, 代码: {response.code}, 消息: {response.msg}, log_id: {response.get_log_id()}")
            #     self.logger.debug(f"完整响应: {json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
                
            #     # 如果错误码是234011（不能识别图片格式）
            #     if response.code == 234011:
            #         self.logger.error("飞书不能识别图片格式，请确保：")
            #         self.logger.error("1. 图片格式为JPG或PNG")
            #         self.logger.error("2. 图片文件没有损坏")
            #         self.logger.error("3. 图片大小在5MB以内")
            #         self.logger.error("4. 文件扩展名与实际格式一致")
                
            #     return None
            
            # # 处理业务结果
            # self.logger.info("图片上传成功")
            # image_key = response.data.image_key
            # self.logger.info(f"image_key: {image_key}")
            # return image_key
            
        except Exception as e:
            self.logger.exception(f"上传图片时出错: {str(e)}")
            return None
    
    def send_message_to_feishu(self, file_name, image_key):
        """发送消息到飞书群"""
        try:
            # 构建请求体，根据飞书API文档格式调整
            message = {
                "msg_type": "image",
                "content": {
                    "image_key": image_key
                }
            }
            
            # 可以添加文本说明
            text_message = {
                "msg_type": "text",
                "content": {
                    "text": f"天气: {file_name}"
                }
            }
            
            # 发送请求
            headers = {
                'Content-Type': 'application/json'
            }
            
            self.logger.info(f"开始发送文本消息: {file_name}")
            log_request(self.logger, "POST", self.webhook_url, headers, json_data=text_message)
            
            # 先发送文本消息
            text_response = requests.post(
                self.webhook_url, 
                headers=headers, 
                data=json.dumps(text_message)
            )
            log_response(self.logger, text_response)
            
            self.logger.info(f"开始发送图片消息: {image_key}")
            log_request(self.logger, "POST", self.webhook_url, headers, json_data=message)
            
            # 再发送图片消息
            image_response = requests.post(
                self.webhook_url, 
                headers=headers, 
                data=json.dumps(message)
            )
            log_response(self.logger, image_response)
            
            # 检查响应
            if text_response.status_code == 200 and image_response.status_code == 200:
                self.logger.info(f"消息发送成功，文件: {file_name}")
                return True
            else:
                self.logger.error(f"消息发送失败，状态码: {text_response.status_code}, {image_response.status_code}")
                return False
            
        except Exception as e:
            self.logger.exception(f"发送消息时出错: {str(e)}")
            return False


def start_file_monitoring(monitored_path, webhook_url, app_id, app_secret):
    """启动文件监控"""
    # 创建事件处理器
    event_handler = ImageHandler(webhook_url, monitored_path, app_id, app_secret)
    
    # 创建观察者
    observer = Observer()
    observer.schedule(event_handler, monitored_path, recursive=True)
    
    # 启动观察者
    observer.start()
    event_handler.logger.info(f"开始监控目录: {monitored_path}")
    
    return observer
