import os
import logging
from datetime import timedelta


class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 时区配置
    TIMEZONE = 'Asia/Shanghai'
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB
    
    # 评论功能配置
    COMMENT_RATE_LIMIT = 10  # 每小时评论数限制
    COMMENT_MAX_LENGTH = 1000  # 评论最大长度
    COMMENT_AUTO_APPROVE = False  # 是否自动审核通过
    COMMENT_ENABLE_LOCATION = True  # 是否启用地理位置
    
    # 点赞功能配置
    LIKE_RATE_LIMIT = 100  # 每小时点赞数限制
    LIKE_SESSION_TRACKING = True  # 是否启用session跟踪
    
    # 访问统计配置
    STATS_ENABLE_VISITOR_LOG = True  # 是否记录访客日志
    STATS_SESSION_TIMEOUT = 30  # 访客session超时时间（分钟）
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:rootpassword_here@localhost/your_database_name'
    
    # 开发环境session配置
    SESSION_COOKIE_SECURE = False
    
    # 开发环境功能配置
    COMMENT_AUTO_APPROVE = True  # 开发环境自动审核通过
    COMMENT_RATE_LIMIT = 50  # 开发环境放宽限制
    LIKE_RATE_LIMIT = 200
    
    # 开发环境日志配置
    LOG_LEVEL = logging.DEBUG
    LOG_TO_STDOUT = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # 生产环境session配置
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 生产环境延长到2小时
    
    # 优化的数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 15,  # 连接池大小
        'pool_recycle': 300,  # 连接回收时间（5分钟）
        'pool_pre_ping': True,  # 连接前ping测试
        'max_overflow': 30,  # 最大溢出连接数
        'pool_timeout': 30,  # 获取连接超时时间
        'echo': False,  # 生产环境不输出SQL
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 60,
            'read_timeout': 30,
            'write_timeout': 30,
            'autocommit': True
        }
    }
    
    # 生产环境功能配置
    COMMENT_RATE_LIMIT = 5  # 生产环境严格限制
    COMMENT_AUTO_APPROVE = False  # 需要审核
    LIKE_RATE_LIMIT = 50
    STATS_ENABLE_VISITOR_LOG = True
    
    # 压缩配置
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript', 'image/svg+xml'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # 生产环境日志配置
    LOG_LEVEL = logging.WARNING
    LOG_TO_STDOUT = False
    LOG_TO_FILE = True
    
    @staticmethod
    def init_app(app):
        """生产环境初始化和安全检查"""
        Config.init_app(app)
        
        # 安全检查
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
        
        # 数据库配置检查
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_uri or 'your_password_here' in db_uri:
            raise ValueError("生产环境必须正确设置 DATABASE_URL 环境变量")
        
        # 配置日志
        ProductionConfig.setup_logging(app)
    
    @staticmethod
    def setup_logging(app):
        """配置生产环境日志"""
        from logging.handlers import RotatingFileHandler
        
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 应用日志
        if app.config.get('LOG_TO_FILE'):
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'record_log.log'),
                maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024),
                backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5),
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s: %(message)s'
            ))
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(app.config.get('LOG_LEVEL', logging.WARNING))
        
        # 错误日志
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024),
            backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(pathname)s:%(lineno)d: %(message)s'
        ))
        app.logger.addHandler(error_handler)


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False
    COMMENT_AUTO_APPROVE = True
    STATS_ENABLE_VISITOR_LOG = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 