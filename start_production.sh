#!/bin/bash

# 生产环境启动脚本

# 设置环境变量
export FLASK_CONFIG=production
export FLASK_DEBUG=false

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 确保日志目录存在
mkdir -p logs

# 启动应用
echo "启动生产环境..."
gunicorn -c deploy/gunicorn.conf.py wsgi:application 