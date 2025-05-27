import os
import time
import datetime
from playwright.sync_api import sync_playwright

def format_date(date):
    """将日期格式化为MM.DD格式"""
    return date.strftime("%m.%d")

def get_monday_date():
    """获取本周一的日期"""
    today = datetime.datetime.now()
    days_since_monday = today.weekday()
    monday = today - datetime.timedelta(days=days_since_monday)
    return monday

def capture_weather_screenshots(output_dir="./Weather"):
    """使用Playwright捕获天气网站截图
    
    Args:
        output_dir: 图片保存目录，默认为./Weather
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 访问天气网站
        page.goto("http://www.nmc.cn/publish/forecast/AZJ/hangzhou.html")
        print("页面加载完成")
        
        # 等待页面加载完成
        page.wait_for_load_state("networkidle")
        
        # 1. 获取今日天气截图
        print("开始截取今日天气...")
        today = datetime.datetime.now()
        today_date_str = format_date(today)
        today_selector = "div.weather-header"
        
        # 确保元素可见
        page.wait_for_selector(today_selector, state="visible")
        
        # 截图并保存
        today_element = page.query_selector(today_selector)
        if today_element:
            today_filename = os.path.join(output_dir, f"weather_{today_date_str}.jpg")
            today_element.screenshot(path=today_filename)
            print(f"今日天气截图已保存: {today_filename}")
        else:
            print("未能找到今日天气元素")
        
        # 2. 获取明日天气截图
        print("开始截取明日天气...")
        tomorrow = today + datetime.timedelta(days=1)
        tomorrow_date_str = format_date(tomorrow)
        
        # 找到并点击明日天气标签
        # 使用XPath定位右侧第一个div.weather.pull-left
        page.wait_for_selector("div.weather.pull-left", state="visible")
        tomorrow_tab = page.query_selector("div.weather.pull-left.selected + div.weather.pull-left")
        
        if tomorrow_tab:
            # 点击切换到明日天气
            tomorrow_tab.click()
            
            # 等待切换完成
            page.wait_for_timeout(1000)  # 等待1秒确保切换完成
            
            # 截取明日天气header
            tomorrow_element = page.query_selector(today_selector)  # 使用相同的选择器，因为结构相同
            
            if tomorrow_element:
                tomorrow_filename = os.path.join(output_dir, f"weather_{tomorrow_date_str}.jpg")
                tomorrow_element.screenshot(path=tomorrow_filename)
                print(f"明日天气截图已保存: {tomorrow_filename}")
            else:
                print("未能找到明日天气元素")
        else:
            print("未能找到明日天气标签")
        
        # 3. 获取本周天气截图
        print("开始截取本周天气...")
        monday = get_monday_date()
        monday_date_str = format_date(monday)
        week_selector = "div#realChart.hp.mt15"
        
        # 确保元素可见
        page.wait_for_selector(week_selector, state="visible")
        
        # 截取本周天气图
        week_element = page.query_selector(week_selector)
        if week_element:
            week_filename = os.path.join(output_dir, f"week_{monday_date_str}.jpg")
            week_element.screenshot(path=week_filename)
            print(f"本周天气截图已保存: {week_filename}")
        else:
            print("未能找到本周天气元素")
        
        # 关闭浏览器
        browser.close()
        print("天气截图完成")
