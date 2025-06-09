#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
批量创建文章脚本
用法: python bulk_create_articles.py [数量] [--status published/draft] [--with-tags]

示例:
python bulk_create_articles.py 10                    # 创建10篇草稿文章
python bulk_create_articles.py 5 --status published  # 创建5篇已发布文章
python bulk_create_articles.py 20 --with-tags        # 创建20篇文章并添加标签
"""

import sys
import os
import argparse
import random
from datetime import datetime, timedelta
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Article, Tag, db


# 预定义的文章数据模板
ARTICLE_TEMPLATES = [
    {
        'title': 'Python编程入门指南',
        'content': '''# Python编程入门指南

Python是一种简单易学、功能强大的编程语言。它有高效的高层数据结构，简单而有效地实现面向对象编程。

## 为什么选择Python？

1. **语法简洁明了**：Python的语法接近自然语言，易于理解
2. **功能强大**：拥有丰富的标准库和第三方库
3. **跨平台**：可以在Windows、Mac、Linux等系统上运行
4. **应用广泛**：Web开发、数据分析、人工智能等领域都有应用

## 基础语法

```python
# 变量定义
name = "Python"
version = 3.9

# 函数定义
def hello_world():
    print("Hello, World!")

# 调用函数
hello_world()
```

## 数据类型

Python有多种内置数据类型：
- 整数 (int)
- 浮点数 (float)
- 字符串 (str)
- 列表 (list)
- 字典 (dict)
- 元组 (tuple)

这是一篇关于Python编程的入门文章，希望对初学者有所帮助。''',
        'summary': '一篇面向初学者的Python编程入门指南，介绍了Python的特点、基础语法和数据类型。',
        'author': 'Python教程编辑部',
        'tags': ['Python', '编程', '教程', '入门']
    },
    {
        'title': 'Web开发技术栈选择指南',
        'content': '''# Web开发技术栈选择指南

现代Web开发涉及前端、后端、数据库等多个技术层面，选择合适的技术栈对项目成功至关重要。

## 前端技术栈

### React
- **优点**：组件化开发、虚拟DOM、生态丰富
- **适用场景**：大型单页应用、需要高性能的交互式应用

### Vue.js
- **优点**：学习曲线平缓、文档完善、双向数据绑定
- **适用场景**：中小型项目、快速原型开发

### Angular
- **优点**：企业级框架、TypeScript支持、完整的解决方案
- **适用场景**：大型企业应用、需要严格架构的项目

## 后端技术栈

### Node.js
- **优点**：JavaScript全栈、高并发处理、npm生态
- **适用场景**：实时应用、API服务、微服务架构

### Python (Django/Flask)
- **优点**：开发效率高、库丰富、语法简洁
- **适用场景**：快速开发、数据处理、机器学习集成

### Java (Spring Boot)
- **优点**：稳定可靠、性能好、企业级支持
- **适用场景**：大型系统、金融系统、高并发应用

## 数据库选择

### 关系型数据库
- **MySQL**：开源、性能好、社区活跃
- **PostgreSQL**：功能强大、支持复杂查询、数据完整性好

### NoSQL数据库
- **MongoDB**：文档型、灵活的数据结构
- **Redis**：内存数据库、高性能缓存

## 总结

技术栈的选择需要考虑项目需求、团队技能、性能要求等多个因素。没有最好的技术栈，只有最适合的技术栈。''',
        'summary': '详细介绍了现代Web开发中前端、后端、数据库等技术栈的选择指南，帮助开发者做出合适的技术决策。',
        'author': 'Web开发专家',
        'tags': ['Web开发', '技术栈', '前端', '后端', '数据库']
    },
    {
        'title': '机器学习入门：从零开始的AI之旅',
        'content': '''# 机器学习入门：从零开始的AI之旅

机器学习是人工智能的核心技术之一，它让计算机能够从数据中学习并做出预测或决策。

## 什么是机器学习？

机器学习是一种让计算机系统能够自动学习和改进的方法，无需明确编程指令。通过算法分析数据，识别模式，并基于这些模式做出预测。

## 机器学习的主要类型

### 1. 监督学习 (Supervised Learning)
- **定义**：使用标记的训练数据来学习输入和输出之间的映射关系
- **应用**：分类、回归、预测
- **算法**：线性回归、决策树、随机森林、支持向量机

### 2. 无监督学习 (Unsupervised Learning)
- **定义**：从未标记的数据中发现隐藏的模式或结构
- **应用**：聚类、降维、异常检测
- **算法**：K-means、主成分分析(PCA)、自编码器

### 3. 强化学习 (Reinforcement Learning)
- **定义**：通过与环境的交互来学习最优的行动策略
- **应用**：游戏AI、自动驾驶、机器人控制
- **算法**：Q-learning、Actor-Critic、Deep Q-Network

## 学习路径建议

### 第一阶段：基础知识
1. **数学基础**：线性代数、概率统计、微积分
2. **编程语言**：Python或R
3. **数据处理**：Pandas、NumPy

### 第二阶段：核心算法
1. **监督学习算法**：线性回归、逻辑回归、决策树
2. **模型评估**：交叉验证、混淆矩阵、ROC曲线
3. **特征工程**：特征选择、特征缩放、特征构造

### 第三阶段：深度学习
1. **神经网络基础**：感知器、多层感知器
2. **深度学习框架**：TensorFlow、PyTorch
3. **高级架构**：CNN、RNN、Transformer

## 实践项目推荐

1. **房价预测**：使用线性回归预测房价
2. **图像分类**：使用CNN对图像进行分类
3. **情感分析**：使用NLP技术分析文本情感
4. **推荐系统**：构建商品推荐算法

## 学习资源

### 在线课程
- Coursera的机器学习课程 (Andrew Ng)
- edX的MIT机器学习入门
- Udacity的机器学习纳米学位

### 书籍推荐
- 《机器学习》- 周志华
- 《Python机器学习》- Sebastian Raschka
- 《深度学习》- Ian Goodfellow

### 实践平台
- Kaggle：数据科学竞赛平台
- Google Colab：免费的Jupyter notebook环境
- GitHub：开源项目和代码分享

机器学习是一个快速发展的领域，需要不断学习和实践。从基础开始，循序渐进，理论与实践相结合，你也可以在AI的世界中找到自己的位置。''',
        'summary': '一篇全面的机器学习入门指南，涵盖了机器学习的基本概念、主要类型、学习路径和实践建议。',
        'author': 'AI研究员',
        'tags': ['机器学习', '人工智能', 'AI', '深度学习', '数据科学']
    },
    {
        'title': 'Git版本控制系统使用指南',
        'content': '''# Git版本控制系统使用指南

Git是目前最流行的分布式版本控制系统，每个开发者都应该掌握的必备工具。

## Git基础概念

### 仓库 (Repository)
Git仓库是项目的完整历史记录，包含所有的文件、提交记录和分支信息。

### 工作区、暂存区、版本库
- **工作区**：实际修改文件的地方
- **暂存区**：临时保存即将提交的修改
- **版本库**：Git存储提交历史的地方

## 基本命令

### 初始化和克隆
```bash
# 初始化新仓库
git init

# 克隆远程仓库
git clone https://github.com/user/repo.git
```

### 基本操作
```bash
# 查看状态
git status

# 添加文件到暂存区
git add filename
git add .  # 添加所有文件

# 提交更改
git commit -m "提交信息"

# 查看提交历史
git log
```

### 分支操作
```bash
# 查看分支
git branch

# 创建分支
git branch new-branch

# 切换分支
git checkout new-branch

# 创建并切换分支
git checkout -b new-branch

# 合并分支
git merge branch-name

# 删除分支
git branch -d branch-name
```

### 远程操作
```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin url

# 推送到远程仓库
git push origin main

# 从远程仓库拉取
git pull origin main
```

## 进阶技巧

### 撤销操作
```bash
# 撤销工作区修改
git checkout -- filename

# 撤销暂存区修改
git reset HEAD filename

# 撤销提交
git reset --soft HEAD~1  # 保留修改
git reset --hard HEAD~1  # 丢弃修改
```

### 标签管理
```bash
# 创建标签
git tag v1.0

# 创建带注释的标签
git tag -a v1.0 -m "版本1.0"

# 推送标签
git push origin v1.0
```

## 最佳实践

### 1. 提交信息规范
- 使用清晰、简洁的提交信息
- 采用统一的格式，如：`类型: 描述`
- 例如：`feat: 添加用户登录功能`

### 2. 分支策略
- **主分支 (main/master)**：稳定的生产版本
- **开发分支 (develop)**：最新的开发版本
- **功能分支 (feature)**：单个功能的开发
- **修复分支 (hotfix)**：紧急bug修复

### 3. 代码审查
- 使用Pull Request进行代码审查
- 确保代码质量和团队协作
- 及时响应和处理审查意见

## 常见问题解决

### 冲突解决
当合并分支时出现冲突，需要手动解决：
1. 打开冲突文件
2. 查找冲突标记 `<<<<<<<`, `=======`, `>>>>>>>`
3. 手动编辑解决冲突
4. 添加并提交解决后的文件

### 找回丢失的提交
```bash
# 查看所有操作记录
git reflog

# 恢复到指定提交
git reset --hard commit-hash
```

Git是一个功能强大的工具，掌握它需要时间和实践。从基础命令开始，逐步学习高级功能，你会发现Git让团队协作变得更加高效。''',
        'summary': '详细的Git版本控制系统使用指南，涵盖了基础概念、常用命令、进阶技巧和最佳实践。',
        'author': '开发工具专家',
        'tags': ['Git', '版本控制', '开发工具', '团队协作']
    },
    {
        'title': '响应式Web设计原理与实践',
        'content': '''# 响应式Web设计原理与实践

随着移动设备的普及，响应式设计成为现代Web开发的必备技能。本文将深入探讨响应式设计的原理和实现方法。

## 什么是响应式设计？

响应式设计是一种让网页能够在不同设备和屏幕尺寸上都能良好显示的设计方法。它通过灵活的网格系统、图片和CSS媒体查询来实现。

## 核心概念

### 1. 流式布局 (Fluid Layout)
使用相对单位（如百分比）而不是固定像素值来定义元素的宽度。

```css
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
}

.column {
    width: 50%;
    float: left;
}
```

### 2. 媒体查询 (Media Queries)
根据设备特性（如屏幕宽度）应用不同的CSS样式。

```css
/* 基础样式 */
.header {
    font-size: 24px;
    padding: 20px;
}

/* 平板设备 */
@media screen and (max-width: 768px) {
    .header {
        font-size: 20px;
        padding: 15px;
    }
}

/* 手机设备 */
@media screen and (max-width: 480px) {
    .header {
        font-size: 18px;
        padding: 10px;
    }
}
```

### 3. 弹性图片 (Flexible Images)
确保图片能够根据容器大小自动缩放。

```css
img {
    max-width: 100%;
    height: auto;
}
```

## 设计断点 (Breakpoints)

常用的响应式断点：

```css
/* Extra small devices (phones, 600px and down) */
@media only screen and (max-width: 600px) {...}

/* Small devices (portrait tablets and large phones, 600px and up) */
@media only screen and (min-width: 600px) {...}

/* Medium devices (landscape tablets, 768px and up) */
@media only screen and (min-width: 768px) {...}

/* Large devices (laptops/desktops, 992px and up) */
@media only screen and (min-width: 992px) {...}

/* Extra large devices (large laptops and desktops, 1200px and up) */
@media only screen and (min-width: 1200px) {...}
```

## CSS Grid 和 Flexbox

### CSS Grid
二维布局系统，适合复杂的网格布局。

```css
.grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}
```

### Flexbox
一维布局系统，适合组件内部的布局。

```css
.flex-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
}

.flex-item {
    flex: 1 1 300px;
    margin: 10px;
}
```

## 移动优先设计 (Mobile First)

从最小屏幕开始设计，然后逐渐增强到更大屏幕。

```css
/* 移动设备样式（基础样式） */
.navigation {
    display: none;
}

.menu-toggle {
    display: block;
}

/* 平板及以上设备 */
@media screen and (min-width: 768px) {
    .navigation {
        display: block;
    }
    
    .menu-toggle {
        display: none;
    }
}
```

## 性能优化

### 1. 图片优化
```html
<!-- 响应式图片 -->
<picture>
    <source media="(max-width: 480px)" srcset="small.jpg">
    <source media="(max-width: 768px)" srcset="medium.jpg">
    <img src="large.jpg" alt="描述">
</picture>

<!-- 使用 srcset 属性 -->
<img src="image.jpg" 
     srcset="image-320w.jpg 320w,
             image-480w.jpg 480w,
             image-800w.jpg 800w"
     sizes="(max-width: 320px) 280px,
            (max-width: 480px) 440px,
            800px"
     alt="描述">
```

### 2. CSS优化
- 使用CSS预处理器（Sass/Less）
- 压缩和合并CSS文件
- 使用关键CSS内联
- 延迟加载非关键CSS

### 3. JavaScript优化
- 条件加载JavaScript
- 使用Intersection Observer API
- 避免阻塞渲染的脚本

## 测试和调试

### 浏览器开发者工具
- Chrome DevTools的设备模拟器
- Firefox的响应式设计模式
- Safari的Web Inspector

### 在线测试工具
- BrowserStack：多设备测试
- Responsinator：快速响应式预览
- Google Mobile-Friendly Test

### 真机测试
- 在实际设备上测试
- 使用不同的网络条件
- 考虑触摸交互

## 最佳实践

1. **内容优先**：确保核心内容在所有设备上都能访问
2. **渐进增强**：从基础功能开始，逐步添加高级特性
3. **性能考虑**：优化加载速度，特别是在移动网络上
4. **可访问性**：确保所有用户都能使用你的网站
5. **用户体验**：在不同设备上提供一致而优秀的体验

响应式设计不仅仅是技术实现，更是一种设计思维。它要求我们从用户的角度出发，考虑他们在不同环境下的需求和体验。''',
        'summary': '全面介绍响应式Web设计的原理、技术实现和最佳实践，帮助开发者创建适配各种设备的网站。',
        'author': '前端设计师',
        'tags': ['响应式设计', '前端开发', 'CSS', 'Web设计', '用户体验']
    }
]

# 预定义的标签数据
DEFAULT_TAGS = [
    {'name': 'Python', 'color': '#3776ab'},
    {'name': '编程', 'color': '#28a745'},
    {'name': '教程', 'color': '#17a2b8'},
    {'name': '入门', 'color': '#ffc107'},
    {'name': 'Web开发', 'color': '#6f42c1'},
    {'name': '技术栈', 'color': '#fd7e14'},
    {'name': '前端', 'color': '#20c997'},
    {'name': '后端', 'color': '#6c757d'},
    {'name': '数据库', 'color': '#e83e8c'},
    {'name': '机器学习', 'color': '#dc3545'},
    {'name': '人工智能', 'color': '#007bff'},
    {'name': 'AI', 'color': '#6610f2'},
    {'name': '深度学习', 'color': '#e83e8c'},
    {'name': '数据科学', 'color': '#20c997'},
    {'name': 'Git', 'color': '#f86c00'},
    {'name': '版本控制', 'color': '#6c757d'},
    {'name': '开发工具', 'color': '#28a745'},
    {'name': '团队协作', 'color': '#17a2b8'},
    {'name': '响应式设计', 'color': '#6f42c1'},
    {'name': 'CSS', 'color': '#1572b6'},
    {'name': 'Web设计', 'color': '#fd7e14'},
    {'name': '用户体验', 'color': '#ffc107'},
]

# 扩展标题模板
TITLE_TEMPLATES = [
    "深入理解{}：从入门到精通",
    "{}开发实战指南",
    "{}最佳实践总结",
    "{}技术栈详解",
    "{}项目经验分享",
    "{}性能优化技巧",
    "{}常见问题解决方案",
    "{}学习路径规划",
    "{}工具使用心得",
    "{}架构设计思考",
    "现代{}开发趋势",
    "{}与人工智能的结合",
    "{}在企业中的应用",
    "{}安全性考虑",
    "{}测试策略详解",
]

TECH_KEYWORDS = [
    "JavaScript", "TypeScript", "React", "Vue.js", "Angular", "Node.js",
    "Python", "Django", "Flask", "FastAPI", "Java", "Spring Boot",
    "Go", "Rust", "PHP", "Laravel", "Ruby", "Rails", "C#", ".NET",
    "Docker", "Kubernetes", "微服务", "云原生", "DevOps", "CI/CD",
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "机器学习", "深度学习", "数据分析", "区块链", "物联网",
    "移动开发", "小程序", "PWA", "性能优化", "架构设计"
]

CONTENT_TEMPLATES = [
    """# {title}

