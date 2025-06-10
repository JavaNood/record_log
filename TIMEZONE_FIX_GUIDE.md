# 生产环境时区修复部署指南

## 问题描述

当前系统使用 `datetime.utcnow()` 存储时间，导致显示的时间比实际时间少8小时（中国时区问题）。

## 解决方案概述

1. 创建时区处理工具函数
2. 修改代码使用本地时间
3. 转换数据库中的现有数据
4. 安全部署到生产环境

## 生产环境部署步骤

### 第一步：备份数据库

```bash
# 备份MySQL数据库
mysqldump -u your_username -p your_database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# 验证备份文件
ls -la backup_*.sql
```

### 第二步：停止应用服务

```bash
# 停止supervisor管理的应用
sudo supervisorctl stop record_log

# 或者停止所有相关进程
sudo supervisorctl stop all

# 验证进程已停止
sudo supervisorctl status
```

### 第三步：备份代码

```bash
# 进入应用目录
cd /path/to/your/app

# 创建代码备份
cp -r . ../app_backup_$(date +%Y%m%d_%H%M%S)

# 或者使用git创建标签
git tag backup-before-timezone-fix-$(date +%Y%m%d)
git push origin --tags
```

### 第四步：更新代码

```bash
# 拉取最新代码
git pull origin main

# 或者如果是手动上传，替换文件：
# - app/utils.py (新文件)
# - app/models.py (修改)
# - app/admin/views.py (修改)  
# - app/__init__.py (修改)
# - fix_timezone.py (新文件)
```

### 第五步：激活虚拟环境

```bash
# 激活虚拟环境
source venv/bin/activate

# 检查Python包（确保没有新的依赖问题）
pip check
```

### 第六步：预览时区修复

```bash
# 预览将要修改的数据
python fix_timezone.py --preview
```

**示例输出：**
```
ARTICLES 表:
  记录数量: 25
  最早时间: 2024-01-01 10:30:00 -> 2024-01-01 18:30:00
  最晚时间: 2024-06-10 09:15:30 -> 2024-06-10 17:15:30

VISITS 表:
  记录数量: 1523
  最早时间: 2024-01-01 08:00:00 -> 2024-01-01 16:00:00
  最晚时间: 2024-06-10 09:20:45 -> 2024-06-10 17:20:45

总计将修改 3096 个时间字段
```

### 第七步：执行时区修复

```bash
# 执行修复（需要确认）
python fix_timezone.py --fix
```

**确认提示：**
```
确认要执行时区修复吗？这将修改数据库中的时间数据 (输入 'yes' 确认): yes
```

### 第八步：验证修复结果

```bash
# 检查一些记录的时间是否正确
mysql -u username -p database_name -e "
SELECT id, title, created_at, updated_at 
FROM articles 
ORDER BY created_at DESC 
LIMIT 5;"
```

### 第九步：重启应用服务

```bash
# 重启supervisor管理的应用
sudo supervisorctl start record_log

# 检查状态
sudo supervisorctl status

# 检查日志
sudo supervisorctl tail -f record_log
```

### 第十步：功能验证

1. **登录后台管理**：
   - 访问 `https://your-domain.com/admin`
   - 检查文章列表的创建时间和更新时间

2. **创建测试文章**：
   - 创建一篇新文章
   - 验证显示的时间是否为当前本地时间

3. **检查访问统计**：
   - 查看访问统计页面
   - 确认访问时间显示正确

## 回滚步骤（如果出现问题）

### 方案一：使用脚本回滚

```bash
# 停止服务
sudo supervisorctl stop record_log

# 回滚时区修复
python fix_timezone.py --rollback

# 恢复旧版本代码
git checkout HEAD~1  # 或者具体的commit hash

# 重启服务
sudo supervisorctl start record_log
```

### 方案二：恢复数据库备份

```bash
# 停止服务
sudo supervisorctl stop record_log

# 恢复数据库
mysql -u username -p database_name < backup_YYYYMMDD_HHMMSS.sql

# 恢复代码
rm -rf /path/to/app
mv /path/to/app_backup_YYYYMMDD_HHMMSS /path/to/app

# 重启服务
sudo supervisorctl start record_log
```

## 监控和验证

### 日志检查

```bash
# 检查应用日志
tail -f logs/record_log.log

# 检查nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 检查supervisor日志
tail -f /var/log/supervisor/supervisord.log
```

### 功能测试清单

- [ ] 管理后台可以正常访问
- [ ] 文章列表时间显示正确
- [ ] 新创建文章时间正确
- [ ] 文章编辑后更新时间正确
- [ ] 访问统计时间正确
- [ ] 前端文章显示时间正确

## 注意事项

1. **服务器时间确认**：
   ```bash
   # 确认服务器时区设置
   timedatectl
   
   # 如果时区不正确，设置为中国时区
   sudo timedatectl set-timezone Asia/Shanghai
   ```

2. **MySQL时区设置**：
   ```sql
   -- 检查MySQL时区
   SELECT @@global.time_zone, @@session.time_zone;
   
   -- 如果需要，设置MySQL时区
   SET GLOBAL time_zone = '+08:00';
   ```

3. **备份策略**：
   - 修复完成后，建立新的备份
   - 定期验证备份文件的完整性

4. **性能监控**：
   - 修复后监控应用性能
   - 观察数据库查询是否正常

## 常见问题

**Q：修复后新创建的时间是否正确？**
A：是的，代码已修改为使用本地时间，新记录会自动使用正确时区。

**Q：如果部分数据修复失败怎么办？**
A：脚本会在出错时回滚事务，可以检查错误信息后重新执行。

**Q：修复会影响API接口吗？**
A：API返回的时间格式不变，但时间值会更正确。建议测试相关接口。

**Q：访问统计的历史数据准确吗？**
A：历史访问数据的时间会被统一修正，统计分析会更准确。

## 联系支持

如果在部署过程中遇到问题，请保留：
- 错误日志
- 数据库备份文件
- 操作步骤记录

以便快速排查和解决问题。