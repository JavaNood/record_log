#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from sqlalchemy.orm import joinedload
from . import admin
from .forms import LoginForm, ArticleEditForm, PasswordChangeForm
from ..auth import (
    authenticate_admin, admin_logout, login_required, admin_required,
    get_current_admin, admin_login, get_session_info, change_admin_password
)
from ..models import Article, Tag, Config, Music
from .. import db
from ..utils import get_local_now


def _parse_datetime_string(datetime_str):
    """解析时间字符串并转换为本地时间"""
    if not datetime_str or not datetime_str.strip():
        return get_local_now()
    
    try:
        from datetime import datetime
        local_datetime = datetime.strptime(datetime_str.strip(), '%Y-%m-%d %H:%M:%S')
        return local_datetime
    except ValueError:
        return get_local_now()


# 允许的图片格式
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

# 允许的音乐格式
ALLOWED_MUSIC_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}

def allowed_image_file(filename):
    """检查是否是允许的图片格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_music_file(filename):
    """检查是否是允许的音乐格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_MUSIC_EXTENSIONS


@admin.route('/')
def index():
    """管理员后台首页重定向"""
    return redirect(url_for('admin.login'))


@admin.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    """图片上传API"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '没有选择图片文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择图片文件'}), 400
        
        if not allowed_image_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的图片格式，请上传 PNG、JPG、JPEG、GIF、WebP 或 BMP 格式的图片'}), 400
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加UUID前缀避免文件名冲突
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 确保上传目录存在
        upload_dir = os.path.join('static', 'images', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # 返回相对URL路径
        image_url = f"/static/images/uploads/{unique_filename}"
        
        return jsonify({
            'success': True,
            'message': '图片上传成功',
            'image_url': image_url,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'图片上传失败: {str(e)}'}), 500


@admin.route('/upload-music', methods=['POST'])
@login_required
def upload_music():
    """音乐文件上传API"""
    try:
        if 'music' not in request.files:
            return jsonify({'success': False, 'message': '没有选择音乐文件'}), 400
        
        file = request.files['music']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择音乐文件'}), 400
        
        if not allowed_music_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的音乐格式，请上传 MP3、WAV、OGG、M4A、AAC 或 FLAC 格式的音乐文件'}), 400
        
        # 检查文件大小（20MB限制）
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置到文件开头
        
        max_size = 20 * 1024 * 1024  # 20MB
        if file_size > max_size:
            return jsonify({'success': False, 'message': f'文件大小超过限制（最大20MB），当前文件大小：{file_size / (1024 * 1024):.1f}MB'}), 400
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加UUID前缀避免文件名冲突
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 确保音乐上传目录存在
        upload_dir = os.path.join('static', 'music')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # 获取显示名称（从表单或使用原始文件名）
        display_name = request.form.get('display_name', '').strip()
        if not display_name:
            # 如果没有提供显示名称，使用原始文件名（去掉扩展名）
            display_name = os.path.splitext(file.filename)[0]
        
        # 获取MIME类型
        mime_type = file.content_type or 'audio/mpeg'
        
        # 创建Music数据库记录
        music = Music(
            filename=filename,
            display_name=display_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            duration=0  # 暂时设为0，后续可以添加音频时长检测
        )
        
        db.session.add(music)
        db.session.commit()
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '音乐文件上传成功',
            'music': music.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'音乐上传失败: {str(e)}'}), 500


@admin.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录页面"""
    # 如果已经登录，重定向到后台首页
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        remember_me = form.remember_me.data
        
        # 使用新的认证系统验证
        if authenticate_admin(username, password):
            # 使用新的登录函数
            admin_login(username, remember_me)
            
            flash(f'欢迎回来，{username}！登录成功', 'success')
            
            # 获取重定向目标（来自装饰器保存的URL或用户指定的next参数）
            next_page = session.pop('next_url', None) or request.args.get('next')
            if next_page and next_page.startswith('/admin'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        else:
            # 登录失败
            flash('用户名或密码错误，请检查后重试', 'danger')
    
    return render_template('admin/login.html', form=form)


@admin.route('/dashboard')
@login_required
def dashboard():
    """管理员后台首页"""
    current_admin = get_current_admin()
    session_info = get_session_info()
    return render_template('admin/dashboard.html', 
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/articles')
@login_required
def articles():
    """文章列表管理页面"""
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'updated_at')  # 默认按更新时间排序
    order = request.args.get('order', 'desc')  # 默认降序
    search_query = request.args.get('search', '').strip()  # 搜索关键词
    per_page = 10  # 每页显示10篇文章
    
    # 构建查询
    query = Article.query.options(joinedload(Article.tags))
    
    # 应用搜索筛选
    if search_query:
        query = query.filter(Article.title.contains(search_query))
    
    # 应用排序
    if sort_by == 'likes_count':
        if order == 'asc':
            query = query.order_by(Article.is_top.desc(), Article.likes_count.asc())
        else:
            query = query.order_by(Article.is_top.desc(), Article.likes_count.desc())
    elif sort_by == 'view_count':
        if order == 'asc':
            query = query.order_by(Article.is_top.desc(), Article.view_count.asc())
        else:
            query = query.order_by(Article.is_top.desc(), Article.view_count.desc())
    elif sort_by == 'created_at':
        if order == 'asc':
            query = query.order_by(Article.is_top.desc(), Article.created_at.asc())
        else:
            query = query.order_by(Article.is_top.desc(), Article.created_at.desc())
    else:  # updated_at (默认)
        if order == 'asc':
            query = query.order_by(Article.is_top.desc(), Article.updated_at.asc())
        else:
            query = query.order_by(Article.is_top.desc(), Article.updated_at.desc())
    
    # 分页
    articles = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/articles.html',
                         articles=articles,
                         current_admin=current_admin,
                         session_info=session_info,
                         sort_by=sort_by,
                         order=order,
                         search_query=search_query)


