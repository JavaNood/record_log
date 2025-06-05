#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from . import admin
from .forms import LoginForm, ArticleEditForm
from ..auth import (
    authenticate_admin, admin_logout, login_required, admin_required,
    get_current_admin, admin_login, get_session_info
)
from ..models import Article, Tag
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
    
    # 获取所有文章，包括草稿和已发布的
    articles = Article.query.order_by(
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