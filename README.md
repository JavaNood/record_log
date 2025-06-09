# 个人博客系统部署文档

本文档详细介绍如何在不同环境下部署个人博客系统。

## 📋 目录

- [系统要求](#系统要求)
- [Windows 本地部署](#windows-本地部署)
- [macOS 本地部署](#macos-本地部署)

## 🔧 系统要求

### 基础环境
- Python 3.8+
- MySQL 5.7+ 或 8.0+
- Git
### Python 依赖
```
请参考requirements.txt
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
git clone https://github.com/JavaNood/record_log.git
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

# 如果是升级现有系统，例如需要添加访问统计功能：
# python update_db.py
```

#### 2.6 启动应用
```cmd
# 启动开发服务器
python run_dev.py
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