## 概述

{summary}

## 主要特点

1. **高性能**：经过优化的算法和数据结构
2. **易于使用**：简洁的API设计，上手简单
3. **可扩展性**：模块化架构，支持自定义扩展
4. **跨平台**：支持多种操作系统和环境

## 技术实现

### 核心架构

系统采用分层架构设计：
- 表示层：负责用户界面和交互
- 业务层：处理核心业务逻辑
- 数据层：管理数据持久化

### 关键技术

- **前端技术**：HTML5, CSS3, JavaScript ES6+
- **后端技术**：RESTful API, 数据库设计
- **开发工具**：版本控制, 自动化测试, 持续集成

## 最佳实践

1. 遵循设计模式，提高代码可维护性
2. 编写单元测试，确保代码质量
3. 使用代码审查，促进团队协作
4. 持续重构，保持代码整洁

## 总结

这是一个非常有价值的技术分享，希望对大家的学习和工作有所帮助。技术在不断发展，我们也需要保持学习的心态，跟上时代的步伐。

## 参考资源

- 官方文档
- 社区最佳实践
- 开源项目案例
""",
    """# {title}

{summary}

## 背景介绍

在当今快速发展的技术环境中，掌握新技术和工具变得越来越重要。本文将详细介绍相关的核心概念和实际应用。

