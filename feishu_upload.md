<!-- import json
import os
import logging
import time

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

# 这个是飞书上传图片API，已经跑通的python用例：扫描目录下所有jpg文件，上传到飞书服务器，返回image_key
# 这个是main()函数形式的。如需使用，请将main()函数剥离，写成独立的模块函数调用。被注释掉了，需要使用请取消整个文件的注释


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("feishu_uploader")


# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
# 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
# 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
def main():
    start_time = time.time()
    logger.info("====== 开始上传图片到飞书 ======")
    
    # APP凭证信息
    app_id = "cli_a8a5bc999631d00b"
    app_secret = "bM3XAdFtSnnrFVK5FveVYdNJDB2dWniB"
    image_path = "./test_upload/1.jpg"
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        logger.error(f"文件不存在: {image_path}")
        return
    
    # 获取文件信息
    file_size = os.path.getsize(image_path) / 1024  # KB
    logger.info(f"图片路径: {os.path.abspath(image_path)}")
    logger.info(f"图片大小: {file_size:.2f} KB")
    
    # 创建client
    logger.info(f"初始化飞书客户端，AppID: {app_id}")
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    logger.info("读取图片文件...")
    try:
        file = open(image_path, "rb")
        logger.info("构建上传请求...")
        request: CreateImageRequest = CreateImageRequest.builder() \
            .request_body(CreateImageRequestBody.builder()
                .image_type("message")
                .image(file)
                .build()) \
            .build()

        # 发起请求
        logger.info("发送上传请求...")
        response: CreateImageResponse = client.im.v1.image.create(request)

        # 处理失败返回
        if not response.success():
            logger.error(
                f"上传失败! 错误代码: {response.code}, 错误信息: {response.msg}, log_id: {response.get_log_id()}")
            logger.error(f"完整响应: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            
            # 详细诊断234011错误
            if response.code == 234011:
                logger.error("图片格式无法识别，可能原因:")
                logger.error("1. 图片格式不符合要求（只支持JPG/PNG）")
                logger.error("2. 文件扩展名与实际格式不匹配")
                logger.error("3. 图片文件可能已损坏")
                
                # 检查文件扩展名
                _, ext = os.path.splitext(image_path)
                logger.info(f"文件扩展名: {ext}")
            return

        # 处理业务结果
        logger.info("上传成功!")
        image_key = response.data.image_key
        logger.info(f"获取到的image_key: {image_key}")
        logger.info(f"上传耗时: {(time.time() - start_time):.2f} 秒")
        logger.info("可以使用该image_key发送消息到飞书群")
        
    except Exception as e:
        logger.exception(f"上传过程中出错: {str(e)}")
    finally:
        try:
            file.close()
        except:
            pass
        
    logger.info("====== 图片上传过程结束 ======")


if __name__ == "__main__":
    main() -->
