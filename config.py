import os
from datetime import timedelta


class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') \
    or 'mysql+pymysql://myblog_user2:your_password_here@localhost/myblog'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)  # session有效期1小时
    SESSION_COOKIE_HTTPONLY = True  # 仅HTTP访问，提高安全性
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF保护
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Redis配置（可选）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    @staticmethod
    def init_app(app):
        """初始化应用配置，进行安全检查"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://myblog_user2:your_password_here@localhost/myblog_dev'
    
    # 开发环境session配置
    SESSION_COOKIE_SECURE = False  # 开发环境允许HTTP


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://myblog_user2:your_password_here@localhost/myblog'
    
    # 生产环境session配置
    SESSION_COOKIE_SECURE = True  # 生产环境仅HTTPS
    
    @staticmethod
    def init_app(app):
        """生产环境安全检查"""
        Config.init_app(app)
        
        # 安全检查：确保生产环境必须设置SECRET_KEY
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError(
                "生产环境必须设置 SECRET_KEY 环境变量！"
                "请设置: export SECRET_KEY='your-secure-secret-key'"
            )
        
        # 安全检查：数据库URI不能包含默认密码
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if 'your_password_here' in db_uri:
            raise ValueError(
                "生产环境必须设置 DATABASE_URL 环境变量，不能使用默认密码！"
                "请设置: export DATABASE_URL='mysql+pymysql://user:password@host/db'"
            )


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 