@admin.route('/article/new', methods=['GET', 'POST'])
@login_required
def new_article():
    """新建文章页面"""
    form = ArticleEditForm()
    
    # 设置标签选择项
    all_tags = Tag.query.order_by(Tag.name).all()
    form.tags.choices = [(tag.id, tag.name) for tag in all_tags]
    
    if form.validate_on_submit():
        # 验证权限相关字段
        if form.permission.data == 'verify':
            if not form.verify_question.data:
                flash('权限为需要验证时，验证提示词为必填项', 'danger')
                return render_template('admin/article_edit.html',
                                     form=form,
                                     article=None,
                                     is_new=True,
                                     all_tags=all_tags,
                                     current_admin=get_current_admin(),
                                     session_info=get_session_info())
        
        # 处理表单提交
        try:
            from ..utils import local_to_utc
            article = Article(
                title=form.title.data.strip(),
                content=form.content.data,
                summary=form.summary.data.strip() if form.summary.data else None,
                permission=form.permission.data,
                verify_question=form.verify_question.data.strip() if form.verify_question.data else None,
                verify_answer=form.verify_answer.data.strip() if form.verify_answer.data else None,
                status=form.status.data,
                is_top=form.is_top.data,
                allow_comments=form.allow_comments.data,
                publish_location=form.publish_location.data.strip() if form.publish_location.data else None,
                view_count=form.view_count.data or 0,
                likes_count=form.likes_count.data or 0,
                created_at=_parse_datetime_string(form.created_at.data) if form.created_at.data and form.created_at.data.strip() else get_local_now(),
                updated_at=_parse_datetime_string(form.updated_at.data) if form.updated_at.data and form.updated_at.data.strip() else get_local_now()
            )
            
            # 处理标签关联
            selected_tag_ids = form.tags.data
            if selected_tag_ids:
                selected_tags = Tag.query.filter(Tag.id.in_(selected_tag_ids)).all()
                article.tags = selected_tags
            
            db.session.add(article)
            db.session.commit()
            
            status_text = '已发布' if article.status == 'published' else '草稿'
            flash(f'文章《{article.title}》已成功创建并保存为{status_text}', 'success')
            
            return redirect(url_for('admin.articles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'创建文章失败: {str(e)}', 'danger')
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/article_edit.html',
                         form=form,
                         article=None,  # 新建文章时没有现有文章
                         is_new=True,
                         all_tags=all_tags,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/article/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    """文章编辑页面"""
    article = Article.query.get_or_404(article_id)
    form = ArticleEditForm()
    
    # 设置标签选择项
    all_tags = Tag.query.order_by(Tag.name).all()
    form.tags.choices = [(tag.id, tag.name) for tag in all_tags]
    
    if form.validate_on_submit():
        # 验证权限相关字段
        if form.permission.data == 'verify':
            if not form.verify_question.data:
                flash('权限为需要验证时，验证提示词为必填项', 'danger')
                return render_template('admin/article_edit.html',
                                     form=form,
                                     article=article,
                                     is_new=False,
                                     all_tags=all_tags,
                                     current_admin=get_current_admin(),
                                     session_info=get_session_info())
        
        # 处理表单提交
        try:
            article.title = form.title.data.strip()
            article.content = form.content.data
            article.summary = form.summary.data.strip() if form.summary.data else None
            article.permission = form.permission.data
            article.verify_question = form.verify_question.data.strip() if form.verify_question.data else None
            article.verify_answer = form.verify_answer.data.strip() if form.verify_answer.data else None
            article.status = form.status.data
            article.is_top = form.is_top.data
            article.allow_comments = form.allow_comments.data
            article.publish_location = form.publish_location.data.strip() if form.publish_location.data else None
            article.view_count = form.view_count.data or 0
            article.likes_count = form.likes_count.data or 0
              # 处理时间字段，转换为数据库存储格式
            from datetime import datetime
            
            # 处理创建时间
            if form.created_at.data and form.created_at.data.strip():
                try:
                    local_datetime = datetime.strptime(form.created_at.data.strip(), '%Y-%m-%d %H:%M:%S')
                    article.created_at = local_datetime
                except ValueError:
                    pass  # 格式错误时保持原值
            
            # 处理更新时间 - 编辑文章时始终更新，除非用户手动指定了时间
            # 检查用户是否手动修改了时间字段
            original_time_str = article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else ''
            user_time_str = form.updated_at.data.strip() if form.updated_at.data else ''
            
            if user_time_str and user_time_str != original_time_str:
                # 用户手动修改了时间，使用用户指定的时间
                try:
                    local_datetime = datetime.strptime(user_time_str, '%Y-%m-%d %H:%M:%S')
                    article.updated_at = local_datetime
                except ValueError:
                    article.updated_at = get_local_now()  # 格式错误时使用当前时间
            else:
                # 用户没有修改时间，使用当前时间（编辑文章时更新）
                article.updated_at = get_local_now()
            # 处理标签关联
            selected_tag_ids = form.tags.data
            if selected_tag_ids:
                selected_tags = Tag.query.filter(Tag.id.in_(selected_tag_ids)).all()
                article.tags = selected_tags
            else:
                # 如果没有选择标签，清除所有标签关联
                article.tags = []
            
            db.session.commit()
            
            status_text = '已发布' if article.status == 'published' else '草稿'
            flash(f'文章《{article.title}》已成功保存为{status_text}', 'success')
            
            return redirect(url_for('admin.articles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'保存文章失败: {str(e)}', 'danger')
    
    # GET请求，显示编辑表单
    if request.method == 'GET':
        # 填充表单数据
        form.title.data = article.title
        form.content.data = article.content
        form.summary.data = article.summary
        form.permission.data = article.permission
        form.verify_question.data = article.verify_question
        form.verify_answer.data = article.verify_answer
        form.status.data = article.status
        form.is_top.data = article.is_top
        form.allow_comments.data = article.allow_comments
        form.publish_location.data = article.publish_location
        form.view_count.data = article.view_count
        form.likes_count.data = article.likes_count
        # 格式化时间为本地时间字符串
        if article.created_at:
            form.created_at.data = article.created_at.strftime('%Y-%m-%d %H:%M:%S')
        if article.updated_at:
            form.updated_at.data = article.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        # 设置已选择的标签
        form.tags.data = [tag.id for tag in article.tags]
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/article_edit.html',
                         form=form,
                         article=article,
                         is_new=False,
                         all_tags=all_tags,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/article/delete/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    """删除单篇文章"""
    try:
        article = Article.query.get_or_404(article_id)
        title = article.title
        
        # 删除文章
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'文章《{title}》已成功删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除文章失败: {str(e)}'
        }), 500


@admin.route('/articles/batch-delete', methods=['POST'])
@login_required
def batch_delete_articles():
    """批量删除文章"""
    try:
        data = request.get_json()
        article_ids = data.get('article_ids', [])
        
        if not article_ids:
            return jsonify({
                'success': False,
                'message': '请选择要删除的文章'
            }), 400
        
        # 查找要删除的文章
        articles = Article.query.filter(Article.id.in_(article_ids)).all()
        if not articles:
            return jsonify({
                'success': False,
                'message': '未找到要删除的文章'
            }), 404
        
        deleted_count = len(articles)
        titles = [article.title for article in articles[:3]]  # 最多显示3个标题
        
        # 删除文章
        for article in articles:
            db.session.delete(article)
        
        db.session.commit()
        
        # 构建成功消息
        if deleted_count <= 3:
            message = f'成功删除文章：{", ".join(titles)}'
        else:
            message = f'成功删除文章：{", ".join(titles)} 等 {deleted_count} 篇'
        
        return jsonify({
            'success': True,
            'message': message,
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量删除失败: {str(e)}'
        }), 500


@admin.route('/article/toggle-status/<int:article_id>', methods=['POST'])
@login_required
def toggle_article_status(article_id):
    """切换单篇文章状态（草稿/发布）"""
    try:
        article = Article.query.get_or_404(article_id)
        
        # 切换状态
        if article.status == 'published':
            article.status = 'draft'
            new_status_text = '草稿'
        else:
            article.status = 'published'
            new_status_text = '已发布'
        
        article.updated_at = get_local_now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'文章《{article.title}》已设为{new_status_text}',
            'new_status': article.status,
            'new_status_text': new_status_text
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'状态切换失败: {str(e)}'
        }), 500


