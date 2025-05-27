# Linux定时服务配置

## 天气服务单元文件

创建系统服务文件：

```bash
sudo nano /etc/systemd/system/weather-to-feishu.service
```

内容如下：

```ini
[Unit]
Description=天气到飞书自动截图服务
After=network.target

[Service]
Type=simple
User=root  # 替换为实际运行服务的用户名
WorkingDirectory=/path/to/weather_to_Feishu  # 替换为项目的实际路径
ExecStart=/usr/bin/timeout 10m /usr/bin/python3 main.py
Restart=no

[Install]
WantedBy=multi-user.target
```

## 定时器单元文件

创建定时器文件：

```bash
sudo nano /etc/systemd/system/weather-to-feishu.timer
```

内容如下：

```ini
[Unit]
Description=每天早上7点运行天气到飞书截图服务

[Timer]
OnCalendar=*-*-* 07:00:00
AccuracySec=1s
Persistent=true

[Install]
WantedBy=timers.target
```

<!-- ## 启用服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用并启动定时器
sudo systemctl enable weather-to-feishu.timer
sudo systemctl start weather-to-feishu.timer

# 检查定时器状态
sudo systemctl status weather-to-feishu.timer

# 列出所有定时器
sudo systemctl list-timers
```

## 服务说明

1. 该服务将在每天早上7:00准时启动
2. 服务启动后会运行main.py
3. 通过timeout命令限制运行时间为10分钟
4. 10分钟后服务将自动停止

## 日志查看

可以使用以下命令查看服务日志：

```bash
sudo journalctl -u weather-to-feishu.service
```  -->