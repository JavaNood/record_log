#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 前端视图函数
from flask import render_template, request, abort, session, jsonify
from datetime import datetime, timedelta
import re
import markdown
from . import frontend
from ..models import Article, Tag
from .. import db


def parse_custom_date(date_str):
    """解析自定义日期格式：YYYY, YYYYMM, YYYYMMDD"""
    if not date_str:
        return None
    
    # 移除非数字字符
    date_str = re.sub(r'[^\d]', '', date_str)
    
    try:
        if len(date_str) == 4:  # YYYY
            return datetime(int(date_str), 1, 1)
        elif len(date_str) == 6:  # YYYYMM
            year = int(date_str[:4])
            month = int(date_str[4:6])
            if 1 <= month <= 12:
                return datetime(year, month, 1)
        elif len(date_str) == 8:  # YYYYMMDD
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
    except (ValueError, TypeError):
        pass
    
    return None


@frontend.route('/')
def index():
    """首页视图 - 显示文章列表和分页"""
    page = request.args.get('page', 1, type=int)
    time_range = request.args.get('range', 'all')  # 时间范围筛选
    custom_date = request.args.get('date', '')  # 自定义日期
    tag_filter = request.args.get('tag', '')  # 标签筛选
    permission_filter = request.args.get('permission', 'all')  # 权限筛选
    per_page = 10  # 每页显示10篇文章
    
    # 构建查询
    query = Article.query.filter_by(status='published')
    
    # 根据时间范围筛选
    if time_range == 'custom' and custom_date:
        start_date = parse_custom_date(custom_date)
        if start_date:
            # 根据日期格式确定结束日期
            date_str = re.sub(r'[^\d]', '', custom_date)
            if len(date_str) == 4:  # 年份：整年
                end_date = datetime(start_date.year + 1, 1, 1)
            elif len(date_str) == 6:  # 年月：整月
                if start_date.month == 12:
                    end_date = datetime(start_date.year + 1, 1, 1)
                else:
                    end_date = datetime(start_date.year, start_date.month + 1, 1)
            else:  # 具体日期：当天
                end_date = start_date + timedelta(days=1)
            
            query = query.filter(
                Article.created_at >= start_date,
                Article.created_at < end_date
            )
    elif time_range != 'all':
        now = datetime.now()
        if time_range == 'week':
            start_date = now - timedelta(days=7)
        elif time_range == 'month':
            start_date = now - timedelta(days=30)
        elif time_range == 'quarter':
            start_date = now - timedelta(days=90)
        elif time_range == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = None
            
        if start_date:
            query = query.filter(Article.created_at >= start_date)
    
    # 根据标签筛选
    if tag_filter:
        query = query.join(Article.tags).filter(Tag.name == tag_filter)
    
    # 根据权限筛选
    if permission_filter == 'public':
        query = query.filter(Article.permission == 'public')
    elif permission_filter == 'verify':
        query = query.filter(Article.permission == 'verify')
    
    # 获取已发布的文章列表，按置顶和时间排序
    articles = query.order_by(
        Article.is_top.desc(),  # 置顶文章优先
        Article.created_at.desc()  # 然后按创建时间倒序
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 获取所有标签（用于筛选器）
    all_tags = Tag.query.order_by(Tag.name).all()
    
    # 获取Top文章（按浏览量）
    top_articles = Article.query.filter_by(status='published').order_by(
        Article.view_count.desc()
    ).limit(5).all()
    
    return render_template(
        'frontend/index.html', 
        articles=articles, 
        time_range=time_range, 
        custom_date=custom_date,
        tag_filter=tag_filter,
        permission_filter=permission_filter,
        all_tags=all_tags,
        top_articles=top_articles
    )


@frontend.route('/search')
def search():
    """搜索功能"""
    query = request.args.get('q', '').strip()
    time_range = request.args.get('range', 'all')  # 时间范围筛选
    custom_date = request.args.get('date', '')  # 自定义日期
    tag_filter = request.args.get('tag', '')  # 标签筛选
    permission_filter = request.args.get('permission', 'all')  # 权限筛选
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 构建基础查询
    base_query = Article.query.filter(Article.status == 'published')
    
    # 根据时间范围筛选
    if time_range == 'custom' and custom_date:
        start_date = parse_custom_date(custom_date)
        if start_date:
            # 根据日期格式确定结束日期
            date_str = re.sub(r'[^\d]', '', custom_date)
            if len(date_str) == 4:  # 年份：整年
                end_date = datetime(start_date.year + 1, 1, 1)
            elif len(date_str) == 6:  # 年月：整月
                if start_date.month == 12:
                    end_date = datetime(start_date.year + 1, 1, 1)
                else:
                    end_date = datetime(start_date.year, start_date.month + 1, 1)
            else:  # 具体日期：当天
                end_date = start_date + timedelta(days=1)
            
            base_query = base_query.filter(
                Article.created_at >= start_date,
                Article.created_at < end_date
            )
    elif time_range != 'all':
        now = datetime.now()
        if time_range == 'week':
            start_date = now - timedelta(days=7)
        elif time_range == 'month':
            start_date = now - timedelta(days=30)
        elif time_range == 'quarter':
            start_date = now - timedelta(days=90)
        elif time_range == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = None
            
        if start_date:
            base_query = base_query.filter(Article.created_at >= start_date)
    
    # 根据标签筛选
    if tag_filter:
        base_query = base_query.join(Article.tags).filter(Tag.name == tag_filter)
    
    # 根据权限筛选
    if permission_filter == 'public':
        base_query = base_query.filter(Article.permission == 'public')
    elif permission_filter == 'verify':
        base_query = base_query.filter(Article.permission == 'verify')
    
    if query:
        # 按标题搜索已发布的文章
        articles = base_query.filter(
            Article.title.contains(query)
        ).order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    else:
        # 如果没有搜索词，返回所有已发布文章（带所有筛选）
        articles = base_query.order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    # 获取所有标签（用于筛选器）
    all_tags = Tag.query.order_by(Tag.name).all()
    
    # 获取Top文章（按浏览量）
    top_articles = Article.query.filter_by(status='published').order_by(
        Article.view_count.desc()
    ).limit(5).all()
    
    return render_template(
        'frontend/index.html', 
        articles=articles, 
        search_query=query, 
        time_range=time_range, 
        custom_date=custom_date,
        tag_filter=tag_filter,
        permission_filter=permission_filter,
        all_tags=all_tags,
        top_articles=top_articles
    )


@frontend.route('/article/<int:article_id>')
def article_detail(article_id):
    """文章详情页"""
    # 获取文章
    article = Article.query.filter_by(id=article_id, status='published').first()
    
    if not article:
        abort(404)
    
    # 检查文章权限
    if article.permission == 'verify':
        # 需要验证的文章，检查是否已验证
        verified_articles = session.get('verified_articles', [])
        
        # 确保session中的数据是整数列表
        if not isinstance(verified_articles, list):
            verified_articles = []
            session['verified_articles'] = verified_articles
        
        # 检查当前文章是否已验证（支持不同数据类型的比较）
        article_verified = False
        for verified_id in verified_articles:
            if int(verified_id) == article_id:
                article_verified = True
                break
        
        if not article_verified:
            # 未验证，返回验证页面
            return render_template('frontend/verify.html', article=article)
    
    # 增加浏览数（只有成功访问文章时才增加）
    article.view_count += 1
    db.session.commit()
    
    return render_template('frontend/article.html', article=article)


@frontend.route('/verify_article', methods=['POST'])
def verify_article():
    """文章权限验证接口"""
    data = request.get_json()
    article_id = data.get('article_id')
    user_answer = data.get('answer', '').strip()
    
    if not article_id or not user_answer:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    # 确保article_id是整数
    try:
        article_id = int(article_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '文章ID格式错误'})
    
    # 获取文章
    article = Article.query.filter_by(id=article_id, status='published').first()
    if not article or article.permission != 'verify':
        return jsonify({'success': False, 'message': '文章不存在或无需验证'})
    
    # 检查文章是否设置了验证答案
    if not article.verify_answer:
        return jsonify({'success': False, 'message': '文章验证配置错误'})
    
    # 验证答案（不区分大小写，去除首尾空格）
    correct_answer = article.verify_answer.strip().lower()
    user_answer_clean = user_answer.strip().lower()
    
    if user_answer_clean == correct_answer:
        # 验证成功，记录到session
        verified_articles = session.get('verified_articles', [])
        
        # 确保session中的数据是列表
        if not isinstance(verified_articles, list):
            verified_articles = []
        
        # 检查是否已经记录（避免重复）
        if article_id not in verified_articles:
            verified_articles.append(article_id)
            session['verified_articles'] = verified_articles
            # 确保session持久化
            session.permanent = True
        
        return jsonify({'success': True, 'message': '验证成功'})
    else:
        return jsonify({'success': False, 'message': '答案错误，请重试'})


