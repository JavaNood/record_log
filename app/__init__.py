# Flask应用初始化文件
import pymysql
import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import config

# 初始化扩展
db = SQLAlchemy()

# 告诉PyMySQL使用pymysql作为MySQLdb
pymysql.install_as_MySQLdb()

# 性能优化扩展
try:
    from flask_compress import Compress
    compress = Compress()
except ImportError:
    compress = None


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
    
    # 初始化性能优化扩展
    if compress:
        compress.init_app(app)
    
    # 添加时间格式化过滤器
    from .utils import format_datetime, format_relative_time
    
    @app.template_filter('datetime')
    def datetime_filter(dt, format_str='%Y-%m-%d %H:%M:%S'):
        return format_datetime(dt, format_str)
    
    @app.template_filter('relative_time')
    def relative_time_filter(dt):
        return format_relative_time(dt)
    
    # 添加安全头中间件
    @app.after_request
    def add_security_headers(response):
        """为所有响应添加安全头"""
        if 'Cache-Control' not in response.headers:
            if request.endpoint and request.endpoint.startswith('static'):
                response.headers['Cache-Control'] = 'public, max-age=2592000'
            else:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        if response.content_type and response.content_type.startswith('image/'):
            response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
    
    # 导入模型（避免循环导入）
    from . import models
    
    # 添加访问统计中间件
    @app.before_request
    def track_visitor():
        """记录访客访问信息"""
        if (request.method == 'GET' and 
            request.endpoint and 
            not request.endpoint.startswith(('static', 'admin')) and
            app.config.get('STATS_ENABLE_VISITOR_LOG', True)):
            
            try:
                from .models import SiteVisit
                from flask import session
                from datetime import timedelta
                from .utils import get_local_now
                
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                if ip_address and ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()
                
                if 'visitor_session' not in session:
                    import uuid
                    session['visitor_session'] = str(uuid.uuid4())
                    session.permanent = True
                
                session_id = session['visitor_session']
                page_url = request.url[:255]
                
                # 检查重复访问（5分钟内不重复记录）
                timeout_minutes = app.config.get('STATS_SESSION_TIMEOUT', 5)
                recent_visit = SiteVisit.query.filter(
                    SiteVisit.session_id == session_id,
                    SiteVisit.page_url == page_url,
                    SiteVisit.visit_time >= get_local_now() - timedelta(minutes=timeout_minutes)
                ).first()
                
                if not recent_visit:
                    visit = SiteVisit(
                        ip_address=ip_address,
                        session_id=session_id,
                        user_agent=request.headers.get('User-Agent', '')[:500],
                        referer=request.headers.get('Referer', '')[:255],
                        page_url=page_url
                    )
                    db.session.add(visit)
                    db.session.commit()
                    
            except Exception:
                db.session.rollback()
    
    # 注册蓝图
    from .frontend import frontend as frontend_bp
    app.register_blueprint(frontend_bp)
    
    from .admin import admin as admin_bp
    app.register_blueprint(admin_bp)
    
    # 注册错误处理器
    from flask import render_template
    
    @app.errorhandler(404)
    def page_not_found(error):
        """404页面未找到错误处理"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """500服务器内部错误处理"""
        return render_template('errors/500.html'), 500
    
    return app 