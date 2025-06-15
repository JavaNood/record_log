# 🌟 个人博客系统 - Record Log

一个AI+的项目，个人博客系统，采用 Flask + MySQL 构建，专注于提供优质的写作和阅读体验。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-5.7+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

## 🎯 主要特性

### 📝 **内容管理**
- 🎨 **Markdown 编辑器** - 支持实时预览，内置工具栏快速插入格式
- 🏷️ **智能标签系统** - 彩色标签分类，支持多标签筛选
- 📋 **文章摘要** - 自定义首页展示内容，支持自动截取
- 📱 **响应式设计** - 完美适配桌面、平板、手机等设备

### 🔐 **访问控制**
- 🛡️ **文章验证机制** - 支持密码保护的私密文章
- 📊 **智能展示逻辑** - 验证文章可展示自定义摘要
- 🎯 **精确权限控制** - 灵活的公开/验证访问设置

### 💬 **互动功能**
- 💭 **评论系统** - 支持嵌套回复、审核机制
- ❤️ **点赞功能** - 一键点赞，实时统计
- 📍 **地理位置** - 自动获取评论者地理位置
- 🔔 **管理审核** - 后台评论审核、批量操作

### 🎵 **多媒体**
- 🎶 **背景音乐** - 支持上传音乐文件，自动播放控制
- 🖼️ **图片管理** - 图片上传、尺寸调整、对齐方式
- 🌈 **动态背景** - 多种预设背景，支持时间自动切换
- 🎭 **自定义主题** - 个性化背景图片和渐变效果

### 📈 **数据统计**
- 👁️ **访问统计** - 文章浏览数、访客统计
- 📊 **时间线导航** - 按时间排序的文章导航
- 🔍 **智能搜索** - 全文搜索，关键词高亮
- 📅 **时间筛选** - 按日期范围筛选文章

### 🎯 **用户体验**
- ⚡ **智能定位** - 返回时精确定位到原阅读位置
- 🔄 **无刷新操作** - AJAX 实现流畅交互体验
- 📖 **文章目录** - 自动生成文章目录，快速跳转
- 🎨 **优雅动画** - 平滑过渡效果和交互反馈

### 🛠️ **管理功能**
- 👨‍💼 **后台管理** - 功能完整的管理界面
- 📝 **批量操作** - 批量删除、状态修改
- 🎛️ **配置管理** - 网站设置、功能开关
- 📊 **数据统计** - 访问数据、内容统计

## 🔧 系统要求

- Python 3.8+
- MySQL 5.7+ 或 8.0+
- Git

## 🚀 快速部署

### Windows 本地部署

```cmd
# 1. 克隆项目
git clone https://github.com/JavaNood/record_log.git
cd record_log
注：如果没有安装git，可以下载代码文件进行解压

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置数据库
mysql -u root -p
CREATE DATABASE record_log DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 5. 修改配置文件 config.py
# 设置数据库连接
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://用户名:密码@localhost/数据库名'
# 6. 初始化数据库
python init_db.py --init

# 7. 启动服务
python run_dev.py
```

### macOS 本地部署

```bash
# 1. 安装依赖环境
brew install python mysql git

# 2. 克隆项目
git clone https://github.com/your-username/record_log.git
cd record_log

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置数据库
mysql -u root -p
CREATE DATABASE record_log DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 6. 修改配置文件 config.py
# 设置数据库连接

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://用户名:密码@localhost/数据库名'



# 7. 初始化数据库
python init_db.py

# 8. 启动服务
python run_dev.py
```
访问 http://127.0.0.1:5000 查看博客系统

## ⚙️ 配置说明

- **评论审核**：`COMMENT_AUTO_APPROVE = False` 开启评论审核
- **访问限制**：`COMMENT_RATE_LIMIT = 10` 设置评论频率限制
- **地理位置**：`COMMENT_ENABLE_LOCATION = True` 开启位置功能

## 📁 项目结构

```
record_log/
├── app/                    # 应用核心代码
│   ├── admin/             # 后台管理模块
│   ├── frontend/          # 前端展示模块
│   ├── api/               # API接口模块
│   └── models.py          # 数据模型
├── templates/             # HTML模板
│   ├── admin/            # 管理后台模板
│   ├── frontend/         # 前端展示模板
│   └── components/       # 组件模板
├── static/               # 静态资源
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript文件
│   ├── images/          # 图片文件
│   └── music/           # 音乐文件
├── config.py            # 配置文件
├── init_db.py          # 数据库初始化
├── run_dev.py          # 开发服务器
└── requirements.txt    # 依赖列表
```



## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🌐 在线演示

- **访问地址**: [https://www.rlj.net.cn](https://www.rlj.net.cn)
- **功能展示**: 体验完整的博客系统功能

## 📞 联系方式

如有问题或建议，欢迎在 [在线网站](https://www.rlj.net.cn) 留言反馈

---