# 添加Markdown渲染过滤器
@frontend.app_template_filter('markdown')
def markdown_filter(text):
    """Markdown渲染过滤器"""
    if not text:
        return ''
    
    # 配置Markdown扩展
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.fenced_code',  # 代码块支持
            'markdown.extensions.tables',       # 表格支持
            'markdown.extensions.toc',          # 目录支持
            'markdown.extensions.nl2br',        # 换行支持
        ],
        extension_configs={
            'markdown.extensions.toc': {
                'title': '目录'
            }
        }
    )
    
    # 转换markdown并保留HTML标签
    html = md.convert(text)
    return html

# 添加内容预览过滤器
@frontend.app_template_filter('preview')
def preview_filter(text, lines=2):
    """内容预览过滤器，只显示前几行"""
    if not text:
        return ''
    
    import re
    
    # 先处理HTML img标签，替换为[图片]
    text = re.sub(r'<img[^>]*>', '[图片]', text)
    
    # 处理markdown图片语法，替换为[图片]
    text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', '[图片]', text)
    
    # 移除其他HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 按行分割
    lines_list = text.split('\n')
    preview_lines = []
    
    count = 0
    for line in lines_list:
        if line.strip():  # 只计算非空行
            preview_lines.append(line.strip())
            count += 1
            if count >= lines:
                break
    
    return '\n'.join(preview_lines) + ('...' if count >= lines else '')

# 添加验证状态检查函数
@frontend.app_template_filter('is_verified')
def is_verified_filter(article_id):
    """检查文章是否已通过验证"""
    verified_articles = session.get('verified_articles', [])
    if not isinstance(verified_articles, list):
        return False
    
    for verified_id in verified_articles:
        if int(verified_id) == int(article_id):
            return True
    return False 