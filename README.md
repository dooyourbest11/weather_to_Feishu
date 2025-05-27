帮我写一个python程序:

一、监听jpg文件，上传文件到飞书云存储，再通过消息引用文件链接发送
1.主要功能：监听服务器某目录下存在的jpg文件，自动发送给飞书群的机器人
2.参考API文档，在项目引用文档里已经给出:Feishu , Feishu2

以下是详细描述：
1.文件监听功能：
    基于watchdog库实现，仅监听jpg类型
2.飞书消息发送功能：
    先上传文件到飞书云存储，再通过消息引用文件链接
    （1）发送的是watchdog监听的jpg文件，发送到【上传图片】接口
    （2）通过【上传图片】接口的响应拿到image_key
    （3）通过post请求，将image_key、webhook填入请求体，发送给飞书机器人，务必需严格匹配飞书机器人的请求体格式，参考API文档
3.去重功能：
    需避免重复发送，通过发送时间戳、文件名的方式去避免

二、天气网站截图
使用Playwright库，需要定位HTML网页的某些区域并进行截图并保存为jpg，地址为http://www.nmc.cn/publish/forecast/AZJ/hangzhou.html

以下是详细描述：
1.<今日天气截图> 
    1)定位到div.weather-header，截图保存为jpg文件，命名规则为weather_xx.jpg，保存到当前文件夹下。xx代表今日日期，格式形如05.22
2.<明日天气截图>
    1）找到div.weather.pull-left.selected区域右方的第一个div.weather.pull-left区域，选中该区域（模拟点击的操作）
    2）定位到div.weather-header，截图保存为jpg文件，命名规则为weather_xx.jpg，保存到当前文件夹下,xx代表明天的日期，格式形如05.22
3.<本周天气截图>
    1)定位到div#realChart.hp.mt15的整个区域，截图保存为jpg文件，命名为week_xxx.jpg，保存到当前文件夹下,xxx代表今天所在星期的星期一，格式形如05.22
    