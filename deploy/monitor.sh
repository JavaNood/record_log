#!/bin/bash

# 系统监控脚本 - 个人博客系统

echo "========================================="
echo "个人博客系统监控报告 - $(date)"
echo "========================================="

echo -e "\n系统资源状态:"
echo "负载情况："
uptime

echo -e "\n内存使用："
free -h

echo -e "\n磁盘使用："
df -h /

echo -e "\n应用服务状态:"
sudo supervisorctl status record_log

echo -e "\nWeb服务状态:"
sudo systemctl status nginx --no-pager -l

echo -e "\n数据库状态:"
sudo systemctl status mysql --no-pager -l

echo -e "\n应用健康检查:"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost/ || echo "连接失败"

echo -e "\n相关进程:"
ps aux | grep -E "(gunicorn|nginx)" | grep -v grep

echo "=========================================" 