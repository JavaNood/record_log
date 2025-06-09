import os
import logging
from datetime import timedelta


class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
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
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5
    
    @staticmethod
    def init_app(app):
        """初始化应用配置，进行安全检查"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:200035@localhost/myblog_dev'
    
    # 开发环境session配置
    SESSION_COOKIE_SECURE = False  # 开发环境允许HTTP
    # 开发环境日志配置
    LOG_LEVEL = logging.DEBUG
    LOG_TO_STDOUT = True  # 开发环境输出到控制台


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    
    # 生产环境session配置
    SESSION_COOKIE_SECURE = True  # 生产环境仅HTTPS
    
    # 性能优化配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 60,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # 压缩配置
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'application/xml+rss', 'application/atom+xml',
        'text/javascript', 'image/svg+xml'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # 生产环境日志配置
    LOG_LEVEL = logging.WARNING
    LOG_TO_STDOUT = False  # 生产环境不输出到控制台
    LOG_TO_FILE = True     # 输出到文件
    
    @staticmethod
    def init_app(app):
        """生产环境安全检查和日志配置"""
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
        
        # 配置日志
        ProductionConfig.setup_logging(app)
    
    @staticmethod
    def setup_logging(app):
        """配置生产环境日志"""
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置应用日志
        if app.config.get('LOG_TO_FILE'):
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'record_log.log'),
                maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024),
                backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5),
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
            ))
            app.logger.addHandler(file_handler)
        
        # 设置日志级别
        app.logger.setLevel(app.config.get('LOG_LEVEL', logging.WARNING))
        
        # 配置访问日志
        access_handler = RotatingFileHandler(
            os.path.join(log_dir, 'access.log'),
            maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024),
            backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        access_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(remote_addr)s %(method)s %(url)s %(status)s'
        ))
        
        # 配置错误日志
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024),
            backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(pathname)s:%(lineno)d: %(message)s'
        ))
        app.logger.addHandler(error_handler)


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