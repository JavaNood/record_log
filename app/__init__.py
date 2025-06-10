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
        # 缓存控制头
        if 'Cache-Control' not in response.headers:
            if request.endpoint and request.endpoint.startswith('static'):
                # 静态文件缓存30天
                response.headers['Cache-Control'] = 'public, max-age=2592000'
            else:
                # 动态内容不缓存
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
        
        # 内容类型选项头（防止MIME嗅探）
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # 其他推荐的安全头
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # 对于blob URL和图片响应，设置适当的缓存
        if response.content_type and response.content_type.startswith('image/'):
            response.headers['Cache-Control'] = 'public, max-age=3600'  # 图片缓存1小时
        
        return response
    
    # 导入模型（避免循环导入）
    from . import models
    
    # 添加访问统计中间件
    @app.before_request
    def track_visitor():
        """记录访客访问信息"""
        # 只记录GET请求且非静态文件和管理页面的访问
        if (request.method == 'GET' and 
            request.endpoint and 
            not request.endpoint.startswith('static') and
            not request.endpoint.startswith('admin')):
            
            try:
                from .models import SiteVisit
                from flask import session
                
                # 获取访客信息
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                if ip_address and ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()
                
                # 获取或生成session ID
                if 'visitor_session' not in session:
                    import uuid
                    session['visitor_session'] = str(uuid.uuid4())
                    session.permanent = True
                
                session_id = session['visitor_session']
                user_agent = request.headers.get('User-Agent', '')[:500]  # 限制长度
                referer = request.headers.get('Referer', '')[:255]  # 限制长度
                page_url = request.url[:255]  # 限制长度
                
                # 检查是否是重复访问（同一session在5分钟内访问同一页面不重复记录）
                from datetime import datetime, timedelta
                from .utils import get_local_now
                recent_visit = SiteVisit.query.filter(
                    SiteVisit.session_id == session_id,
                    SiteVisit.page_url == page_url,
                    SiteVisit.visit_time >= get_local_now() - timedelta(minutes=5)
                ).first()
                
                if not recent_visit:
                    # 记录新的访问
                    visit = SiteVisit(
                        ip_address=ip_address,
                        session_id=session_id,
                        user_agent=user_agent,
                        referer=referer,
                        page_url=page_url
                    )
                    db.session.add(visit)
                    db.session.commit()
                    
            except Exception as e:
                # 访问统计失败不应该影响正常功能
                print(f"访问统计记录失败: {e}")
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