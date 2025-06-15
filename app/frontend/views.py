#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 前端视图函数
from flask import render_template, request, abort, session, jsonify, url_for
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime, timedelta
import re
import markdown
from . import frontend
from ..models import Article, Tag, Config, Comment, Music
from .. import db
from sqlalchemy.orm import joinedload


def _build_back_url_with_position(referer_url, article_id):
    """构建带位置信息的返回URL"""
    # 解析来源URL
    parsed_url = urlparse(referer_url)
    
    # 如果来源URL是文章页面，使用首页代替
    if '/article/' in parsed_url.path:
        # 构建首页URL
        return url_for('frontend.index', scroll_to_article=article_id, _external=False)
    
    query_params = parse_qs(parsed_url.query)
    
    # 如果已经有scroll_to_article参数，保持不变；否则添加
    if 'scroll_to_article' not in query_params:
        query_params['scroll_to_article'] = [str(article_id)]
    
    # 重新构建URL
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))
    
    return new_url


def get_current_background():
    """获取当前应该显示的背景"""
    background_type = Config.get_value('background_type', 'custom')
    time_based = Config.get_value('background_time_based', 'False') == 'True'
    
    if background_type == 'preset':
        current_preset = Config.get_value('background_preset', 'sky')
        
        # 如果开启了时间变化，根据当前时间选择背景
        if time_based:
            now = datetime.now()
            hour = now.hour
            
            if 6 <= hour < 11:
                time_preset = 'spring'  # 春日暖阳
            elif 11 <= hour < 15:
                time_preset = 'reading' # 阅读舒适
            elif 15 <= hour < 18:
                time_preset = 'ocean'   # 深海蓝调
            elif 18 <= hour < 22:
                time_preset = 'sunset'  # 黄昏夕阳
            else:
                time_preset = 'night'   # 星空夜晚
            
            current_preset = time_preset
        
        # 获取预设背景的渐变样式
        from ..admin.views import PRESET_BACKGROUNDS
        if current_preset in PRESET_BACKGROUNDS:
            preset_info = PRESET_BACKGROUNDS[current_preset]
            result = {
                'type': 'preset',
                'preset': current_preset,
                'gradient': preset_info['gradient'],
                'name': preset_info['name']
            }
            
            # 检查是否为动态背景
            if 'animation' in preset_info:
                result['type'] = 'animated'
                result['animation'] = preset_info['animation']
            
            return result
    
    # 返回自定义背景或默认背景
    background_image = Config.get_value('background_image', '')
    background_fit_mode = Config.get_value('background_fit_mode', 'cover')
    
    return {
        'type': 'custom',
        'image': background_image,
        'fit_mode': background_fit_mode
    }


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


def build_article_query(time_range='all', custom_date='', tag_filter='', permission_filter='all'):
    """构建文章查询，应用所有筛选条件"""
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
    
    return query


@frontend.route('/')
def index():
    """首页视图 - 显示文章列表和分页"""
    page = request.args.get('page', 1, type=int)
    time_range = request.args.get('range', 'all')  # 时间范围筛选
    custom_date = request.args.get('date', '')  # 自定义日期
    tag_filter = request.args.get('tag', '')  # 标签筛选
    permission_filter = request.args.get('permission', 'all')  # 权限筛选
    timeline_order = request.args.get('timeline_order', 'created')  # 时间线排序方式
    per_page = 10  # 每页显示10篇文章
    
    # 构建基础查询（应用所有筛选条件）
    base_query = build_article_query(time_range, custom_date, tag_filter, permission_filter)
    
    # 获取已发布的文章列表，按置顶和时间排序
    # 优化：预加载标签关联以减少N+1查询
    articles = base_query.options(joinedload(Article.tags)).order_by(
        Article.is_top.desc(),  # 置顶文章优先
        Article.created_at.desc()  # 然后按创建时间倒序
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 获取所有标签（用于筛选器）
    all_tags = Tag.query.order_by(Tag.name).all()
    
    # 获取热门文章（按浏览量，应用相同的筛选条件）
    top_articles = build_article_query(time_range, custom_date, tag_filter, permission_filter).options(joinedload(Article.tags)).order_by(
        Article.view_count.desc()
    ).limit(5).all()
    
    # 获取时间线文章（应用相同的筛选条件，不受分页限制，用于导航）
    timeline_base_query = build_article_query(time_range, custom_date, tag_filter, permission_filter)
    if timeline_order == 'updated':
        timeline_articles = timeline_base_query.options(joinedload(Article.tags)).order_by(
            Article.is_top.desc(),
            Article.updated_at.desc()
        ).limit(50).all()
    else:
        timeline_articles = timeline_base_query.options(joinedload(Article.tags)).order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        ).limit(50).all()
    
    # 获取欢迎语配置
    welcome_title = Config.get_value('homepage_welcome_title', '欢迎来到我的个人博客')
    welcome_subtitle = Config.get_value('homepage_welcome_subtitle', '记录生活，分享想法，探索世界')
    
    # 计算所有已发布文章的总浏览量
    from sqlalchemy import func
    total_views = db.session.query(func.sum(Article.view_count)).filter_by(status='published').scalar() or 0
    
    # 获取背景配置
    background_config = get_current_background()
    
    return render_template(
        'frontend/index.html', 
        articles=articles, 
        time_range=time_range, 
        custom_date=custom_date,
        tag_filter=tag_filter,
        permission_filter=permission_filter,
        timeline_order=timeline_order,
        all_tags=all_tags,
        top_articles=top_articles,
        timeline_articles=timeline_articles,
        welcome_title=welcome_title,
        welcome_subtitle=welcome_subtitle,
        background_config=background_config,
        total_views=total_views
    )


