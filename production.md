# 生产环境部署文档

## 服务器信息

- **IP地址**: 
- **域名**: 
- **配置**: 
- **部署用户**: myblog
- **部署目录**: /home/myblog/record_log
- **MySQL用户**: blog_user
- **数据库名**: record_log

## SSL证书配置

- **证书文件**: /etc/nginx/xxx.crt
- **私钥文件**: /etc/nginx/xxx.key

## 部署前准备

### 1. 环境变量设置

在服务器上设置以下环境变量：

```bash
# 创建环境变量文件
sudo nano /etc/environment

# 添加以下内容
SECRET_KEY="your-production-secret-key-here"
FLASK_CONFIG="production"
DATABASE_URL="mysql+pymysql://blog_user:your_password@localhost:3306/record_log?charset=utf8mb4"
```

### 2. 数据库准备

确保MySQL服务运行正常，数据库用户和权限已配置：

```sql
-- 检查用户权限
SHOW GRANTS FOR 'blog_user'@'localhost';

-- 检查数据库
USE record_log;
SHOW TABLES;
```

## 数据库脚本说明

项目提供了两个数据库脚本，请根据部署情况选择：

### `init_db.py` - 全新环境初始化
- **适用**: 全新的生产环境部署
- **功能**: 创建所有数据库表（文章、标签、管理员、配置、访问统计）
- **默认数据**: 创建默认管理员账户 (admin/admin123)

### `update_db.py` - 现有环境升级  
- **适用**: 已有数据库但缺少访问统计功能
- **功能**: 仅添加 SiteVisit 访问统计表
- **数据保护**: 不影响现有数据

**选择指南**:
- 全新服务器 → 使用 `init_db.py`
- 升级现有系统 → 使用 `update_db.py`

## 部署步骤

### 1. 项目代码上传

```bash
# 切换到部署用户
sudo su - myblog

# 进入项目目录
cd /home/myblog/record_log

# 从git仓库拉取最新代码
git pull origin main

# 或者使用scp上传代码
# scp -r 
```

### 2. Python环境配置

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 升级pip（如果需要）
pip install --upgrade pip
```

### 3. 数据库初始化

```bash


# 如果是现有数据库需要添加访问统计功能：
# python update_db.py

# 注意：全新环境使用 init_db.py，现有环境升级使用 update_db.py
```

### 4. 静态文件权限设置

```bash
# 设置静态文件目录权限
chmod -R 755 static/
chown -R myblog:myblog static/

# 创建上传目录
mkdir -p static/images/uploads
mkdir -p static/uploads
chmod 755 static/images/uploads
chmod 755 static/uploads
```

### 5. 配置Nginx

```bash
# 复制Nginx配置
sudo cp deploy/nginx.conf /etc/nginx/sites-available/record_log

# 启用站点
sudo ln -sf /etc/nginx/sites-available/record_log /etc/nginx/sites-enabled/

# 删除默认站点（如果存在）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t

# 重新加载Nginx
sudo systemctl reload nginx
```

### 6. 配置Supervisor

```bash
# 复制Supervisor配置
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/record_log.conf

# 重新读取配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动应用
sudo supervisorctl start record_log
```

### 7. 启动服务

```bash
# 检查服务状态
sudo supervisorctl status record_log

# 如果需要重启
sudo supervisorctl restart record_log

# 检查Nginx状态
sudo systemctl status nginx
```

## 验证部署

### 1. 服务检查

```bash
# 检查应用进程
ps aux | grep gunicorn

# 检查端口监听
netstat -tlnp | grep :5000

# 检查Nginx状态
sudo systemctl status nginx

# 检查SSL证书
curl -I https://
```

### 2. 功能测试

1. **访问网站**: https:
2. **HTTP重定向**: http: 应自动重定向到HTTPS
3. **管理后台**: https:/
4. **静态文件**: 检查CSS、JS、图片加载
5. **数据库连接**: 测试文章创建和读取

## 服务管理和更新流程

### 1. 停止服务

```bash
# 停止应用服务
sudo supervisorctl stop record_log

# 检查服务状态
sudo supervisorctl status record_log

# 如果需要完全下线，停止Nginx（可选）
sudo systemctl stop nginx
```

### 2. 代码更新流程

```bash
# 切换到部署用户
sudo su - myblog

# 进入项目目录
cd /home/myblog/record_log

# 备份当前版本（可选）
cp -r /home/myblog/record_log /home/myblog/record_log_backup_$(date +%Y%m%d_%H%M%S)

# 拉取最新代码
git fetch origin
git pull origin main

# 激活虚拟环境
source venv/bin/activate

