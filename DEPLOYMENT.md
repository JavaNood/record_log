# 个人博客系统部署文档

本文档详细介绍如何在不同环境下部署个人博客系统。

## 📋 目录

- [系统要求](#系统要求)
- [Windows 本地部署](#windows-本地部署)
- [macOS 本地部署](#macos-本地部署)
- [Ubuntu 服务器部署](#ubuntu-服务器部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 🔧 系统要求

### 基础环境
- Python 3.8+
- MySQL 5.7+ 或 8.0+
- Git

### Python 依赖
```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
PyMySQL==1.1.0
Flask-WTF==1.1.1
WTForms==3.0.1
markdown==3.5.1
```

---

## 🪟 Windows 本地部署

### 1. 环境准备

#### 1.1 安装 Python
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.8+ 版本
3. 安装时勾选 "Add Python to PATH"
4. 验证安装：
```cmd
python --version
pip --version
```

#### 1.2 安装 MySQL
1. 访问 https://dev.mysql.com/downloads/installer/
2. 下载 MySQL Installer
3. 安装时记住 root 密码
4. 启动 MySQL 服务

#### 1.3 安装 Git
1. 访问 https://git-scm.com/download/win
2. 下载并安装 Git for Windows

### 2. 项目部署

#### 2.1 克隆项目
```cmd
# 克隆项目到本地
git clone https://github.com/your-username/record_log.git
cd record_log
```

#### 2.2 创建虚拟环境
```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.3 配置数据库
```cmd
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE record_log DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（可选）
CREATE USER 'blog_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON record_log.* TO 'blog_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 2.4 配置应用
编辑 `config.py` 文件：
```python
# 数据库配置
DB_USERNAME = 'root'  # 或 'blog_user'
DB_PASSWORD = 'your_mysql_password'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'record_log'

# 安全密钥（请更改为随机字符串）
SECRET_KEY = 'your-secret-key-here'
```

#### 2.5 初始化数据库
```cmd
# 全新部署：初始化数据库（包含所有表结构和访问统计功能）
python init_db.py

# 如果是升级现有系统，需要添加访问统计功能：
# python update_db.py
```

#### 2.6 启动应用
```cmd
# 启动开发服务器
python run.py
```

访问 http://127.0.0.1:5000 查看应用

---

## 🍎 macOS 本地部署

### 1. 环境准备

#### 1.1 安装 Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 1.2 安装 Python
```bash
# 安装 Python
brew install python

# 验证安装
python3 --version
pip3 --version
```

#### 1.3 安装 MySQL
```bash
# 安装 MySQL
brew install mysql

# 启动 MySQL 服务
brew services start mysql

# 设置 root 密码
mysql_secure_installation
```

#### 1.4 安装 Git（通常已预装）
```bash
# 如果没有安装
brew install git
```

### 2. 项目部署

#### 2.1 克隆项目
```bash
# 克隆项目到本地
git clone https://github.com/your-username/record_log.git
cd record_log
```

#### 2.2 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.3 配置数据库
```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE record_log DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（可选）
CREATE USER 'blog_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON record_log.* TO 'blog_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 2.4 配置应用
编辑 `config.py` 文件（同 Windows）

#### 2.5 初始化数据库
```bash
# 全新部署：初始化数据库（包含所有表结构和访问统计功能）
python init_db.py

# 如果是升级现有系统，需要添加访问统计功能：
# python update_db.py
```

#### 2.6 启动应用
```bash
# 启动开发服务器
python run.py
```

访问 http://127.0.0.1:5000 查看应用

---

## 🐧 Ubuntu 服务器部署

### 服务器信息
- **域名**: www.rlj.net.cn
- **公网IP**: 43.142.171.111
- **用户**: myblog
- **配置**: 2C2G50GB SSD

### 1. 服务器初始化

#### 1.1 连接服务器
```bash
# 本地连接服务器
ssh myblog@43.142.171.111
```

#### 1.2 更新系统
```bash
# 更新包管理器
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget vim git htop ufw
```

#### 1.3 配置防火墙
```bash
# 启用防火墙
sudo ufw enable

# 允许 SSH
sudo ufw allow ssh

# 允许 HTTP 和 HTTPS
sudo ufw allow 80
sudo ufw allow 443

# 查看状态
sudo ufw status
```

### 2. 环境安装

#### 2.1 安装 Python
```bash
# 安装 Python 和相关工具
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 验证安装
python3 --version
pip3 --version
```

#### 2.2 安装 MySQL
```bash
# 安装 MySQL
sudo apt install -y mysql-server

# 启动 MySQL 服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation
```

#### 2.3 安装 Nginx
```bash
# 安装 Nginx
sudo apt install -y nginx

# 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 2.4 安装 Supervisor
```bash
# 安装 Supervisor（进程管理）
sudo apt install -y supervisor

# 启动 Supervisor
sudo systemctl start supervisor
sudo systemctl enable supervisor
```

### 3. 项目部署

#### 3.1 创建项目目录
```bash
# 切换到用户目录
cd /home/myblog

# 克隆项目
git clone https://github.com/your-username/record_log.git
cd record_log

# 设置权限
sudo chown -R myblog:myblog /home/myblog/record_log
```

#### 3.2 配置 Python 环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 安装生产环境依赖
pip install gunicorn
```

#### 3.3 配置数据库
```bash
# 登录 MySQL
sudo mysql

# 创建数据库和用户
CREATE DATABASE record_log DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'blog_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON record_log.* TO 'blog_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3.4 配置应用
创建生产环境配置文件 `config_prod.py`：
```bash
# 创建生产配置
vim config_prod.py
```

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# 数据库配置
DB_USERNAME = 'blog_user'
DB_PASSWORD = 'StrongPassword123!'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'record_log'

# 构建数据库连接字符串
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

# 安全配置
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secure-secret-key-for-production'

# 生产环境设置
DEBUG = False
TESTING = False

# 文件上传配置
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = 'static/images/uploads'

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 日志配置
LOGGING_LEVEL = 'INFO'
LOG_FILE = 'logs/app.log'

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)
```

#### 3.5 修改启动文件
创建生产环境启动文件 `run_prod.py`：
```bash
vim run_prod.py
```

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入生产配置
import config_prod

# 导入应用
from app import create_app

# 创建应用实例
app = create_app()

# 更新配置
app.config.from_object(config_prod)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### 3.6 初始化数据库
```bash
# 全新部署：使用生产配置初始化数据库（包含所有表结构和访问统计功能）
FLASK_ENV=production python init_db.py

# 如果是升级现有系统，需要添加访问统计功能：
# FLASK_ENV=production python update_db.py

# 注意：
# - init_db.py: 全新环境，创建所有表结构
# - update_db.py: 现有环境，仅添加SiteVisit访问统计表
```

### 4. 配置 Gunicorn

#### 4.1 创建 Gunicorn 配置
```bash
vim gunicorn.conf.py
```

```python
# Gunicorn 配置文件
import multiprocessing

# 监听地址和端口
bind = "127.0.0.1:5000"

# 工作进程数（CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 连接超时
timeout = 30
keepalive = 2

# 用户和组
user = "myblog"
group = "myblog"

# 最大请求数
max_requests = 1000
max_requests_jitter = 50

# 预加载应用
preload_app = True

# 日志
accesslog = "/home/myblog/record_log/logs/gunicorn_access.log"
errorlog = "/home/myblog/record_log/logs/gunicorn_error.log"
loglevel = "info"

# 进程名
proc_name = "record_log"
```

#### 4.2 创建启动脚本
```bash
vim start_gunicorn.sh
```

```bash
#!/bin/bash

# 项目目录
PROJECT_DIR="/home/myblog/record_log"
cd $PROJECT_DIR

# 激活虚拟环境
source venv/bin/activate

# 启动 Gunicorn
exec gunicorn -c gunicorn.conf.py run_prod:app
```

```bash
# 设置执行权限
chmod +x start_gunicorn.sh
```

### 5. 配置 Supervisor

#### 5.1 创建 Supervisor 配置
```bash
sudo vim /etc/supervisor/conf.d/record_log.conf
```

```ini
[program:record_log]
command=/home/myblog/record_log/start_gunicorn.sh
directory=/home/myblog/record_log
user=myblog
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/myblog/record_log/logs/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=FLASK_ENV="production"
```

#### 5.2 启动服务
```bash
# 重新加载 Supervisor 配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动应用
sudo supervisorctl start record_log

# 查看状态
sudo supervisorctl status
```

### 6. 配置 Nginx

#### 6.1 创建 Nginx 配置
```bash
sudo vim /etc/nginx/sites-available/record_log
```

```nginx
server {
    listen 80;
    server_name www.rlj.net.cn rlj.net.cn 43.142.171.111;
    
    # 静态文件路径
    root /home/myblog/record_log;
    
    # 静态文件处理
    location /static {
        alias /home/myblog/record_log/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # 限制文件上传大小
    client_max_body_size 16M;
    
    # 日志
    access_log /var/log/nginx/record_log_access.log;
    error_log /var/log/nginx/record_log_error.log;
}
```

#### 6.2 启用站点
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/record_log /etc/nginx/sites-enabled/

# 删除默认站点
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 7. 配置 SSL（可选）

#### 7.1 安装 Certbot
```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx
```

#### 7.2 获取 SSL 证书
```bash
# 获取证书
sudo certbot --nginx -d www.rlj.net.cn -d rlj.net.cn

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 8. 系统优化

#### 8.1 创建日志轮转
```bash
sudo vim /etc/logrotate.d/record_log
```

```
/home/myblog/record_log/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 myblog myblog
}
```

#### 8.2 设置系统监控脚本
```bash
vim monitor.sh
```

```bash
#!/bin/bash

# 监控脚本
echo "=== $(date) ==="
echo "系统负载："
uptime

echo "内存使用："
free -h

echo "磁盘使用："
df -h

echo "应用状态："
sudo supervisorctl status record_log

echo "Nginx 状态："
sudo systemctl status nginx --no-pager -l

echo "MySQL 状态："
sudo systemctl status mysql --no-pager -l
```

```bash
# 设置执行权限
chmod +x monitor.sh

# 设置定时任务
crontab -e
# 添加：每小时执行监控
# 0 * * * * /home/myblog/record_log/monitor.sh >> /home/myblog/record_log/logs/monitor.log 2>&1
```

---

## ⚙️ 配置说明

### 数据库脚本说明

项目提供了两个数据库脚本：

#### `init_db.py` - 全新环境初始化
- **用途**: 全新部署时创建所有数据库表结构
- **包含功能**: 文章、标签、管理员、配置、访问统计等所有表
- **使用场景**: 首次部署、重置环境
- **命令**: `python init_db.py`

#### `update_db.py` - 现有环境升级
- **用途**: 为现有数据库添加访问统计功能
- **包含功能**: 仅创建 SiteVisit 访问统计表
- **使用场景**: 从旧版本升级到支持访问统计的版本
- **命令**: `python update_db.py`

**重要提示**: 
- 全新环境使用 `init_db.py`
- 已有数据的环境升级使用 `update_db.py`
- 两个脚本不要重复执行

### 管理员账户
默认管理员账户信息：
- 用户名: admin
- 密码: admin123

**⚠️ 首次登录后请立即修改密码！**

### 环境变量
生产环境建议设置以下环境变量：
```bash
export SECRET_KEY="your-very-secure-secret-key"
export FLASK_ENV="production"
export DATABASE_URL="mysql+pymysql://user:password@localhost/record_log"
```

### 文件上传
- 支持格式：PNG、JPG、JPEG、GIF、WebP、BMP
- 文件大小限制：16MB
- 存储路径：`static/images/uploads/`

---

## 🔧 常见问题

### Q1: 数据库连接失败
**A1**: 检查以下配置：
- MySQL 服务是否启动
- 用户名和密码是否正确
- 数据库是否存在
- 防火墙是否阻止连接

### Q2: 静态文件无法访问
**A2**: 检查以下设置：
- Nginx 配置中的静态文件路径
- 文件权限设置
- SELinux 或防火墙设置

### Q3: 应用无法启动
**A3**: 查看日志排查：
```bash
# 查看应用日志
tail -f /home/myblog/record_log/logs/supervisor.log

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/record_log_error.log

# 查看系统日志
sudo journalctl -u nginx -f
```

### Q4: 域名无法访问
**A4**: 检查以下配置：
- DNS 解析是否正确指向服务器 IP
- 防火墙端口 80/443 是否开放
- Nginx 配置是否正确

### Q5: 图片上传失败
**A5**: 检查以下设置：
- 上传目录权限 (`static/images/uploads/`)
- 文件大小限制
- 磁盘空间是否充足

---

## 📞 技术支持

如遇到部署问题，可以检查：
1. 系统日志：`/var/log/`
2. 应用日志：`logs/` 目录
3. Nginx 配置：`/etc/nginx/sites-available/`
4. Supervisor 配置：`/etc/supervisor/conf.d/`

**部署完成后，记得：**
- 修改默认管理员密码
- 设置定期备份
- 监控系统资源使用情况
- 定期更新系统和依赖包

---

**🎉 部署完成！访问 http://www.rlj.net.cn 查看您的博客网站！** 