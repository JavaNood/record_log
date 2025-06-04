# 个人日记Web应用架构设计

## 项目概述

基于Python Flask框架的个人日记Web应用，支持文章发布、标签管理、权限控制等功能。前端采用传统模板渲染，后端提供管理界面，支持Markdown编辑和图片上传。

## 技术栈

- **后端**: Python 3.8+ + Flask + SQLAlchemy
- **数据库**: MySQL 8.0
- **缓存**: Redis (可选)
- **前端**: HTML5 + CSS3 + JavaScript + Bootstrap
- **Web服务器**: Nginx
- **部署**: Ubuntu + Supervisor/systemd

## 1. 文件+文件夹结构

```
myblog/
├── app/
│   ├── __init__.py                 # Flask应用初始化
│   ├── models.py                   # 数据库模型
│   ├── config.py                   # 配置文件
│   ├── utils.py                    # 工具函数
│   ├── auth.py                     # 认证相关
│   ├── frontend/                   # 前端视图
│   │   ├── __init__.py
│   │   ├── views.py                # 前端路由和视图
│   │   └── utils.py                # 前端工具函数
│   ├── admin/                      # 后台管理
│   │   ├── __init__.py
│   │   ├── views.py                # 后台路由和视图
│   │   └── forms.py                # 表单类
│   └── api/                        # API接口(可选)
│       ├── __init__.py
│       └── views.py
├── templates/                      # 模板文件
│   ├── base.html                   # 基础模板
│   ├── frontend/                   # 前端模板
│   │   ├── index.html              # 首页
│   │   ├── about.html              # 关于页
│   │   ├── article.html            # 文章详情页
│   │   └── verify.html             # 验证弹窗
│   └── admin/                      # 后台模板
│       ├── base.html               # 后台基础模板
│       ├── login.html              # 登录页
│       ├── dashboard.html          # 后台首页
│       ├── articles.html           # 文章管理
│       ├── article_edit.html       # 文章编辑
│       ├── tags.html               # 标签管理
│       ├── welcome_edit.html       # 欢迎语编辑
│       ├── about_edit.html         # 关于页编辑
│       ├── background_edit.html    # 背景设置
│       └── password_change.html    # 密码修改
├── static/                         # 静态文件
│   ├── css/
│   │   ├── style.css               # 主样式
│   │   ├── admin.css               # 后台样式
│   │   └── bootstrap.min.css       # Bootstrap
│   ├── js/
│   │   ├── main.js                 # 主要JavaScript
│   │   ├── admin.js                # 后台JavaScript
│   │   ├── markdown-editor.js      # Markdown编辑器
│   │   └── jquery.min.js           # jQuery
│   ├── images/
│   │   ├── backgrounds/            # 背景图片
│   │   └── uploads/                # 文章图片上传
│   └── uploads/                    # 文件上传目录
├── migrations/                     # 数据库迁移文件
├── logs/                          # 日志文件
├── requirements.txt               # Python依赖
├── config.py                      # 配置文件
├── run.py                         # 应用启动文件
├── wsgi.py                        # WSGI入口
├── deploy/                        # 部署相关
│   ├── nginx.conf                 # Nginx配置
│   ├── supervisor.conf            # Supervisor配置
│   ├── systemd.service            # Systemd服务配置
│   └── deploy.sh                  # 部署脚本
└── README.md                      # 项目说明
```

## 2. 各部分功能说明

### 2.1 核心模块

#### `app/__init__.py`
- Flask应用工厂函数
- 扩展初始化（SQLAlchemy、Redis等）
- 蓝图注册

#### `app/models.py`
- **Article**: 文章模型（标题、内容、权限、标签、浏览数、置顶状态）
- **Tag**: 标签模型
- **Admin**: 管理员模型
- **Config**: 系统配置模型（欢迎语、关于页、背景图）
- **ArticleTag**: 文章标签关联表

#### `app/config.py`
- 数据库连接配置
- Redis配置
- 文件上传配置
- 安全密钥配置

### 2.2 前端模块 (`app/frontend/`)

#### `views.py`
- **首页路由** (`/`): 文章列表、时间线、搜索、筛选
- **关于页路由** (`/about`): 个人介绍、版本日志、随手日记
- **文章详情路由** (`/article/<id>`): 文章内容、权限验证
- **文章验证路由** (`/verify/<id>`): 验证答案检查

### 2.3 后台管理模块 (`app/admin/`)

#### `views.py`
- **登录/登出** (`/admin/login`, `/admin/logout`)
- **后台首页** (`/admin/dashboard`)
- **文章管理** (`/admin/articles`): CRUD操作
- **文章编辑** (`/admin/article/edit/<id>`)
- **标签管理** (`/admin/tags`)
- **系统设置** (`/admin/settings`): 欢迎语、关于页、背景、密码

#### `forms.py`
- 文章编辑表单
- 标签管理表单
- 系统设置表单
- 登录表单

### 2.4 模板系统

#### 前端模板特点
- 响应式设计，天空淡蓝色背景
- Bootstrap框架保证美观性
- 时间线组件展示文章
- 搜索和筛选功能