@admin.route('/articles/batch-status', methods=['POST'])
@login_required
def batch_change_status():
    """批量修改文章状态"""
    try:
        data = request.get_json()
        article_ids = data.get('article_ids', [])
        target_status = data.get('target_status')  # 'published' 或 'draft'
        
        if not article_ids:
            return jsonify({
                'success': False,
                'message': '请选择要修改的文章'
            }), 400
        
        if target_status not in ['published', 'draft']:
            return jsonify({
                'success': False,
                'message': '状态参数错误'
            }), 400
        
        # 查找要修改的文章
        articles = Article.query.filter(Article.id.in_(article_ids)).all()
        if not articles:
            return jsonify({
                'success': False,
                'message': '未找到要修改的文章'
            }), 404
        
        status_text = '已发布' if target_status == 'published' else '草稿'
        updated_count = 0
        
        # 修改文章状态
        for article in articles:
            if article.status != target_status:
                article.status = target_status
                article.updated_at = get_local_now()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功将 {updated_count} 篇文章设为{status_text}',
            'updated_count': updated_count,
            'target_status': target_status,
            'status_text': status_text
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量状态修改失败: {str(e)}'
        }), 500


@admin.route('/logout')
def logout():
    """管理员登出"""
    admin_logout()
    flash('您已成功登出，感谢使用！', 'success')
    return redirect(url_for('admin.login'))


@admin.route('/session-info')
@login_required
def session_info():
    """获取会话信息API"""
    info = get_session_info()
    return jsonify(info)


