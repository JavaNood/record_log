#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms.widgets import CheckboxInput, ListWidget


class LoginForm(FlaskForm):
    """管理员登录表单"""
    username = StringField(
        '用户名', 
        validators=[
            DataRequired(message='请输入用户名'),
            Length(min=2, max=20, message='用户名长度应在2-20个字符之间')
        ],
        render_kw={'placeholder': '请输入用户名', 'class': 'form-control'}
    )
    
    password = PasswordField(
        '密码', 
        validators=[
            DataRequired(message='请输入密码'),
            Length(min=6, max=128, message='密码长度应在6-128个字符之间')
        ],
        render_kw={'placeholder': '请输入密码', 'class': 'form-control'}
    )
    
    remember_me = BooleanField(
        '记住我', 
        render_kw={'class': 'form-check-input'}
    )
    
    submit = SubmitField(
        '登录', 
        render_kw={'class': 'btn btn-primary w-100'}
    )


class MultiCheckboxField(SelectMultipleField):
    """
    多选框字段，用于标签选择
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class ArticleEditForm(FlaskForm):
    """文章编辑表单"""
    title = StringField('文章标题', validators=[
        DataRequired(message='标题为必填项'),
        Length(min=1, max=200, message='标题长度应在1-200字符之间')
    ], render_kw={
        'class': 'form-control',
        'id': 'article-title',
        'placeholder': '请输入文章标题...'
    })
    
    content = TextAreaField('文章内容', validators=[
        DataRequired(message='内容为必填项')
    ], render_kw={
        'class': 'form-control',
        'id': 'article-content',
        'rows': 20,
        'placeholder': '请输入文章内容，支持Markdown格式...'
    })
    
    summary = TextAreaField('前端展示内容', validators=[
        Optional(),
        Length(max=500, message='展示内容长度不能超过500个字符')
    ], render_kw={
        'class': 'form-control',
        'id': 'article-summary',
        'rows': 3,
        'placeholder': '可选填写，用于首页文章列表展示。如果不填写，将自动截取文章正文前2行内容'
    })
    
    # 标签选择字段
    tags = MultiCheckboxField(
        '文章标签',
        coerce=int,
        validators=[Optional()],
        description='选择文章相关的标签'
    )
    
    permission = SelectField(
        '文章权限',
        choices=[
            ('public', '公开访问'),
            ('verify', '需要验证')
        ],
        default='public',
        render_kw={
            'class': 'form-select',
            'id': 'article-permission'
        }
    )
    
    # 验证相关字段
    verify_question = StringField(
        '验证提示词',
        validators=[
            Length(max=200, message='提示词长度不能超过200个字符')
        ],
        render_kw={
            'placeholder': '请输入验证提示词（权限为需要验证时必填）',
            'class': 'form-control',
            'id': 'verify-question'
        }
    )
    
    verify_answer = StringField(
        '验证答案',
        validators=[
            Optional(),
            Length(max=100, message='答案长度不能超过100个字符')
        ],
        render_kw={
            'placeholder': '请输入验证答案（可选，留空表示允许任意答案）',
            'class': 'form-control',
            'id': 'verify-answer'
        }
    )
    
    # 自定义浏览数
    view_count = IntegerField(
        '浏览数',
        validators=[
            Optional(),
            NumberRange(min=0, max=99999999, message='浏览数应在0-99999999之间')
        ],
        default=0,
        render_kw={
            'class': 'form-control',
            'id': 'article-view-count',
            'min': '0'
        }
    )
    
    # 自定义点赞数
    likes_count = IntegerField(
        '点赞数',
        validators=[
            Optional(),
            NumberRange(min=0, max=99999999, message='点赞数应在0-99999999之间')
        ],
        default=0,
        render_kw={
            'class': 'form-control',
            'id': 'article-likes-count',
            'min': '0'
        }
    )
    
    # 创建时间 - 使用字符串字段
    created_at = StringField(
        '创建时间',
        validators=[Optional()],
        render_kw={
            'class': 'form-control',
            'id': 'article-created-at',
            'placeholder': '格式：2025-06-11 21:34:00'
        }
    )
    
    # 更新时间 - 使用字符串字段
    updated_at = StringField(
        '更新时间',
        validators=[Optional()],
        render_kw={
            'class': 'form-control',
            'id': 'article-updated-at',
            'placeholder': '格式：2025-06-11 21:34:00'
        }
    )
    
    status = SelectField(
        '发布状态',
        choices=[
            ('draft', '保存为草稿'),
            ('published', '立即发布')
        ],
        default='draft',
        render_kw={
            'class': 'form-select',
            'id': 'article-status'
        }
    )
    
    is_top = BooleanField(
        '置顶文章',
        render_kw={
            'class': 'form-check-input',
            'id': 'article-is-top'
        }
    )
    
    allow_comments = BooleanField(
        '允许评论',
        default=True,
        render_kw={
            'class': 'form-check-input',
            'id': 'article-allow-comments'
        }
    )
    
    publish_location = StringField(
        '发布地址',
        validators=[
            Length(max=100, message='发布地址长度不能超过100个字符')
        ],
        render_kw={
            'placeholder': '请输入发布地址（如：北京、上海、广东等）',
            'class': 'form-control',
            'id': 'article-publish-location'
        }
    )
    
    submit = SubmitField(
        '保存文章',
        render_kw={
            'class': 'btn btn-primary btn-lg',
            'id': 'submit-btn'
        }
    )


class PasswordChangeForm(FlaskForm):
    """密码修改表单"""
    current_password = PasswordField(
        '当前密码', 
        validators=[
            DataRequired(message='请输入当前密码'),
            Length(min=6, max=128, message='密码长度应在6-128个字符之间')
        ],
        render_kw={'placeholder': '请输入当前密码', 'class': 'form-control'}
    )
    
    new_password = PasswordField(
        '新密码', 
        validators=[
            DataRequired(message='请输入新密码'),
            Length(min=6, max=128, message='新密码长度应在6-128个字符之间')
        ],
        render_kw={'placeholder': '请输入新密码（至少6位）', 'class': 'form-control'}
    )
    
    confirm_password = PasswordField(
        '确认新密码', 
        validators=[
            DataRequired(message='请确认新密码'),
            Length(min=6, max=128, message='确认密码长度应在6-128个字符之间')
        ],
        render_kw={'placeholder': '请再次输入新密码', 'class': 'form-control'}
    )
    
    submit = SubmitField(
        '修改密码', 
        render_kw={'class': 'btn btn-primary'}
    ) 