#### 后台模板特点
- 简洁的管理界面
- Markdown编辑器集成
- 图片拖拽上传功能
- 表单验证和提示

## 3. 数据库设计

### 3.1 核心表结构

```sql
-- 文章表
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    summary TEXT,
    author VARCHAR(100),
    status ENUM('draft', 'published') DEFAULT 'draft',
    permission ENUM('public', 'private', 'verify') DEFAULT 'public',
    verify_question TEXT,
    verify_answer VARCHAR(255),
    is_top BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 标签表
CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#007bff',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 文章标签关联表
CREATE TABLE article_tags (
    article_id INT,
    tag_id INT,
    PRIMARY KEY (article_id, tag_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 管理员表
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 系统配置表
CREATE TABLE site_config (
    key_name VARCHAR(50) PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.2 配置存储

系统配置通过 `site_config` 表存储：
- `welcome_text`: 欢迎语内容
- `about_content`: 关于页内容
- `version_log`: 版本更新日志
- `diary_content`: 随手日记内容
- `background_image`: 背景图片路径

## 4. 状态存储位置

### 4.1 数据存储
- **MySQL数据库**: 结构化数据（文章、标签、用户、配置）
- **文件系统**: 上传的图片和背景图片
- **Redis缓存** (可选): 文章浏览数、热门文章列表

### 4.2 会话管理
- **Flask Session**: 管理员登录状态
- **Cookie**: 记住登录状态（可选）

### 4.3 文件存储结构
```
/var/www/myblog/static/
├── uploads/
│   ├── articles/          # 文章图片
│   └── backgrounds/       # 背景图片
└── cache/                 # 缓存文件
```

## 5. 服务器部署方案

### 5.1 服务器环境配置

#### 系统要求
- **操作系统**: Ubuntu 20.04 LTS
- **硬件**: 2核CPU, 2GB内存, 50GB SSD
- **用户**: myblog
- **域名**: www.rlj.net.cn
- **公网IP**: 43.142.171.111

#### 软件栈安装
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和相关工具
sudo apt install python3 python3-pip python3-venv nginx mysql-server redis-server -y

# 安装Supervisor进程管理
sudo apt install supervisor -y
```

### 5.2 应用部署步骤

#### 1. 项目部署
```bash
# 切换到myblog用户
sudo su - myblog

# 创建项目目录
mkdir -p /home/myblog/www
cd /home/myblog/www

# 克隆或上传项目代码
git clone <your-repo> myblog
cd myblog

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 数据库配置
```bash
# 登录MySQL
sudo mysql -u root -p

# 创建数据库和用户
CREATE DATABASE myblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'myblog'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON myblog.* TO 'myblog'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. 应用配置
```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://myblog:password@localhost/myblog'
    UPLOAD_FOLDER = '/home/myblog/www/myblog/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    REDIS_URL = 'redis://localhost:6379/0'
```

#### 4. Nginx配置
```nginx
# /etc/nginx/sites-available/myblog
server {
    listen 80;
    server_name www.rlj.net.cn rlj.net.cn;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /home/myblog/www/myblog/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    client_max_body_size 20M;
}
```

#### 5. Supervisor配置
```ini
# /etc/supervisor/conf.d/myblog.conf
[program:myblog]
command=/home/myblog/www/myblog/venv/bin/python wsgi.py
directory=/home/myblog/www/myblog
user=myblog
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/myblog/www/myblog/logs/app.log
environment=FLASK_ENV=production
```

### 5.3 部署命令序列

```bash
# 1. 启用Nginx站点
sudo ln -s /etc/nginx/sites-available/myblog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 2. 初始化数据库
cd /home/myblog/www/myblog
source venv/bin/activate
flask db upgrade

# 3. 启动应用
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start myblog

# 4. 创建管理员账户
python -c "
from app import create_app, db
from app.models import Admin
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = Admin(username='admin', password_hash=generate_password_hash('your_password'))
    db.session.add(admin)
    db.session.commit()
"
```

### 5.4 SSL配置（推荐）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d www.rlj.net.cn -d rlj.net.cn

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 6. 安全考虑

### 6.1 基础安全措施
- CSRF保护（Flask-WTF）
- SQL注入防护（SQLAlchemy ORM）
- XSS防护（模板自动转义）
- 文件上传安全检查
- 管理员密码哈希存储

### 6.2 权限控制
- 管理员登录验证
- 文章权限验证
- 文件上传权限检查

### 6.3 生产环境安全
- 关闭Flask调试模式
- 设置强密码策略
- 定期备份数据库
- 监控异常访问

## 7. 监控和维护

### 7.1 日志管理
- 应用日志：`/home/myblog/www/myblog/logs/`
- Nginx日志：`/var/log/nginx/`
- 系统日志：`/var/log/syslog`

### 7.2 备份策略
```bash
# 数据库备份脚本
#!/bin/bash
mysqldump -u myblog -p myblog > /home/myblog/backup/myblog_$(date +%Y%m%d).sql
```

### 7.3 性能优化
- 启用Gzip压缩
- 静态文件缓存
- 数据库索引优化
- Redis缓存热点数据

---

此架构设计遵循最小化MVP原则，满足所有功能需求，具备良好的扩展性和可维护性。 