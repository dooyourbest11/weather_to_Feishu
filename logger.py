import os
import logging
import datetime

def setup_logger(log_dir="./Weather/logs"):
    """
    设置日志器，记录程序运行信息
    
    Args:
        log_dir: 日志文件保存目录
    
    Returns:
        配置好的logger对象
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger('weather_app')
    logger.setLevel(logging.DEBUG)
    
    # 防止日志重复
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器，每天一个日志文件
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'weather_app_{today}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_request(logger, method, url, headers=None, data=None, json_data=None, files=None):
    """
    记录HTTP请求详情
    
    Args:
        logger: 日志器
        method: HTTP方法
        url: 请求URL
        headers: 请求头
        data: 表单数据
        json_data: JSON数据
        files: 文件数据
    """
    logger.debug(f"=== HTTP请求 ===")
    logger.debug(f"方法: {method}")
    logger.debug(f"URL: {url}")
    
    if headers:
        logger.debug(f"请求头: {headers}")
    
    if data:
        logger.debug(f"表单数据: {data}")
    
    if json_data:
        logger.debug(f"JSON数据: {json_data}")
    
    if files:
        file_info = {k: f"{v[0]} (文件类型: {v[1]})" for k, v in files.items()}
        logger.debug(f"文件: {file_info}")

def log_response(logger, response):
    """
    记录HTTP响应详情
    
    Args:
        logger: 日志器
        response: 响应对象
    """
    logger.debug(f"=== HTTP响应 ===")
    logger.debug(f"状态码: {response.status_code}")
    logger.debug(f"响应头: {dict(response.headers)}")
    
    try:
        json_response = response.json()
        logger.debug(f"响应体(JSON): {json_response}")
    except:
        # 如果不是JSON格式，记录文本内容
        content = response.text[:500] + "..." if len(response.text) > 500 else response.text
        logger.debug(f"响应体(文本): {content}") 