# 后台管理模块 
from flask import Blueprint

admin = Blueprint('admin', __name__, url_prefix='/admin')

from . import views 