@frontend.route('/search')
def search():
    """搜索功能"""
    search_query = request.args.get('q', '').strip()
    time_range = request.args.get('range', 'all')  # 时间范围筛选
    custom_date = request.args.get('date', '')  # 自定义日期
    tag_filter = request.args.get('tag', '')  # 标签筛选
    permission_filter = request.args.get('permission', 'all')  # 权限筛选
    timeline_order = request.args.get('timeline_order', 'created')  # 时间线排序方式
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 构建基础查询（应用所有筛选条件）
    base_query = build_article_query(time_range, custom_date, tag_filter, permission_filter)
    
    if search_query:
        # 简化搜索：单关键词标题搜索，优化：预加载标签关联
        articles = base_query.options(joinedload(Article.tags)).filter(Article.title.contains(search_query)).order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    else:
        # 如果没有搜索词，返回所有已发布文章（带所有筛选），优化：预加载标签关联
        articles = base_query.options(joinedload(Article.tags)).order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    # 获取所有标签（用于筛选器）
    all_tags = Tag.query.order_by(Tag.name).all()
    
    # 获取热门文章（按浏览量，应用相同的筛选条件）
    top_articles = build_article_query(time_range, custom_date, tag_filter, permission_filter).options(joinedload(Article.tags)).order_by(
        Article.view_count.desc()
    ).limit(5).all()
    
    # 获取时间线文章（应用相同的筛选条件，不受分页限制，用于导航）
    timeline_base_query = build_article_query(time_range, custom_date, tag_filter, permission_filter)
    if timeline_order == 'updated':
        timeline_articles = timeline_base_query.options(joinedload(Article.tags)).order_by(
            Article.is_top.desc(),
            Article.updated_at.desc()
        ).limit(50).all()
    else:
        timeline_articles = timeline_base_query.options(joinedload(Article.tags)).order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        ).limit(50).all()
    
    # 获取欢迎语配置
    welcome_title = Config.get_value('homepage_welcome_title', '欢迎来到我的个人博客')
    welcome_subtitle = Config.get_value('homepage_welcome_subtitle', '记录生活，分享想法，探索世界')
    
    # 计算所有已发布文章的总浏览量
    from sqlalchemy import func
    total_views = db.session.query(func.sum(Article.view_count)).filter_by(status='published').scalar() or 0
    
    # 获取背景配置
    background_config = get_current_background()
    
    return render_template(
        'frontend/index.html', 
        articles=articles, 
        search_query=search_query, 
        time_range=time_range, 
        custom_date=custom_date,
        tag_filter=tag_filter,
        permission_filter=permission_filter,
        timeline_order=timeline_order,
        all_tags=all_tags,
        top_articles=top_articles,
        timeline_articles=timeline_articles,
        welcome_title=welcome_title,
        welcome_subtitle=welcome_subtitle,
        background_config=background_config,
        total_views=total_views
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
            # 获取来源URL，优先使用HTTP_REFERER，否则使用首页
            referer_url = request.headers.get('Referer', url_for('frontend.index'))
            # 如果来源URL就是当前验证页面，则使用首页
            if '/article/' in referer_url and str(article_id) in referer_url:
                referer_url = url_for('frontend.index')
            
            # 构建带位置信息的返回URL
            back_url_with_position = _build_back_url_with_position(referer_url, article_id)
            return render_template('frontend/verify.html', article=article, back_url=back_url_with_position)
    
    # 生成文章内容和目录
    article_html = ''
    article_toc = ''
    if article.content:
        # 配置Markdown扩展，生成目录
        md = markdown.Markdown(
            extensions=[
                'markdown.extensions.fenced_code',  # 代码块支持
                'markdown.extensions.tables',       # 表格支持
                'markdown.extensions.toc',          # 目录支持
                'markdown.extensions.nl2br',        # 换行支持
            ],
            extension_configs={
                'markdown.extensions.toc': {
                    'title': '文章目录',
                    'anchorlink': False,
                    'permalink': False
                }
            }
        )
        
        # 转换markdown
        article_html = md.convert(article.content)
        article_toc = md.toc
    
    # 增加浏览数（只有成功访问文章时才增加）
    article.view_count += 1
    db.session.commit()
    
    # 获取来源页面信息并构建带位置信息的返回URL
    # 优先使用from_page参数，然后是referrer
    from_page = request.args.get('from_page')
    if from_page:
        referrer_url = from_page
    else:
        referrer_url = request.referrer or url_for('frontend.index')
    
    return_url_with_position = _build_back_url_with_position(referrer_url, article_id)
    
    # 获取背景配置
    background_config = get_current_background()
    
    return render_template('frontend/article.html', 
                         article=article, 
                         article_html=article_html,
                         article_toc=article_toc,
                         background_config=background_config,
                         return_url=return_url_with_position)


@frontend.route('/verify_article', methods=['POST'])
def verify_article():
    """文章权限验证接口"""
    data = request.get_json()
    article_id = data.get('article_id')
    user_answer = data.get('answer', '').strip()
    
    if not article_id:
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
    
    # 验证答案（支持空答案的情况）
    correct_answer = (article.verify_answer or '').strip().lower()
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


@frontend.route('/api/get_location')
def get_user_location():
    """获取当前用户的地理位置信息"""
    try:
        # 获取用户IP地址
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


@frontend.route('/api/comments/<int:article_id>')
def get_comments(article_id):
    """获取文章评论列表API - 支持分页"""
    try:
        # 获取文章
        article = Article.query.filter_by(id=article_id, status='published').first()
        if not article:
            return jsonify({'success': False, 'message': '文章不存在'})
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = 10  # 每页10条评论
        
        # 构建基础查询
        query = Comment.query.options(db.joinedload(Comment.article)).filter_by(
            article_id=article_id, 
            status='approved'
        ).order_by(Comment.created_at.desc())
        
        # 分别处理顶层评论和回复评论
        # 顶层评论（用于分页）
        root_comments_query = query.filter(Comment.parent_id.is_(None))
        
        # 使用分页获取顶层评论
        root_comments_page = root_comments_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        root_comments = root_comments_page.items
        
        if not root_comments:
            return jsonify({
                'success': True,
                'comments': [],
                'pagination': {
                    'current_page': page,
                    'total_pages': root_comments_page.pages,
                    'per_page': per_page,
                    'total': root_comments_page.total,
                    'has_prev': root_comments_page.has_prev,
                    'has_next': root_comments_page.has_next,
                    'prev_page': root_comments_page.prev_num,
                    'next_page': root_comments_page.next_num
                },
                'stats': {
                    'total_comments': 0,
                    'root_comments': 0,
                    'replies': 0
                }
            })
        
        # 获取当前页顶层评论的所有回复（优化：一次查询）
        root_comment_ids = [comment.id for comment in root_comments]
        all_replies = Comment.query.filter(
            Comment.parent_id.in_(root_comment_ids),
            Comment.status == 'approved'
        ).order_by(Comment.created_at.asc()).all()
        
        # 构建评论数据结构
        comments_data = []
        
        # 为每个顶层评论构建完整的数据（包括回复）
        for root_comment in root_comments:
            comment_dict = root_comment.to_dict()
            # 添加格式化的时间显示
            from ..utils import format_relative_time
            comment_dict['time_display'] = format_relative_time(root_comment.created_at)
            
            # 添加该评论的所有回复
            comment_replies = [reply for reply in all_replies if reply.parent_id == root_comment.id]
            reply_data = []
            for reply in comment_replies:
                reply_dict = reply.to_dict()
                reply_dict['time_display'] = format_relative_time(reply.created_at)
                reply_data.append(reply_dict)
            
            comment_dict['replies'] = reply_data
            comment_dict['has_replies'] = len(reply_data) > 0
            comments_data.append(comment_dict)
        
        # 获取统计信息
        total_root_comments = root_comments_query.count()
        total_all_comments = query.count()
        
        return jsonify({
            'success': True,
            'comments': comments_data,
            'pagination': {
                'current_page': page,
                'total_pages': root_comments_page.pages,
                'per_page': per_page,
                'total': total_root_comments,
                'has_prev': root_comments_page.has_prev,
                'has_next': root_comments_page.has_next,
                'prev_page': root_comments_page.prev_num,
                'next_page': root_comments_page.next_num
            },
            'stats': {
                'total_comments': total_all_comments,
                'root_comments': total_root_comments,
                'replies': total_all_comments - total_root_comments
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取评论失败: {str(e)}'})


@frontend.route('/add_comment/<int:article_id>', methods=['POST'])
def add_comment(article_id):
    """添加评论API"""
    try:
        # 获取文章
        article = Article.query.filter_by(id=article_id, status='published').first()
        if not article:
            return jsonify({'success': False, 'message': '文章不存在'})
        
        # 检查文章是否允许评论
        if hasattr(article, 'allow_comments') and not article.allow_comments:
            return jsonify({'success': False, 'message': '该文章已关闭评论功能'})
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'})
        
        content = data.get('content', '').strip()
        nickname = data.get('nickname', '').strip()
        is_private = data.get('isPrivate', False)
        parent_id = data.get('parentId')  # 父评论ID，用于回复功能
        
        # 验证父评论（如果是回复）
        parent_comment = None
        if parent_id:
            parent_comment = Comment.query.filter_by(
                id=parent_id, 
                article_id=article_id,
                status='approved'  # 只能回复已审核通过的评论
            ).first()
            if not parent_comment:
                return jsonify({'success': False, 'message': '回复的评论不存在或未通过审核'})
        
        # 验证评论内容
        if not content:
            return jsonify({'success': False, 'message': '评论内容不能为空'})
        
        if len(content) < 2:
            return jsonify({'success': False, 'message': '评论内容至少需要2个字符'})
            
        if len(content) > 1000:
            return jsonify({'success': False, 'message': '评论内容不能超过1000个字符'})
        
        # 验证昵称长度
        if nickname and len(nickname) > 50:
            return jsonify({'success': False, 'message': '昵称长度不能超过50个字符'})
        
        # 获取用户IP地址
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # 获取地理位置信息
        from ..utils import get_ip_location
        location = get_ip_location(ip_address)
        
        # 创建评论记录
        comment = Comment(
            content=content,
            nickname=nickname if nickname else None,
            ip_address=ip_address,
            location=location,
            is_private=is_private,
            article_id=article_id,
            parent_id=parent_id,  # 设置父评论ID
            status='pending'  # 默认待审核状态
        )
        
        db.session.add(comment)
        
        # 更新文章评论数量（包括待审核的评论）
        if hasattr(article, 'comments_count'):
            article.comments_count = article.comments.count() + 1
        
        db.session.commit()
        
        # 根据是否私密评论和是否回复返回不同消息
        if parent_id:
            # 这是一个回复
            if is_private:
                success_message = '回复已提交给作者！私密回复不会公开显示'
            else:
                success_message = '回复发表成功！等待管理员审核后显示'
        else:
            # 这是一个评论
            if is_private:
                success_message = '已提交给作者！私密评论不会公开显示'
            else:
                success_message = '评论发表成功！等待管理员审核后显示'
        
        return jsonify({
            'success': True,
            'message': success_message,
            'comment': {
                'id': comment.id,
                'display_name': comment.display_name,
                'location_display': comment.location_display,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'status': comment.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'发表评论失败: {str(e)}'})


@frontend.route('/like_article/<int:article_id>', methods=['POST'])
def like_article(article_id):
    """文章点赞API接口"""
    try:
        # 获取文章
        article = Article.query.filter_by(id=article_id, status='published').first()
        if not article:
            return jsonify({'success': False, 'message': '文章不存在'})
        
        # 获取已点赞文章列表
        liked_articles = session.get('liked_articles', [])
        
        # 确保session中的数据是列表
        if not isinstance(liked_articles, list):
            liked_articles = []
        
        # 检查是否已经点赞
        if article_id in liked_articles:
            return jsonify({'success': False, 'message': '您已经为这篇文章点过赞了'})
        
        # 增加点赞数
        article.likes_count += 1
        
        # 记录到session
        liked_articles.append(article_id)
        session['liked_articles'] = liked_articles
        session.permanent = True
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '点赞成功',
            'likes_count': article.likes_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'点赞失败: {str(e)}'})


@frontend.route('/api/article-page/<int:article_id>')
def get_article_page(article_id):
    """获取文章所在的页面API"""
    try:
        # 获取当前筛选参数
        time_range = request.args.get('range', 'all')
        custom_date = request.args.get('date', '')
        tag_filter = request.args.get('tag', '')
        permission_filter = request.args.get('permission', 'all')
        search_query = request.args.get('q', '')
        per_page = 10
        
        # 构建基础查询（使用统一的查询构建函数）
        base_query = build_article_query(time_range, custom_date, tag_filter, permission_filter)
        
        # 应用搜索筛选
        if search_query:
            base_query = base_query.filter(Article.title.contains(search_query))
        
        # 按置顶和创建时间排序（与首页排序逻辑保持一致）
        ordered_query = base_query.order_by(
            Article.is_top.desc(),
            Article.created_at.desc()
        )
        
        # 获取所有符合条件的文章ID列表
        all_article_ids = [article.id for article in ordered_query.all()]
        
        # 检查目标文章是否在结果中
        if article_id not in all_article_ids:
            return jsonify({
                'success': False, 
                'message': '文章在当前筛选条件下不可见'
            })
        
        # 计算文章在结果中的位置（从0开始）
        article_position = all_article_ids.index(article_id)
        
        # 计算页码（从1开始）
        page_number = (article_position // per_page) + 1
        
        return jsonify({
            'success': True,
            'page': page_number,
            'position': article_position + 1,
            'total': len(all_article_ids)
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'查询失败: {str(e)}'
        })


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
                'title': '文章目录',
                'anchorlink': False,
                'permalink': False
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


# 添加点赞状态检查函数
@frontend.app_template_filter('is_liked')
def is_liked_filter(article_id):
    """检查文章是否已被点赞"""
    liked_articles = session.get('liked_articles', [])
    if not isinstance(liked_articles, list):
        return False
    
    return int(article_id) in liked_articles


# 添加搜索关键词高亮过滤器
@frontend.app_template_filter('highlight_search')
def highlight_search_filter(text, search_query):
    """高亮显示搜索关键词"""
    if not search_query or not text:
        return text
    
    import re
    from markupsafe import Markup
    
    # 将搜索词按空格分割
    search_terms = search_query.split()
    highlighted_text = text
    
    for term in search_terms:
        if term.strip():
            # 忽略大小写的正则匹配
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted_text = pattern.sub(
                f'<mark class="search-highlight">{term}</mark>', 
                highlighted_text
            )
    
    return Markup(highlighted_text) 


@frontend.route('/api/music/list')
def get_music_list():
    """获取音乐列表API"""
    try:
        # 检查音乐功能是否启用
        music_enabled = Config.get_value('music_enabled', 'True') == 'True'
        if not music_enabled:
            return jsonify({
                'success': True,
                'music_list': [],
                'config': {
                    'enabled': False,
                    'auto_play': False,
                    'default_volume': 0.5
                }
            })
        
        # 获取所有启用的音乐文件
        music_files = Music.query.filter_by(is_enabled=True).order_by(Music.created_at.desc()).all()
        
        # 获取音乐配置
        music_auto_play = Config.get_value('music_auto_play', 'False') == 'True'
        music_default_volume = float(Config.get_value('music_default_volume', '0.5'))
        
        # 转换为字典格式
        music_list = []
        for music in music_files:
            music_list.append({
                'id': music.id,
                'display_name': music.display_name,
                'web_path': music.web_path,
                'file_size_mb': music.file_size_mb
            })
        
        return jsonify({
            'success': True,
            'music_list': music_list,
            'config': {
                'enabled': True,
                'auto_play': music_auto_play,
                'default_volume': music_default_volume
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取音乐列表失败: {str(e)}',
            'music_list': [],
            'config': {
                'enabled': False,
                'auto_play': False,
                'default_volume': 0.5
            }
        }) 