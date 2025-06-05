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
from ..models import Article, Tag, Config
from .. import db


# 允许的图片格式
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

def allowed_image_file(filename):
    """检查是否是允许的图片格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


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
    per_page = 10  # 每页显示10篇文章
    
    # 获取所有文章，包括草稿和已发布的，优化：预加载标签关联
    articles = Article.query.options(joinedload(Article.tags)).order_by(
        Article.is_top.desc(),  # 置顶文章优先
        Article.updated_at.desc()  # 按更新时间降序
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/articles.html',
                         articles=articles,
                         current_admin=current_admin,
                         session_info=session_info)


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
            if not form.verify_question.data or not form.verify_answer.data:
                flash('权限为需要验证时，验证提示词和答案为必填项', 'danger')
                return render_template('admin/article_edit.html',
                                     form=form,
                                     article=None,
                                     is_new=True,
                                     all_tags=all_tags,
                                     current_admin=get_current_admin(),
                                     session_info=get_session_info())
        
        # 处理表单提交
        try:
            article = Article(
                title=form.title.data.strip(),
                content=form.content.data,
                permission=form.permission.data,
                verify_question=form.verify_question.data.strip() if form.verify_question.data else None,
                verify_answer=form.verify_answer.data.strip() if form.verify_answer.data else None,
                status=form.status.data,
                is_top=form.is_top.data,
                view_count=form.view_count.data or 0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
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
            if not form.verify_question.data or not form.verify_answer.data:
                flash('权限为需要验证时，验证提示词和答案为必填项', 'danger')
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
            article.permission = form.permission.data
            article.verify_question = form.verify_question.data.strip() if form.verify_question.data else None
            article.verify_answer = form.verify_answer.data.strip() if form.verify_answer.data else None
            article.status = form.status.data
            article.is_top = form.is_top.data
            article.view_count = form.view_count.data or 0
            article.updated_at = datetime.utcnow()
            
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
        form.permission.data = article.permission
        form.verify_question.data = article.verify_question
        form.verify_answer.data = article.verify_answer
        form.status.data = article.status
        form.is_top.data = article.is_top
        form.view_count.data = article.view_count
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
        
        article.updated_at = datetime.utcnow()
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
                article.updated_at = datetime.utcnow()
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


@admin.route('/background', methods=['GET', 'POST'])
@login_required
def background_edit():
    """背景图片设置页面"""
    if request.method == 'POST':
        try:
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
    current_bg = Config.get_value('background_image', '')
    blur_level = int(Config.get_value('background_blur_level', '10'))
    fit_mode = Config.get_value('background_fit_mode', 'cover')
    
    current_admin = get_current_admin()
    session_info = get_session_info()
    
    return render_template('admin/background_edit.html',
                         current_background=current_bg,
                         blur_level=blur_level,
                         fit_mode=fit_mode,
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
        
        # 清除配置
        Config.set_value('background_image', '')
        Config.set_value('background_blur_level', '10')
        
        return jsonify({'success': True, 'message': '背景已重置为默认'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'重置失败: {str(e)}'}) 


# 注释掉公网部署时的密码帮助页面，避免暴露管理员重置方法
# @admin.route('/password-help')
# def password_help():
#     """密码找回帮助页面"""
#     return render_template('admin/password_help.html')


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