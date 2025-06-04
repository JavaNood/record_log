# Flask应用初始化文件
import pymysql
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

# 初始化SQLAlchemy
db = SQLAlchemy()

# 告诉PyMySQL使用pymysql作为MySQLdb
pymysql.install_as_MySQLdb()


def create_app(config_name='default'):
    """Flask应用工厂函数"""
    # 获取项目根目录
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    
    # 加载配置
    config_class = config[config_name]
    app.config.from_object(config_class)
    
    # 安全检查：调用配置的安全验证
    config_class.init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    
    # 导入模型（避免循环导入）
    from . import models
    
    # 注册蓝图
    from .frontend import frontend as frontend_bp
    app.register_blueprint(frontend_bp)
    
    from .admin import admin as admin_bp
    app.register_blueprint(admin_bp)
    
    return app 