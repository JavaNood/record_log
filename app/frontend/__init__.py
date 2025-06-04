# 前端视图模块 

# 前端蓝图初始化文件
from flask import Blueprint

# 创建前端蓝图
frontend = Blueprint('frontend', __name__)

# 导入视图函数
from . import views 