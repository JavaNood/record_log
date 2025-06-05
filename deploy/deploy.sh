#!/bin/bash

# 个人博客系统部署脚本
# 用于Ubuntu服务器自动化部署

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="record_log"
PROJECT_USER="myblog"
PROJECT_DIR="/home/$PROJECT_USER/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
NGINX_CONF="/etc/nginx/sites-available/$PROJECT_NAME"
SUPERVISOR_CONF="/etc/supervisor/conf.d/$PROJECT_NAME.conf"

echo -e "${GREEN}开始部署个人博客系统...${NC}"

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}请不要使用root用户运行此脚本${NC}"
   exit 1
fi

# 1. 更新系统包
echo -e "${YELLOW}更新系统包...${NC}"
sudo apt update

# 2. 安装依赖
echo -e "${YELLOW}检查并安装系统依赖...${NC}"
sudo apt install -y python3 python3-pip python3-venv nginx supervisor mysql-server

# 3. 创建项目目录
echo -e "${YELLOW}创建项目目录...${NC}"
mkdir -p $PROJECT_DIR/logs

# 4. 创建虚拟环境
echo -e "${YELLOW}创建Python虚拟环境...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# 5. 激活虚拟环境并安装依赖
echo -e "${YELLOW}安装Python依赖...${NC}"
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. 复制配置文件
echo -e "${YELLOW}配置Nginx...${NC}"
sudo cp deploy/nginx.conf $NGINX_CONF
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo -e "${YELLOW}配置Supervisor...${NC}"
sudo cp deploy/supervisor.conf $SUPERVISOR_CONF

# 7. 测试Nginx配置
echo -e "${YELLOW}测试Nginx配置...${NC}"
sudo nginx -t

# 8. 初始化数据库（如果需要）
echo -e "${YELLOW}初始化数据库...${NC}"
if [ ! -f "$PROJECT_DIR/.db_initialized" ]; then
    read -p "是否需要初始化数据库？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python init_db.py
        touch "$PROJECT_DIR/.db_initialized"
    fi
fi

# 9. 设置文件权限
echo -e "${YELLOW}设置文件权限...${NC}"
sudo chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR
chmod +x deploy/*.sh

# 10. 重启服务
echo -e "${YELLOW}重启服务...${NC}"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart $PROJECT_NAME
sudo systemctl reload nginx

# 11. 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
sleep 3
if sudo supervisorctl status $PROJECT_NAME | grep -q "RUNNING"; then
    echo -e "${GREEN}应用服务启动成功${NC}"
else
    echo -e "${RED}应用服务启动失败${NC}"
    sudo supervisorctl status $PROJECT_NAME
fi

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx服务运行正常${NC}"
else
    echo -e "${RED}Nginx服务异常${NC}"
    sudo systemctl status nginx
fi

echo -e "${GREEN}部署完成！${NC}"
echo -e "${YELLOW}访问地址: http://$(hostname -I | awk '{print $1}')${NC}"
echo -e "${YELLOW}如果配置了域名: http://www.rlj.net.cn${NC}"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "  查看应用状态: sudo supervisorctl status $PROJECT_NAME"
echo "  重启应用: sudo supervisorctl restart $PROJECT_NAME"
echo "  查看应用日志: tail -f $PROJECT_DIR/logs/supervisor.log"
echo "  查看Nginx日志: sudo tail -f /var/log/nginx/record_log_error.log" 