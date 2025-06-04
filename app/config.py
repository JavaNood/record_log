import os


class AppConfig:
    """应用内部配置"""
    
    # 分页配置
    POSTS_PER_PAGE = 10
    
    # 图片配置
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 文章权限类型
    PERMISSION_TYPES = {
        'public': '公开',
        'verify': '需要验证'
    }
    
    # 文章状态
    ARTICLE_STATUS = {
        'draft': '草稿',
        'published': '已发布'
    }
    
    @staticmethod
    def allowed_file(filename):
        """检查文件类型是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in AppConfig.ALLOWED_EXTENSIONS 