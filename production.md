# 生产环境部署文档

## 服务器信息

- **IP地址**: 43.142.171.111
- **域名**: www.rlj.net.cn
- **配置**: 2C2G50GB SSD
- **部署用户**: myblog
- **部署目录**: /home/myblog/record_log
- **MySQL用户**: blog_user
- **数据库名**: record_log

## SSL证书配置

- **证书文件**: /etc/nginx/rlj.net.cn_bundle.crt
- **私钥文件**: /etc/nginx/rlj.net.cn.key

## 部署前准备

### 1. 环境变量设置

环境变量将在Supervisor配置中直接设置，无需手动配置系统环境变量。

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

# 或者使用scp上传代码，文件上传
# scp -r ./record_log myblog@43.142.171.111:/home/myblog/
```

### 2. Python环境配置

```bash
#创建
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 升级pip（如果需要）
pip install --upgrade pip
```

### 3. 数据库初始化

```bash
# 全新部署：初始化数据库（仅首次部署）
python init_db.py

# 如果是现有数据库需要添加访问统计功能：
# python update_db.py

# 注意：全新环境使用 init_db.py，现有环境升级使用 update_db.py
```

### 4. 静态文件权限设置

```bash
# Git已包含所需的文件夹结构，只需设置权限
chmod -R 755 static/
chown -R myblog:myblog static/

# 验证目录结构（应该已存在,不存在就创建）
ls -la static/
ls -la static/images/
ls -la static/uploads/
```

### 5. 配置Nginx

```bash
# 复制Nginx配置
sudo cp deploy/nginx.conf /etc/nginx/sites-available/record_log

# 启用站点
sudo ln -sf /etc/nginx/sites-available/record_log /etc/nginx/sites-enabled/

# 删除默认站点（如果存在）
sudo rm -f /etc/nginx/sites-enabled/default

# 编辑/etc/nginx/nginx.conf ,在http处添加：
http {
    include /etc/nginx/sites-enabled/*;
    include       mime.types;
    default_type  application/octet-stream;
    ...}


# 测试Nginx配置
sudo nginx -t

# 启动Nginx服务（如果未启动）
sudo systemctl start nginx
sudo systemctl enable nginx

# 测试Nginx配置
sudo nginx -t

# 重新加载Nginx
sudo systemctl reload nginx
```

### 6. 配置Supervisor

```bash
# 复制Supervisor配置
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/record_log.conf

# 复制gunicorn.conf.py ,作为引用
sudo cp deploy/gunicorn.conf.py /home/myblog/record_log
# ⚠️ 重要：编辑配置文件，可以更新密码和密钥
sudo nano /etc/supervisor/conf.d/record_log.conf

# 在environment行中修改以下内容（注意：不要有引号，用逗号分隔）：
# environment=FLASK_CONFIG=production,SECRET_KEY=你的实际密钥,DATABASE_URL=mysql+pymysql://blog_user:你的实际密码@localhost/record_log,PYTHONPATH=/home/myblog/record_log,PATH=/home/myblog/record_log/venv/bin

# 示例：
# environment=FLASK_CONFIG=production,SECRET_KEY=9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c,DATABASE_URL=mysql+pymysql://blog_user:StrongPass123@localhost/record_log,PYTHONPATH=/home/myblog/record_log,PATH=/home/myblog/record_log/venv/bin

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
curl -I https://www.rlj.net.cn
```

### 2. 功能测试

1. **访问网站**: https://www.rlj.net.cn
2. **HTTP重定向**: http://www.rlj.net.cn 应自动重定向到HTTPS
3. **管理后台**: https://www.rlj.net.cn/admin/login
4. **静态文件**: 检查CSS、JS、图片加载
5. **数据库连接**: 测试文章创建和读取

## 监控和维护

### 1. 日志位置

```bash
# 应用日志
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
# 重启应用
sudo supervisorctl restart record_log

# 重新加载Nginx
sudo systemctl reload nginx

# 查看系统状态
./deploy/monitor.sh

# 更新代码
cd /home/myblog/record_log
git pull origin main
## 强烈建议先备份代码
sudo cp /home/myblog/record_log/* /home/myblog/bakxxxx/
sudo supervisorctl restart record_log

# 修改supervisor配置文件
# 先备份
sudo cp xxx xxx.conf.bakxxx
sudo vim /etc/supervisor/conf.d/record_log.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start record_log
sudo supervisorctl restart record_log
sudo supervisorctl status record_log

# 修改gunicorn配置文件
## 先备份
sudo cp xxx xxxx.py.bak
sudo vim /home/myblog/record_log/gunicorn.conf.py
sudo supervisorctl restart record_log #由于supervisor管理gunicorn

# 修改nginx
#先备份
sudo cp /etc/nginx/sites-available/record_log /etc/nginx/sites-available/record_log.bak
sudo vim /etc/nginx/sites-available/record_log
# 检查结果
sudo nginx -t

# 修改服务配置重启：
sudo systemctl reload nginx

# 中断服务重启
sudo systemctl restart nginx

#验证结果
sudo systemctl status nginx

# 测试访问
curl -I http://your_domain.com

# 回滚
# 恢复备份配置
sudo cp /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf
# 重新加载
sudo nginx -t && sudo systemctl reload nginx
```


### 3. 备份策略

```bash
# 数据库备份
mysqldump -u blog_user -p record_log > backup_$(date +%Y%m%d_%H%M%S).sql

# 文件备份
tar -czf backup_files_$(date +%Y%m%d_%H%M%S).tar.gz static/images/uploads/
```

### 4.日志轮转


### 5.git提交


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
   sudo ls -la /etc/nginx/rlj.net.cn*
   
   # 测试SSL
   openssl s_client -connect www.rlj.net.cn:443
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