## 核心概念

### 基础理论

理解基础概念是掌握任何技术的第一步。我们需要从理论层面深入了解其工作原理和设计思想。

### 实际应用

理论联系实际，通过具体的案例和代码示例来加深理解。

```
示例代码将在这里展示
```

## 实战案例

### 项目需求分析

在开始任何项目之前，我们需要：
1. 明确项目目标和范围
2. 分析技术要求和约束
3. 评估资源和时间安排
4. 制定详细的实施计划

### 技术选型

根据项目需求选择合适的技术栈：
- 考虑团队技能水平
- 评估技术成熟度
- 分析社区支持度
- 权衡开发效率

### 实施过程

详细的实施步骤和注意事项，包括：
- 环境搭建
- 核心功能开发
- 测试和调试
- 部署和维护

## 经验总结

通过这个项目，我们学到了很多宝贵的经验：
- 技术选择的重要性
- 团队协作的必要性
- 持续学习的意义
- 用户体验的价值

## 未来展望

技术在不断发展，我们需要保持开放的心态，拥抱变化，持续改进。希望这篇文章能够为大家提供一些有用的参考。
""",
    """# {title}

## 引言

{summary}

## 深入分析

### 技术背景

随着互联网技术的快速发展，新的挑战和机遇不断涌现。我们需要深入理解技术的本质，才能更好地应对各种复杂的问题。