# 更新依赖（如果requirements.txt有变化）
pip install -r requirements.txt

# 如果有数据库迁移
# python update_db.py

# 收集静态文件（如果有变化）
# 确保静态文件权限正确
chmod -R 755 static/
chown -R myblog:myblog static/

# 重启服务
sudo supervisorctl start record_log

# 检查服务状态
sudo supervisorctl status record_log
```

### 3. 零停机更新（推荐）

```bash
# 使用reload而不是restart，减少停机时间
sudo supervisorctl restart record_log

# 重新加载Nginx配置（如果有配置变化）
sudo nginx -t && sudo systemctl reload nginx

# 检查所有服务状态
sudo supervisorctl status
sudo systemctl status nginx
```

### 4. 回滚操作

```bash
# 如果更新出现问题，快速回滚
cd /home/myblog

# 停止当前服务
sudo supervisorctl stop record_log

# 恢复备份（假设备份目录名为 record_log_backup_YYYYMMDD_HHMMSS）
rm -rf record_log
mv record_log_backup_YYYYMMDD_HHMMSS record_log

# 重启服务
sudo supervisorctl start record_log
```

## 监控和维护

### 1. 日志位置

```bash
# 应用日志（新增的配置化日志）
tail -f /home/myblog/record_log/logs/record_log.log    # 应用主日志
tail -f /home/myblog/record_log/logs/access.log        # 访问日志
tail -f /home/myblog/record_log/logs/error.log         # 错误日志

# Supervisor日志
tail -f /home/myblog/record_log/logs/supervisor.log
tail -f /home/myblog/record_log/logs/gunicorn_access.log
tail -f /home/myblog/record_log/logs/gunicorn_error.log

# Nginx日志
tail -f /var/log/nginx/record_log_access.log
tail -f /var/log/nginx/record_log_error.log
tail -f /var/log/nginx/record_log_ssl_access.log
tail -f /var/log/nginx/record_log_ssl_error.log
```

### 2. 常用维护命令

```bash
# 服务管理
sudo supervisorctl restart record_log    # 重启应用
sudo supervisorctl reload record_log     # 重新加载配置
sudo supervisorctl stop record_log       # 停止应用
sudo supervisorctl start record_log      # 启动应用

# Nginx管理
sudo systemctl reload nginx              # 重新加载配置
sudo systemctl restart nginx             # 重启Nginx
sudo nginx -t                           # 测试配置文件

# 日志查看
tail -f /home/myblog/record_log/logs/record_log.log  # 实时查看应用日志
grep "ERROR" /home/myblog/record_log/logs/error.log  # 查看错误日志
grep "$(date +%Y-%m-%d)" /home/myblog/record_log/logs/access.log  # 查看今日访问日志

# 系统监控
ps aux | grep gunicorn                   # 查看进程
netstat -tlnp | grep :5000             # 查看端口
df -h                                   # 查看磁盘空间
free -h                                 # 查看内存使用
```

### 3. 完整更新流程（推荐）

```bash
#!/bin/bash
# 安全更新脚本

echo "开始更新部署..."

# 1. 备份当前版本
BACKUP_DIR="/home/myblog/backups/record_log_$(date +%Y%m%d_%H%M%S)"
echo "创建备份: $BACKUP_DIR"
sudo -u myblog mkdir -p /home/myblog/backups
sudo -u myblog cp -r /home/myblog/record_log $BACKUP_DIR

# 2. 更新代码
echo "更新代码..."
cd /home/myblog/record_log
sudo -u myblog git fetch origin
sudo -u myblog git pull origin main

# 3. 更新依赖
echo "更新依赖..."
sudo -u myblog bash -c "source venv/bin/activate && pip install -r requirements.txt"

# 4. 数据库迁移（如果需要）
# echo "执行数据库迁移..."
# sudo -u myblog bash -c "source venv/bin/activate && python update_db.py"

# 5. 重启服务
echo "重启服务..."
sudo supervisorctl restart record_log

# 6. 检查服务状态
echo "检查服务状态..."
sleep 3
if sudo supervisorctl status record_log | grep -q "RUNNING"; then
    echo "✅ 更新成功！服务正常运行"
    echo "备份保存在: $BACKUP_DIR"
else
    echo "❌ 更新失败！正在回滚..."
    sudo supervisorctl stop record_log
    sudo -u myblog rm -rf /home/myblog/record_log
    sudo -u myblog mv $BACKUP_DIR /home/myblog/record_log
    sudo supervisorctl start record_log
    echo "已回滚到之前版本"
    exit 1
