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

在服务器上设置以下环境变量：

```bash
# 创建环境变量文件
sudo nano /etc/environment

# 添加以下内容
SECRET_KEY="your-production-secret-key-here"
FLASK_CONFIG="production"
DATABASE_URL="mysql+pymysql://blog_user:%5E%28withrlj%40%40%23blog35%24%25RLJTTES1%21s@localhost:3306/record_log?charset=utf8mb4"
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
# scp -r ./record_log myblog@43.142.171.111:/home/myblog/
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
sudo supervisorctl restart record_log
```

### 3. 备份策略

```bash
# 数据库备份
mysqldump -u blog_user -p record_log > backup_$(date +%Y%m%d_%H%M%S).sql

# 文件备份
tar -czf backup_files_$(date +%Y%m%d_%H%M%S).tar.gz static/images/uploads/
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