### 问题定义

在实际工作中，我们经常遇到各种技术难题：
- 性能瓶颈
- 可扩展性问题
- 安全隐患
- 维护成本高

### 解决方案

针对这些问题，我们提出了以下解决方案：

1. **性能优化**
   - 算法优化
   - 缓存策略
   - 数据库优化
   - 前端优化

2. **架构改进**
   - 微服务架构
   - 分布式系统
   - 云原生应用
   - 容器化部署

3. **安全加固**
   - 身份认证
   - 数据加密
   - 访问控制
   - 安全监控

## 实践指南

### 环境准备

开始之前，请确保您的开发环境满足以下要求：
- 操作系统版本
- 开发工具安装
- 依赖库配置
- 网络环境设置

### 步骤详解

详细的操作步骤和代码示例，让您能够快速上手。

### 常见问题

在实践过程中可能遇到的问题和解决方法。

## 高级技巧

对于有经验的开发者，我们还提供了一些高级技巧和优化建议。

## 总结与思考

技术学习是一个持续的过程，需要理论学习和实践相结合。希望这篇文章能够对您的技术成长有所帮助。

## 延伸阅读

- 相关技术文档
- 开源项目推荐
- 学习资源链接
"""
]

def create_or_get_tags(tag_names):
    """创建或获取标签"""
    tags = []
    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            # 从默认标签中查找颜色
            color = '#007bff'  # 默认颜色
            for default_tag in DEFAULT_TAGS:
                if default_tag['name'] == tag_name:
                    color = default_tag['color']
                    break
            
            tag = Tag(name=tag_name, color=color)
            db.session.add(tag)
        tags.append(tag)
    
    db.session.commit()
    return tags

def generate_random_article():
    """生成随机文章"""
    # 从模板中随机选择或生成新的
    if random.choice([True, False]) and ARTICLE_TEMPLATES:
        # 50% 概率使用预定义模板
        template = random.choice(ARTICLE_TEMPLATES)
        return template.copy()
    else:
        # 50% 概率生成随机文章
        tech = random.choice(TECH_KEYWORDS)
        title_template = random.choice(TITLE_TEMPLATES)
        content_template = random.choice(CONTENT_TEMPLATES)
        
        title = title_template.format(tech)
        summary = f"这是一篇关于{tech}的技术文章，详细介绍了相关的概念、应用和最佳实践。"
        content = content_template.format(title=title, summary=summary)
        
        # 随机选择标签
        all_tag_names = [tag['name'] for tag in DEFAULT_TAGS]
        tag_count = random.randint(2, 5)
        selected_tags = random.sample(all_tag_names, min(tag_count, len(all_tag_names)))
        
        return {
            'title': title,
            'content': content,
            'summary': summary,
            'author': random.choice(['技术专家', '资深开发者', '架构师', '全栈工程师', '技术博主']),
            'tags': selected_tags
        }

def create_bulk_articles(count, status='draft', with_tags=True):
    """批量创建文章"""
    created_articles = []
    
    print(f"开始创建 {count} 篇文章...")
    
    for i in range(count):
        try:
            # 生成文章数据
            article_data = generate_random_article()
            
            # 创建文章
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                summary=article_data['summary'],
                author=article_data['author'],
                status=status,
                permission=random.choice(['public', 'verify']),
                is_top=random.choice([True, False]) if random.random() < 0.1 else False,  # 10%概率置顶
                view_count=random.randint(0, 1000)
            )
            
            # 如果需要验证权限，添加验证问题
            if article.permission == 'verify':
                article.verify_question = "请输入访问密码"
                article.verify_answer = "123456"
            
            # 随机设置创建时间（最近30天内）
            random_days = random.randint(0, 30)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            article.created_at = datetime.now() - timedelta(
                days=random_days, 
                hours=random_hours, 
                minutes=random_minutes
            )
            article.updated_at = article.created_at
            
            db.session.add(article)
            db.session.flush()  # 获取文章ID
            
            # 添加标签
            if with_tags and 'tags' in article_data:
                tags = create_or_get_tags(article_data['tags'])
                article.tags.extend(tags)
            
            created_articles.append(article)
            
            print(f"创建文章 {i + 1}/{count}: {article.title}")
            
        except Exception as e:
            print(f"创建第 {i + 1} 篇文章时发生错误: {str(e)}")
            db.session.rollback()
            continue
    
    try:
        db.session.commit()
        print(f"成功创建 {len(created_articles)} 篇文章！")
        return created_articles
    except Exception as e:
        print(f"保存文章时发生错误: {str(e)}")
        db.session.rollback()
        return []

def create_default_tags():
    """创建默认标签"""
    print("创建默认标签...")
    created_count = 0
    
    for tag_data in DEFAULT_TAGS:
        existing_tag = Tag.query.filter_by(name=tag_data['name']).first()
        if not existing_tag:
            tag = Tag(name=tag_data['name'], color=tag_data['color'])
            db.session.add(tag)
            created_count += 1
    
    try:
        db.session.commit()
        print(f"成功创建 {created_count} 个标签！")
    except Exception as e:
        print(f"创建标签时发生错误: {str(e)}")
        db.session.rollback()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量创建文章脚本')
    parser.add_argument('count', type=int, nargs='?', default=10, help='要创建的文章数量 (默认: 10)')
    parser.add_argument('--status', choices=['draft', 'published'], default='draft', help='文章状态 (默认: draft)')
    parser.add_argument('--with-tags', action='store_true', help='是否添加标签')
    parser.add_argument('--create-tags', action='store_true', help='是否先创建默认标签')
    
    args = parser.parse_args()
    
    # 从环境变量获取配置，默认为development
    config_name = os.getenv('FLASK_CONFIG', 'development')
    print(f"使用配置环境: {config_name}")
    
    # 创建Flask应用
    app = create_app(config_name)
    
    with app.app_context():
        try:
            # 检查数据库连接
            db.session.execute(text('SELECT 1'))
            print("数据库连接成功")
            
            # 如果指定了创建标签选项，先创建默认标签
            if args.create_tags:
                create_default_tags()
            
            # 创建文章
            articles = create_bulk_articles(
                count=args.count,
                status=args.status,
                with_tags=args.with_tags
            )
            
            if articles:
                print(f"\n批量创建完成!")
                print(f"创建文章数量: {len(articles)}")
                print(f"文章状态: {args.status}")
                print(f"包含标签: {'是' if args.with_tags else '否'}")
                
                # 显示统计信息
                total_articles = Article.query.count()
                published_articles = Article.query.filter_by(status='published').count()
                draft_articles = Article.query.filter_by(status='draft').count()
                total_tags = Tag.query.count()
                
                print(f"\n数据库统计:")
                print(f"总文章数: {total_articles}")
                print(f"已发布: {published_articles}")
                print(f"草稿: {draft_articles}")
                print(f"标签数: {total_tags}")
            else:
                print("没有成功创建任何文章")
                
        except Exception as e:
            print(f"执行过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()