fi
```

### 4. 日志管理

```bash
# 日志轮换（已自动配置，手动轮换）
sudo logrotate -f /etc/logrotate.d/record_log

# 清理旧日志（保留最近7天）
find /home/myblog/record_log/logs -name "*.log.*" -mtime +7 -delete

# 监控日志大小
du -sh /home/myblog/record_log/logs/
ls -lah /home/myblog/record_log/logs/

# 实时监控错误
tail -f /home/myblog/record_log/logs/error.log | grep -i error
```

### 5. 备份策略

```bash
# 自动备份脚本
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/myblog/backups"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
mysqldump -u blog_user -p record_log > $BACKUP_DIR/db_backup_$BACKUP_DATE.sql

# 文件备份
tar -czf $BACKUP_DIR/files_backup_$BACKUP_DATE.tar.gz -C /home/myblog/record_log static/uploads/

# 日志备份
tar -czf $BACKUP_DIR/logs_backup_$BACKUP_DATE.tar.gz -C /home/myblog/record_log logs/

# 清理7天前的备份
find $BACKUP_DIR -name "*backup_*" -mtime +7 -delete

echo "备份完成: $BACKUP_DATE"
```

### 6. 自动化部署脚本

保存为 `/home/myblog/update_deploy.sh`：

```bash
#!/bin/bash
# 自动化部署更新脚本

set -e  # 遇到错误立即退出

DEPLOY_USER="myblog"
DEPLOY_DIR="/home/myblog/record_log"
BACKUP_DIR="/home/myblog/backups"
LOG_FILE="/home/myblog/deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "开始部署更新..."

# 检查是否为部署用户
if [ "$USER" != "$DEPLOY_USER" ]; then
    log "错误: 请使用 $DEPLOY_USER 用户执行此脚本"
    exit 1
fi

# 创建备份
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/record_log_$TIMESTAMP"
log "创建备份: $BACKUP_PATH"
mkdir -p $BACKUP_DIR
cp -r $DEPLOY_DIR $BACKUP_PATH

# 更新代码
log "更新代码..."
cd $DEPLOY_DIR
git fetch origin
git pull origin main

# 激活虚拟环境并更新依赖
log "更新依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 检查配置语法
log "检查配置..."
python -c "from config import config; print('配置检查通过')"

# 重启服务
log "重启服务..."
sudo supervisorctl restart record_log

# 等待服务启动
sleep 5

# 检查服务状态
if sudo supervisorctl status record_log | grep -q "RUNNING"; then
    log "✅ 部署成功！服务正常运行"
    log "备份已保存: $BACKUP_PATH"
    
    # 测试网站响应
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200"; then
        log "✅ 网站响应正常"
    else
        log "⚠️  网站响应异常，请检查"
    fi
else
    log "❌ 部署失败！正在回滚..."
    sudo supervisorctl stop record_log
    rm -rf $DEPLOY_DIR
    mv $BACKUP_PATH $DEPLOY_DIR
    sudo supervisorctl start record_log
    log "已回滚到之前版本"
    exit 1
fi

log "部署完成"
```

## 安全注意事项

1. **环境变量**: 不要在代码中硬编码敏感信息
2. **文件权限**: 确保配置文件权限正确
3. **防火墙**: 只开放必要的端口（80, 443, 22）
4. **SSL证书**: 定期检查证书有效期
5. **定期备份**: 设置自动化备份任务
6. **日志监控**: 定期检查错误日志

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查MySQL服务
   sudo systemctl status mysql
   
   # 检查用户权限
   mysql -u blog_user -p
   ```

2. **静态文件404**
   ```bash
   # 检查文件权限
   ls -la static/
   
   # 检查Nginx配置
   sudo nginx -t
   ```

3. **应用无法启动**
   ```bash
   # 查看详细错误
   sudo supervisorctl tail record_log stderr
   
   # 手动启动测试
   cd /home/myblog/record_log
   source venv/bin/activate
   python wsgi.py
   ```

4. **SSL证书问题**
   ```bash
   # 检查证书文件
   sudo ls -la /etc/nginx/*
   
   # 测试SSL
   openssl s_client -connect www.xxxx:443
   ```

## 性能优化建议

1. **启用Gzip压缩** - 已在Nginx配置中启用
2. **静态文件缓存** - 已配置长期缓存
3. **数据库连接池** - 已在生产配置中配置
4. **CDN加速** - 可考虑使用CDN服务
5. **监控工具** - 建议使用监控服务

---

**部署完成时间**: 预计30-60分钟  
**维护联系**: 系统管理员  
**最后更新**: Task 38-1 生产环境部署 