@admin.route('/statistics')
@login_required
def statistics():
    """网站访问统计页面"""
    from ..models import SiteVisit, Article
    from sqlalchemy import func, distinct
    from datetime import datetime, timedelta
    
    # 获取访问统计
    site_stats = SiteVisit.get_stats()
    
    # 获取文章统计
    total_articles = Article.query.filter_by(status='published').count()
    total_drafts = Article.query.filter_by(status='draft').count()
    total_views = db.session.query(func.sum(Article.view_count)).filter_by(status='published').scalar() or 0
    
    # 获取最近访问记录（最近50条）
    recent_visits = SiteVisit.query.order_by(SiteVisit.visit_time.desc()).limit(50).all()
    
    # 获取热门页面统计
    from sqlalchemy import text
    popular_pages = db.session.execute(text("""
        SELECT page_url, COUNT(*) as visit_count, COUNT(DISTINCT ip_address) as unique_visitors
        FROM site_visits 
        WHERE visit_time >= :week_ago
        GROUP BY page_url 
        ORDER BY visit_count DESC 
        LIMIT 10
    """), {'week_ago': datetime.now() - timedelta(days=7)}).fetchall()
    
    # 获取每日访问统计（最近7天）
    daily_stats = []
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        daily_visits = SiteVisit.query.filter(
            SiteVisit.visit_time >= start,
            SiteVisit.visit_time < end
        ).count()
        
        daily_unique = db.session.query(func.count(distinct(SiteVisit.ip_address))).filter(
            SiteVisit.visit_time >= start,
            SiteVisit.visit_time < end
        ).scalar() or 0
        
        daily_stats.append({
            'date': start.strftime('%m-%d'),
            'visits': daily_visits,
            'unique': daily_unique
        })
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/statistics.html',
                         site_stats=site_stats,
                         total_articles=total_articles,
                         total_drafts=total_drafts,
                         total_views=total_views,
                         recent_visits=recent_visits,
                         popular_pages=popular_pages,
                         daily_stats=daily_stats,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/profile')
