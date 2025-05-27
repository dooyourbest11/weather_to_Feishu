import os
import time
import sys
from weather import start_file_monitoring
from weatherPic import capture_weather_screenshots
from logger import setup_logger

def main():
    """主函数：启动天气截图和文件监控功能"""
    # 设置日志
    logger = setup_logger()
    logger.info("===== 程序启动 =====")
    
    try:
        # 配置参数
        monitored_path = "./Weather"  # 要监控的目录路径
        webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/787effd4-1e14-4d80-bfe5-8ae60e87bc4e"  # 飞书机器人webhook URL
        app_id = "cli_a8a5bc999631d00b"  # 飞书应用ID
        app_secret = "bM3XAdFtSnnrFVK5FveVYdNJDB2dWniB"  # 飞书应用密钥
        
        # 确保目标目录存在
        os.makedirs(monitored_path, exist_ok=True)
        logger.info(f"监控目录: {os.path.abspath(monitored_path)}")
        
        # 1. 先启动文件监控功能
        logger.info("===== 开始启动文件监控功能 =====")
        observer = start_file_monitoring(monitored_path, webhook_url, app_id, app_secret)
        
        # 2. 再执行天气截图功能
        logger.info("\n===== 开始执行天气网站截图 =====")
        try:
            capture_weather_screenshots(output_dir=monitored_path)
        except Exception as e:
            logger.exception(f"截图过程中出现错误: {str(e)}")
        

        
        try:
            # 保持程序运行
            logger.info("监控已启动，按 Ctrl+C 停止监控...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # 当用户按下Ctrl+C时，停止观察者
            observer.stop()
            logger.info("用户终止监控")
        
        # 等待观察者结束
        observer.join()
        
        logger.info("程序已退出")
    except Exception as e:
        logger.exception(f"程序运行过程中出现未处理的异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
