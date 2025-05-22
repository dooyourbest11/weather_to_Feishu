#coding=utf-8
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import schedule
import time
import requests
import os
# 新增在文件头部
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/787effd4-1e14-4d80-bfe5-8ae60e87bc4e"  # 需替换真实webhook地址
# 删除以下配置和函数：
# FEISHU_APP_ID = "cli_a8a5bc999631d00b"
# FEISHU_APP_SECRET = "bM3XAdFtSnnrFVK5FveVYdNJDB2dWniB"
# def get_feishu_token():
# def upload_image_to_feishu():

def send_to_feishu(image_path):
    """直接通过webhook发送base64图片"""
    try:
        with open(image_path, "rb") as f:
            # 将图片转为base64编码
            base64_image = base64.b64encode(f.read()).decode()
            
            # 构造飞书要求的消息格式
            payload = {
                "msg_type": "image",
                "content": {
                    "image_key": f"base64://{base64_image}"  # 使用base64特殊格式
                }
            }
            response = requests.post(FEISHU_WEBHOOK, json=payload)
            return response.status_code == 200
    except Exception as e:
        log_action(f"发送失败：{str(e)}")
        return False

def log_action(message):
    """记录日志到文件"""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
    with open("tran_log.txt", "a") as f:
        f.write(f"{timestamp}{message}\n")

def send_to_feishu(image_path):
    """使用与rss_to_feishu.py相同的消息格式"""
    try:
        message = {
            "msg_type": "interactive",
            "card": {
                "elements": [{
                    "tag": "img",
                    "img_key": "img_v2_xxxxxxxx",  # 需替换实际的上传逻辑
                    "alt": {
                        "tag": "plain_text",
                        "content": os.path.basename(image_path)
                    }
                }]
            }
        }
        response = requests.post(FEISHU_WEBHOOK, json=message)
        return response.status_code == 200
    except Exception as e:
        log_action(f"发送失败：{str(e)}")
        return False

# 新增图片上传函数（参考rss_to_feishu中的实现）
def upload_image_to_feishu(image_path, token):
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
        response = requests.post(url, headers=headers, files=files)
        
    if response.status_code == 200:
        return response.json().get("data", {}).get("image_key")
    return None

# 在发送消息前先上传图片
def send_to_feishu(image_path):
    try:
        token = get_feishu_token()
        image_key = upload_image_to_feishu(image_path, token)
        
        if image_key:
            message = {
                "msg_type": "image",
                "content": {"image_key": image_key}
            }
            response = requests.post(FEISHU_WEBHOOK, json=message)
            return response.status_code == 200
        return False
    except Exception as e:
        log_action(f"发送失败：{str(e)}")
        return False

def get_dates():
    today = datetime.today()
    return {
        "today": today.strftime("%m.%d"),
        "monday": (today - timedelta(days=today.weekday())).strftime("%m.%d"),
        "tomorrow": (today + timedelta(days=1)).strftime("%m.%d")
    }

def capture_demand1():
    """执行需求一：本周天气截图"""
    dates = get_dates()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("http://www.nmc.cn/publish/forecast/AZJ/hangzhou.html")
            page.wait_for_selector('div#realChart.hp.mt15')
            page.query_selector('div#realChart.hp.mt15').screenshot(path=f'week_{dates["monday"]}.jpg')
            browser.close()
        log_action("需求一执行成功")
        if send_to_feishu(f'week_{dates["monday"]}.jpg'):
            log_action("需求一图片发送成功")
    except Exception as e:
        log_action(f"需求一失败：{str(e)}")

def capture_demand23():
    """执行需求二、三：今日和明日天气"""
    dates = get_dates()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("http://www.nmc.cn/publish/forecast/AZJ/hangzhou.html")
            
            # 今日天气
            page.wait_for_selector('div.weather-header')
            page.query_selector('div.weather-header').screenshot(path=f'weather_{dates["today"]}.jpg')
            
            # 明日天气
            page.query_selector('div.weather.pull-left.selected').evaluate('''el => el.nextElementSibling?.click()''')
            page.wait_for_timeout(3000)
            page.query_selector('div.weather-header').screenshot(path=f'weather_{dates["tomorrow"]}.jpg')
            
            browser.close()
        
        log_action("需求二、三执行成功")
        for img in [f'weather_{dates["today"]}.jpg', f'weather_{dates["tomorrow"]}.jpg']:
            if send_to_feishu(img):
                log_action(f"{img}发送成功")
    except Exception as e:
        log_action(f"需求二、三失败：{str(e)}")

def cleanup_job():
    """定时清理任务"""
    try:
        [os.remove(f) for f in os.listdir() if f.endswith('.jpg')]
        log_action("垃圾文件清理完成")
    except Exception as e:
        log_action(f"清理失败：{str(e)}")

def setup_scheduler():
    """配置定时任务"""
    schedule.every().wednesday.at("07:00").do(capture_demand1)
    schedule.every().sunday.at("07:00").do(capture_demand1)
    # schedule.every().day.at("07:10").do(capture_demand23)
    # schedule.every().day.at("22:00").do(cleanup_job)
    schedule.every(10).seconds.do(capture_demand23)
    schedule.every().day.at("07:03").do(capture_demand23)
    schedule.every().day.at("00:55").do(cleanup_job)



if __name__ == "__main__":
    setup_scheduler()
    log_action("服务启动成功")
    while True:
        schedule.run_pending()
        time.sleep(60)