@admin_required
def profile():
    """管理员个人信息页面"""
    current_admin = get_current_admin()
    session_info = get_session_info()
    return render_template('admin/profile.html', 
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/settings')
@admin_required
def settings():
    """管理员系统设置页面"""
    current_admin = get_current_admin()
    return render_template('admin/settings.html', current_admin=current_admin)


@admin.route('/tags')
@login_required
def tags():
    """标签管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 15  # 每页显示15个标签
    
    # 获取所有标签，按创建时间降序
    tags = Tag.query.order_by(Tag.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/tags.html',
                         tags=tags,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/tag/create', methods=['POST'])
@login_required
def create_tag():
    """创建新标签"""
    try:
        name = request.form.get('name', '').strip()
        color = request.form.get('color', '#007bff').strip()
        
        if not name:
            return jsonify({'success': False, 'message': '标签名称不能为空'})
        
        # 检查标签是否已存在
        existing_tag = Tag.query.filter_by(name=name).first()
        if existing_tag:
            return jsonify({'success': False, 'message': '标签已存在'})
        
        # 创建新标签
        tag = Tag(name=name, color=color)
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'标签《{name}》创建成功',
            'tag': tag.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建标签失败: {str(e)}'})


@admin.route('/tag/edit/<int:tag_id>', methods=['POST'])
@login_required
def edit_tag(tag_id):
    """编辑标签"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        
        name = request.form.get('name', '').strip()
        color = request.form.get('color', '#007bff').strip()
        
        if not name:
            return jsonify({'success': False, 'message': '标签名称不能为空'})
        
        # 检查标签名是否与其他标签冲突
        existing_tag = Tag.query.filter(Tag.name == name, Tag.id != tag_id).first()
        if existing_tag:
            return jsonify({'success': False, 'message': '标签名称已存在'})
        
        # 更新标签
        tag.name = name
        tag.color = color
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'标签《{name}》更新成功',
            'tag': tag.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新标签失败: {str(e)}'})


@admin.route('/tag/delete/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(tag_id):
    """删除标签"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        
        # 检查标签是否被文章使用
        if tag.articles.count() > 0:
            return jsonify({
                'success': False, 
                'message': f'标签《{tag.name}》正在被 {tag.articles.count()} 篇文章使用，无法删除'
            })
        
        tag_name = tag.name
        db.session.delete(tag)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'标签《{tag_name}》已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除标签失败: {str(e)}'})


@admin.route('/welcome', methods=['GET', 'POST'])
@login_required
def welcome_edit():
    """欢迎语编辑页面"""
    if request.method == 'POST':
        try:
            welcome_title = request.form.get('welcome_title', '').strip()
            welcome_subtitle = request.form.get('welcome_subtitle', '').strip()
            
            if not welcome_title:
                flash('欢迎语标题不能为空', 'danger')
                return redirect(url_for('admin.welcome_edit'))
            
            # 保存欢迎语标题和副标题
            Config.set_value('homepage_welcome_title', welcome_title)
            Config.set_value('homepage_welcome_subtitle', welcome_subtitle)
            
            flash('欢迎语更新成功！', 'success')
            return redirect(url_for('admin.welcome_edit'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新欢迎语失败: {str(e)}', 'danger')
    
    # GET请求，显示编辑表单
    welcome_title = Config.get_value('homepage_welcome_title', '欢迎来到我的个人博客')
    welcome_subtitle = Config.get_value('homepage_welcome_subtitle', '记录生活，分享想法，探索世界')
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/welcome_edit.html',
                         welcome_title=welcome_title,
                         welcome_subtitle=welcome_subtitle,
                         current_admin=current_admin,
                         session_info=session_info)


def process_background_image(file_path, blur_level=10, fit_mode='cover'):
    """处理背景图片，添加虚化效果"""
    try:
        from PIL import Image, ImageFilter
        
        # 打开图片
        with Image.open(file_path) as img:
            # 转换为RGB模式（如果是RGBA则保留透明度）
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # 获取原始尺寸
            original_width, original_height = img.size
            
            # 根据适配方式处理图片尺寸
            if fit_mode == 'contain':
                # 完整显示模式：确保图片完全可见，可能有边距
                max_width = 1920
                max_height = 1080
                
                # 计算缩放比例，保持宽高比，使用较小的比例确保完整显示
                width_ratio = max_width / original_width
                height_ratio = max_height / original_height
                ratio = min(width_ratio, height_ratio)
                
                # 计算新尺寸
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                # 缩放图片
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
            elif fit_mode == '100% 100%':
                # 拉伸填满模式：强制拉伸到目标尺寸
                max_width = 1920
                max_height = 1080
                img_resized = img.resize((max_width, max_height), Image.Resampling.LANCZOS)
                
            else:  # cover 模式（默认）
                # 覆盖填满模式：填满容器，可能裁剪
                max_width = 1920
                max_height = 1080
                
                # 计算缩放比例，保持宽高比，使用较大的比例确保完全覆盖
                width_ratio = max_width / original_width
                height_ratio = max_height / original_height
                ratio = max(width_ratio, height_ratio)
                
                # 计算新尺寸
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                # 缩放图片
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 如果需要，居中裁剪到目标尺寸
                if new_width > max_width or new_height > max_height:
                    left = (new_width - max_width) // 2
                    top = (new_height - max_height) // 2
                    right = left + max_width
                    bottom = top + max_height
                    img_resized = img_resized.crop((left, top, right, bottom))
            
            # 应用虚化效果
            if blur_level > 0:
                img_resized = img_resized.filter(ImageFilter.GaussianBlur(radius=blur_level))
            
            # 保存处理后的图片
            img_resized.save(file_path, 'JPEG', quality=85, optimize=True)
            
            return True
            
    except Exception as e:
        print(f"图片处理失败: {str(e)}")
        return False


# 添加预设背景选项
PRESET_BACKGROUNDS = {
    'sky': {
        'name': '蓝天白云',
        'gradient': 'linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #a29bfe 100%)',
        'description': '清新的蓝天白云背景'
    },
    'ocean': {
        'name': '深海蓝调',
        'gradient': 'linear-gradient(135deg, #00b894 0%, #00cec9 50%, #6c5ce7 100%)',
        'description': '宁静的海洋蓝色背景'
    },
    'sunset': {
        'name': '黄昏夕阳',
        'gradient': 'linear-gradient(135deg, #fdcb6e 0%, #e17055 50%, #d63031 100%)',
        'description': '温暖的黄昏夕阳背景'
    },
    'forest': {
        'name': '翠绿森林',
        'gradient': 'linear-gradient(135deg, #00b894 0%, #55a3ff 30%, #1dd1a1 100%)',
        'description': '清新的森林绿色背景'
    },
    'night': {
        'name': '星空夜晚',
        'gradient': 'linear-gradient(135deg, #2d3436 0%, #636e72 50%, #74b9ff 100%)',
        'description': '神秘的星空夜色背景'
    },
    'spring': {
        'name': '春日暖阳',
        'gradient': 'linear-gradient(135deg, #a8e6cf 0%, #dcedc1 50%, #ffd3a5 100%)',
        'description': '温暖的春日阳光背景'
    },
    'reading': {
        'name': '阅读舒适',
        'gradient': 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 25%, #90caf9 50%, #e1f5fe 75%, #f0f8ff 100%)',
        'description': '适合阅读的淡蓝色背景，与文章详情页一致'
    },
    # 新增动态背景选项
    'rain_animated': {
        'name': '🌧️ 下雨动态',
        'gradient': 'linear-gradient(to bottom, #0c1445 0%, #1f2951 25%, #3a4d6b 50%, #5a6b7f 75%, #758a9b 100%)',
        'description': '动态下雨效果，包含雨滴和闪电',
        'animation': 'rain'
    },
    'ocean_animated': {
        'name': '🌊 海洋动态',
        'gradient': 'linear-gradient(to bottom, #87CEEB 0%, #4682B4 30%, #1e3c72 60%, #2a5298 100%)',
        'description': '动态海洋效果，包含波浪和气泡',
        'animation': 'ocean'
    },
    'snow_animated': {
        'name': '❄️ 下雪动态',
        'gradient': 'linear-gradient(to bottom, #e6f3ff 0%, #b3d9ff 50%, #cce6ff 100%)',
        'description': '动态下雪效果，飘落的雪花',
        'animation': 'snow'
    }
}

# 时间段对应的背景
TIME_BASED_BACKGROUNDS = {
    'morning': 'spring',    # 6-11点：春日暖阳
    'noon': 'reading',      # 11-15点：阅读舒适（原蓝天白云）
    'afternoon': 'ocean',   # 15-18点：深海蓝调
    'evening': 'sunset',    # 18-22点：黄昏夕阳
    'night': 'night'        # 22-6点：星空夜晚
}

@admin.route('/background', methods=['GET', 'POST'])
@login_required
def background_edit():
    """背景图片设置页面"""
    if request.method == 'POST':
        try:
            # 处理预设背景选择
            preset_bg = request.form.get('preset_background')
            if preset_bg and preset_bg in PRESET_BACKGROUNDS:
                # 使用预设背景
                Config.set_value('background_type', 'preset')
                Config.set_value('background_preset', preset_bg)
                Config.set_value('background_image', '')  # 清除自定义图片
                
                # 获取其他设置
                time_based = request.form.get('time_based_background') == 'on'
                Config.set_value('background_time_based', str(time_based))
                
                flash('预设背景设置成功！', 'success')
                return redirect(url_for('admin.background_edit'))
            
            # 处理时间变化开关（独立更新）
            if 'update_time_setting' in request.form:
                time_based = request.form.get('time_based_background') == 'on'
                Config.set_value('background_time_based', str(time_based))
                flash('时间变化设置已更新！', 'success')
                return redirect(url_for('admin.background_edit'))
            
            # 处理图片上传
            if 'background_image' in request.files:
                file = request.files['background_image']
                if file and file.filename != '':
                    if not allowed_image_file(file.filename):
                        flash('不支持的图片格式，请上传 PNG、JPG、JPEG、GIF、WebP 或 BMP 格式的图片', 'danger')
                        return redirect(url_for('admin.background_edit'))
                    
                    # 生成安全的文件名
                    filename = secure_filename(file.filename)
                    unique_filename = f"bg_{uuid.uuid4().hex}_{filename}"
                    
                    # 确保背景图片目录存在
                    background_dir = os.path.join('static', 'images', 'backgrounds')
                    os.makedirs(background_dir, exist_ok=True)
                    
                    # 保存原始文件
                    file_path = os.path.join(background_dir, unique_filename)
                    file.save(file_path)
                    
                    # 获取虚化级别和适配方式
                    blur_level = int(request.form.get('blur_level', 10))
                    fit_mode = request.form.get('bg_fit_mode', 'cover')
                    
                    # 处理图片（缩放和虚化）
                    if process_background_image(file_path, blur_level, fit_mode):
                        # 删除旧的背景图片
                        old_bg = Config.get_value('background_image', '')
                        if old_bg and old_bg.startswith('/static/images/backgrounds/'):
                            old_path = old_bg[1:]  # 移除开头的/
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                except:
                                    pass
                        
                        # 保存新的背景图片配置
                        bg_url = f"/static/images/backgrounds/{unique_filename}"
                        Config.set_value('background_type', 'custom')
                        Config.set_value('background_image', bg_url)
                        Config.set_value('background_blur_level', str(blur_level))
                        Config.set_value('background_fit_mode', fit_mode)
                        
                        flash('背景图片上传成功！', 'success')
                    else:
                        # 处理失败，删除文件
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        flash('图片处理失败，请重试', 'danger')
                    
                    return redirect(url_for('admin.background_edit'))
            
            # 处理设置调整（不上传新图片）
            blur_level = int(request.form.get('blur_level', 10))
            fit_mode = request.form.get('bg_fit_mode', 'cover')
            current_bg = Config.get_value('background_image', '')
            
            if current_bg and current_bg.startswith('/static/images/backgrounds/'):
                file_path = current_bg[1:]  # 移除开头的/
                if os.path.exists(file_path):
                    # 重新处理现有图片
                    if process_background_image(file_path, blur_level, fit_mode):
                        Config.set_value('background_blur_level', str(blur_level))
                        Config.set_value('background_fit_mode', fit_mode)
                        flash('背景设置已更新！', 'success')
                    else:
                        flash('设置调整失败', 'danger')
                else:
                    flash('背景图片文件不存在', 'danger')
            else:
                # 只保存设置
                Config.set_value('background_blur_level', str(blur_level))
                Config.set_value('background_fit_mode', fit_mode)
                flash('背景设置已保存', 'info')
            
            return redirect(url_for('admin.background_edit'))
            
        except Exception as e:
            flash(f'背景设置失败: {str(e)}', 'danger')
    
    # GET请求，显示设置页面
    background_type = Config.get_value('background_type', 'custom')
    current_bg = Config.get_value('background_image', '')
    current_preset = Config.get_value('background_preset', 'sky')
    blur_level = int(Config.get_value('background_blur_level', '10'))
    fit_mode = Config.get_value('background_fit_mode', 'cover')
    time_based = Config.get_value('background_time_based', 'False') == 'True'
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/background_edit.html',
                         current_background=current_bg,
                         background_type=background_type,
                         current_preset=current_preset,
                         blur_level=blur_level,
                         fit_mode=fit_mode,
                         time_based=time_based,
                         preset_backgrounds=PRESET_BACKGROUNDS,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/background/reset', methods=['POST'])
@login_required 
def reset_background():
    """重置背景为默认"""
    try:
        # 删除当前背景图片文件
        current_bg = Config.get_value('background_image', '')
        if current_bg and current_bg.startswith('/static/images/backgrounds/'):
            file_path = current_bg[1:]  # 移除开头的/
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        # 清除所有背景相关配置
        Config.set_value('background_type', 'custom')
        Config.set_value('background_image', '')
        Config.set_value('background_preset', 'sky')
        Config.set_value('background_blur_level', '10')
        Config.set_value('background_fit_mode', 'cover')
        Config.set_value('background_time_based', 'False')
        
        return jsonify({'success': True, 'message': '背景已重置为默认'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'重置失败: {str(e)}'})


# 注释掉公网部署时的密码帮助页面，避免暴露管理员重置方法
# @admin.route('/password-help')
# def password_help():
#     """密码找回帮助页面"""
#     return render_template('admin/password_help.html')


@admin.route('/comments')
@login_required
def comments():
    """评论管理页面"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')  # 状态筛选
    article_id = request.args.get('article', type=int)  # 文章筛选
    search_query = request.args.get('search', '').strip()  # 搜索
    per_page = 20  # 每页显示20条评论
    
    # 导入评论模型
    from ..models import Comment
    
    # 构建基础查询
    query = Comment.query.options(db.joinedload(Comment.article))
    
    # 应用状态筛选
    if status_filter != 'all':
        query = query.filter(Comment.status == status_filter)
    
    # 应用文章筛选
    if article_id:
        query = query.filter(Comment.article_id == article_id)
    
    # 应用搜索筛选
    if search_query:
        query = query.filter(
            db.or_(
                Comment.content.contains(search_query),
                Comment.nickname.contains(search_query)
            )
        )
    
    # 按创建时间倒序排列
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 获取统计信息
    stats = {
        'total': Comment.query.count(),
        'pending': Comment.query.filter_by(status='pending').count(),
        'approved': Comment.query.filter_by(status='approved').count(),
        'rejected': Comment.query.filter_by(status='rejected').count()
    }
    
    # 获取文章列表（用于筛选）
    articles_with_comments = db.session.query(Article.id, Article.title, db.func.count(Comment.id).label('comment_count'))\
        .outerjoin(Comment)\
        .group_by(Article.id, Article.title)\
        .having(db.func.count(Comment.id) > 0)\
        .order_by(Article.title)\
        .limit(50).all()
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/comments.html',
                         comments=comments,
                         stats=stats,
                         status_filter=status_filter,
                         article_id=article_id,
                         search_query=search_query,
                         articles_with_comments=articles_with_comments,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/comment/approve/<int:comment_id>', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """审核通过评论"""
    try:
        from ..models import Comment
        comment = Comment.query.get_or_404(comment_id)
        
        comment.status = 'approved'
        
        # 更新文章评论数（只计算已通过的评论）
        approved_count = Comment.query.filter_by(
            article_id=comment.article_id,
            status='approved'
        ).count()
        comment.article.comments_count = approved_count
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'评论已审核通过',
            'new_status': 'approved'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@admin.route('/comment/reject/<int:comment_id>', methods=['POST'])
@login_required
def reject_comment(comment_id):
    """拒绝评论"""
    try:
        from ..models import Comment
        comment = Comment.query.get_or_404(comment_id)
        
        old_status = comment.status
        comment.status = 'rejected'
        
        # 如果之前是已通过状态，需要更新文章评论数
        if old_status == 'approved':
            approved_count = Comment.query.filter_by(
                article_id=comment.article_id,
                status='approved'
            ).count()
            comment.article.comments_count = approved_count - 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'评论已拒绝',
            'new_status': 'rejected'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@admin.route('/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    try:
        from ..models import Comment
        comment = Comment.query.get_or_404(comment_id)
        
        # 如果是已通过的评论，需要更新文章评论数
        if comment.status == 'approved':
            comment.article.comments_count = max(0, comment.article.comments_count - 1)
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '评论已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})


@admin.route('/comment/reply', methods=['POST'])
@login_required
def admin_reply_comment():
    """管理员回复评论"""
    try:
        data = request.get_json()
        parent_id = data.get('parentId')
        content = data.get('content', '').strip()
        is_private = data.get('isPrivate', False)
        
        # 验证参数
        if not parent_id or not content:
            return jsonify({'success': False, 'message': '参数不完整'})
        
        if len(content) < 2:
            return jsonify({'success': False, 'message': '回复内容至少需要2个字符'})
        
        if len(content) > 1000:
            return jsonify({'success': False, 'message': '回复内容不能超过1000个字符'})
        
        # 获取父评论
        from ..models import Comment
        parent_comment = Comment.query.filter_by(
            id=parent_id,
            status='approved'  # 只能回复已审核通过的评论
        ).first()
        
        if not parent_comment:
            return jsonify({'success': False, 'message': '回复的评论不存在或未通过审核'})
        
        # 获取当前管理员信息
        current_admin = get_current_admin()
        admin_nickname = "作者"
        
        # 创建管理员回复
        admin_reply = Comment(
            content=content,
            nickname=admin_nickname,
            ip_address='127.0.0.1',  # 管理员回复使用本地IP
            location='管理员',
            is_private=is_private,
            article_id=parent_comment.article_id,
            parent_id=parent_id,
            status='approved'  # 管理员回复直接审核通过
        )
        
        db.session.add(admin_reply)
        
        # 更新文章评论数（管理员回复直接通过，计入评论数）
        parent_comment.article.comments_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '管理员回复发表成功！',
            'reply': {
                'id': admin_reply.id,
                'content': admin_reply.content,
                'display_name': admin_reply.display_name,
                'status': admin_reply.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'回复失败: {str(e)}'})


@admin.route('/comments/batch-action', methods=['POST'])
@login_required
def batch_comment_action():
    """批量操作评论"""
    try:
        data = request.get_json()
        comment_ids = data.get('comment_ids', [])
        action = data.get('action')  # 'approve', 'reject', 'delete'
        
        if not comment_ids or not action:
            return jsonify({'success': False, 'message': '参数错误'})
        
        from ..models import Comment
        comments = Comment.query.filter(Comment.id.in_(comment_ids)).all()
        
        if not comments:
            return jsonify({'success': False, 'message': '未找到要操作的评论'})
        
        success_count = 0
        
        for comment in comments:
            try:
                if action == 'approve':
                    if comment.status != 'approved':
                        comment.status = 'approved'
                        # 更新文章评论数
                        approved_count = Comment.query.filter_by(
                            article_id=comment.article_id,
                            status='approved'
                        ).count()
                        comment.article.comments_count = approved_count + 1
                        success_count += 1
                        
                elif action == 'reject':
                    old_status = comment.status
                    comment.status = 'rejected'
                    # 如果之前是已通过状态，需要更新文章评论数
                    if old_status == 'approved':
                        comment.article.comments_count = max(0, comment.article.comments_count - 1)
                    success_count += 1
                    
                elif action == 'delete':
                    # 如果是已通过的评论，需要更新文章评论数
                    if comment.status == 'approved':
                        comment.article.comments_count = max(0, comment.article.comments_count - 1)
                    db.session.delete(comment)
                    success_count += 1
                    
            except Exception as e:
                continue  # 跳过失败的操作
        
        db.session.commit()
        
        action_names = {
            'approve': '审核通过',
            'reject': '拒绝',
            'delete': '删除'
        }
        
        return jsonify({
            'success': True,
            'message': f'成功{action_names.get(action, "处理")} {success_count} 条评论',
            'processed_count': success_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'批量操作失败: {str(e)}'})


@admin.route('/api/get_location')
@login_required
def get_admin_location():
    """获取管理员当前的地理位置信息"""
    try:
        # 获取管理员IP地址
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # 获取地理位置信息
        from ..utils import get_ip_location
        location = get_ip_location(ip_address)
        
        return jsonify({
            'success': True,
            'location': location,
            'ip': ip_address
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'location': '未知地区',
            'message': f'获取位置信息失败: {str(e)}'
        })


@admin.route('/music')
@login_required
def music():
    """音乐管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10个音乐文件
    
    # 获取所有音乐文件，按上传时间倒序
    music_files = Music.query.order_by(Music.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 获取音乐相关配置
    music_enabled = Config.get_value('music_enabled', 'True') == 'True'
    music_auto_play = Config.get_value('music_auto_play', 'False') == 'True'
    music_default_volume = float(Config.get_value('music_default_volume', '0.5'))
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/music.html',
                         music_files=music_files,
                         music_enabled=music_enabled,
                         music_auto_play=music_auto_play,
                         music_default_volume=music_default_volume,
                         current_admin=current_admin,
                         session_info=session_info)


@admin.route('/music/delete/<int:music_id>', methods=['POST'])
@login_required
def delete_music(music_id):
    """删除音乐文件"""
    try:
        music = Music.query.get_or_404(music_id)
        
        # 删除文件
        if music.file_path and os.path.exists(music.file_path):
            try:
                os.remove(music.file_path)
            except Exception as e:
                print(f"删除文件失败: {str(e)}")
        
        # 删除数据库记录
        display_name = music.display_name
        db.session.delete(music)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'音乐《{display_name}》已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@admin.route('/music/edit/<int:music_id>', methods=['POST'])
@login_required
def edit_music(music_id):
    """编辑音乐显示名称"""
    try:
        music = Music.query.get_or_404(music_id)
        
        display_name = request.form.get('display_name', '').strip()
        if not display_name:
            return jsonify({'success': False, 'message': '显示名称不能为空'})
        
        music.display_name = display_name
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'音乐名称已更新为《{display_name}》',
            'music': music.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


@admin.route('/music/toggle/<int:music_id>', methods=['POST'])
@login_required
def toggle_music_enabled(music_id):
    """切换音乐启用状态"""
    try:
        music = Music.query.get_or_404(music_id)
        
        enabled = request.json.get('enabled', False)
        music.is_enabled = enabled
        db.session.commit()
        
        status_text = '已添加到前端播放列表' if enabled else '已从前端播放列表移除'
        
        return jsonify({
            'success': True,
            'message': f'音乐《{music.display_name}》{status_text}',
            'enabled': enabled
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@admin.route('/music/settings', methods=['POST'])
@login_required
def music_settings():
    """更新音乐设置"""
    try:
        enabled = request.form.get('enabled') == 'on'
        auto_play = request.form.get('auto_play') == 'on'
        default_volume = float(request.form.get('default_volume', 0.5))
        
        # 验证音量范围
        if not 0 <= default_volume <= 1:
            flash('音量值必须在0-1之间', 'danger')
            return redirect(url_for('admin.music'))
        
        # 保存设置
        Config.set_value('music_enabled', str(enabled))
        Config.set_value('music_auto_play', str(auto_play))
        Config.set_value('music_default_volume', str(default_volume))
        
        flash('音乐设置已保存', 'success')
        return redirect(url_for('admin.music'))
        
    except Exception as e:
        flash(f'保存设置失败: {str(e)}', 'danger')
        return redirect(url_for('admin.music'))


@admin.route('/password-change', methods=['GET', 'POST'])
@login_required
def password_change():
    """管理员密码修改页面"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # 检查新密码和确认密码是否一致
        if form.new_password.data != form.confirm_password.data:
            flash('新密码和确认密码不一致，请重新输入', 'danger')
            return render_template('admin/password_change.html', 
                                 form=form,
                                 current_admin=get_current_admin(),
                                 session_info=get_session_info())
        
        # 使用auth.py中的密码修改函数
        try:
            success, message = change_admin_password(
                form.current_password.data, 
                form.new_password.data
            )
            
            if success:
                flash(message, 'success')
                # 密码修改成功后重定向到登录页
                return redirect(url_for('admin.login'))
            else:
                flash(message, 'danger')
                
        except Exception as e:
            flash(f'密码修改失败: {str(e)}', 'danger')
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/password_change.html',
                         form=form,
                         current_admin=current_admin,
                         session_info=session_info)