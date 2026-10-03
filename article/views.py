from django.contrib.auth.mixins import LoginRequiredMixin
import os
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from .models import Article, ArticleColumn, CampusLink
from .forms import ArticlePostForm
import markdown
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
from comment.forms import CommentForm
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_http_methods
import re
from rag.service_loader import get_rag_service
from django.conf import settings
from pathlib import Path
from datetime import datetime
from .services_import import import_from_oa_articles
from .services_oa_fetch import fetch_latest_oa_articles
import json

from openai import OpenAI

def index(request):
    return render(request, "index.html")

#文章总结
class ArticleSumView(View):
    def __init__(self):
        super().__init__()
        self.context = {}
        self.client = None

    # 在文章列表处新建一个按钮用来触发这个get请求，并跳转到问答网页
    def get(self, request, article_id):
        response_summary = self.submit("请你总结一下文章内容：", article_id)
        self.context["summary"] = response_summary   # 包装为字典
        return render(request, "article_summary.html", self.context)

    # 用户在问答网页通过post请求提问，传送到下面这个函数
    def post(self, request, article_id):
        response_summary = self.submit("请你总结一下文章内容：", article_id)
        self.context["summary"] = response_summary

        message = request.POST.get("question")  # 修正字段名称
        response_text = self.submit(message, article_id)
        self.context["response"] = response_text
        # context = {"response": response_text}  # 包装为字典
        return render(request, "article_summary.html", self.context)


    def submit(self, inquire, article_id):
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            return 'AI 功能未配置。请设置 DEEPSEEK_API_KEY 后重试。'
        if self.client is None:
            self.client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')
        article = Article.objects.get(id=article_id)
        context = "请你根据以下文章内容进行回答：" + article.content
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": inquire},
            ],
            stream=False
        )
        return response.choices[0].message.content


class ArticleListView(View):

    def get(self, request):
        order = request.GET.get('order')
        column = request.GET.get('column')
        tag = request.GET.get('tag')

        article_list,search = self.search(request)
        if column is not None and column.isdigit():
            article_list = article_list.filter(column=column)
        if tag and tag != 'None':
            article_list = article_list.filter(tags__name__in=[tag])
        if order == 'total_views':
            article_list = article_list.order_by('-total_views')
        paginator = Paginator(article_list, 3)
        page = request.GET.get('page')
        articles = paginator.get_page(page)

        # 打包数据
        context = {
            'articles': articles,
            'order': order,
            'search': search,
            'column': column,
            'tag': tag,
        }
        return render(request, 'list.html', context)

    def search(self,request):
        search = request.GET.get('search')

        article_list = Article.objects.all()

        if search:
            article_list = article_list.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        else:
            search = ''

        return article_list,search

#文章详细
class ArticleDetailView(View):
    def get(self, request, article_id):
        article = Article.objects.get(id=article_id)

        article.total_views += 1
        article.save(update_fields=['total_views'])

        comments = Comment.objects.filter(article=article_id)
        # 引入评论表单
        comment_form = CommentForm()

        # 将markdown语法渲染成html样式
        md = markdown.Markdown(
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
            ]
        )

        article.content = md.convert(article.content)

        context = {"article": article,
                   'toc': md.toc,
                   'comments': comments,
                   'comment_form': comment_form,
                   }
        return render(request, "detail.html", context)

class ArticleDeleteView(View):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def post(self, request, article_id):
        article = Article.objects.get(id=article_id)
        if request.user != article.author:
            return HttpResponse("抱歉，你没有修改这篇文章的权限。")
        article.delete()
        # 同时从向量数据库中删除该文章
        service = get_rag_service()
        if service is not None:
            service.delete_article(article.title)
        return redirect("article:list")

    def get(self):
        return HttpResponse("仅允许post请求")


class ArticleNewPageView(View):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request):
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = {'article_post_form': article_post_form, 'columns': columns}
        return render(request, 'newpage.html', context)

    def post(self,request):
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit=False)
            new_article.author = User.objects.get(id=request.user.id)
            column_id = request.POST.get('column')
            if column_id and column_id != 'none':
                new_article.column = ArticleColumn.objects.get(id=column_id)
            if request.FILES.get('avatar'):
                new_article.avatar = request.FILES.get('avatar')
            new_article.save()
            article_post_form.save_m2m()
            content = new_article.content
            title = new_article.title
            # 使用关键字参数（推荐）
            service = get_rag_service()
            if service is not None:
                service.add_article(article_title=title, article_content=content)
 
            return redirect("article:list")
        else:
            return HttpResponse("内容填写有误")



class ArticleUpdateView(LoginRequiredMixin,View):
    login_url = '/user/login/'
    redirect_field_name = 'next'

    def get(self, request, article_id):
        article = Article.objects.get(id=article_id)
        if request.user != article.author:
            return HttpResponse("用户没有修改文章的权限")
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        # 提取旧内容
        context = {'article': article,
                   'article_post_form': article_post_form,
                   'columns': columns,
                   'tags': ','.join([x for x in article.tags.names()]),
                   }
        return render(request, 'update.html', context)

    def post(self, request, article_id):
        article = Article.objects.get(id=article_id)
        if request.user != article.author:
            return HttpResponse("用户没有修改文章的权限")
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            article.title = request.POST['title']
            article.content = request.POST['content']
            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            if request.FILES.get('avatar'):
                article.avatar = request.FILES.get('avatar')
            article.tags.set(request.POST.get('tags').split(','), clear=True)

            article.save()
            # 更新向量数据库中的文章内容
            content = article.content
            title = article.title
            service = get_rag_service()
            if service is not None:
                service.update_article(article_title=title, new_content=content)
            return redirect("article:detail", article_id=article_id)
        else:
            return HttpResponse("内容填写有误")



#点赞+1
class IncreaseLikesView(View):
    def post(self, request, *args, **kwargs):
        article = Article.objects.get(id=kwargs.get('id'))
        article.likes += 1
        article.save()
        return HttpResponse('success')


# 获取最新文章API
@require_http_methods(["GET"])
def latest_articles_api(request):
    """获取最新文章API"""
    try:
        articles = Article.objects.all().order_by('-created')[:6]
        articles_data = []
        
        for article in articles:
            # 清理HTML标签，生成摘要
            content = re.sub('<.*?>', '', article.content)
            excerpt = content[:100] + '...' if len(content) > 100 else content
            
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'excerpt': excerpt,
                'author': article.author.username,
                'created': article.created.strftime('%Y-%m-%d'),
                'views': article.total_views,
                'url': article.get_absolute_url()
            })
        
        return JsonResponse({'articles': articles_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def import_oa_articles(request):
    """从 oa_articles 文件夹批量导入 .txt 到文章库（兼容多种目录层级）"""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}
    limit = payload.get('limit')
    skip_rag = payload.get('skip_rag', False)
    auto_fetch = payload.get('auto_fetch', False)
    try:
        if limit is not None:
            limit = int(limit)
            if limit <= 0:
                limit = None
    except (ValueError, TypeError):
        limit = None

    fetch_result = None
    if auto_fetch:
        fetch_count = limit or 50
        try:
            fetch_result = fetch_latest_oa_articles(target_count=fetch_count)
        except Exception as e:
            fetch_result = {'error': str(e)}
        # 如果自动抓取了新文件，只导入最近抓取的文件（避免导入所有旧文件）
        only_recent = True
    else:
        only_recent = False

    result = import_from_oa_articles(
        preferred_author=request.user,
        limit=limit,
        skip_rag=bool(skip_rag),
        only_recent=only_recent,
        recent_minutes=10,  # 只导入最近10分钟内创建的文件
    )
    if fetch_result:
        result['fetch'] = fetch_result
    status = 200 if 'error' not in result else 400
    return JsonResponse(result, status=status)


def campus_nav(request):
    links = []
    if request.user.is_authenticated:
        links = CampusLink.objects.filter(user=request.user)
    context = {'custom_links': links}
    return render(request, "campus_nav.html", context)


@login_required
@require_http_methods(["POST"])
def campus_link_add(request):
    title = request.POST.get('title', '').strip()
    url = request.POST.get('url', '').strip()
    style = request.POST.get('style', 'btn-outline-secondary').strip() or 'btn-outline-secondary'
    if not title or not url:
        return JsonResponse({'error': '标题与网址必填'}, status=400)
    if len(title) > 64:
        title = title[:64]
    CampusLink.objects.create(user=request.user, title=title, url=url, style=style)
    return redirect('article:campus')


@login_required
@require_http_methods(["POST"])
def campus_link_delete(request, link_id):
    try:
        link = CampusLink.objects.get(id=link_id, user=request.user)
    except CampusLink.DoesNotExist:
        return JsonResponse({'error': '链接不存在或无权限'}, status=404)
    link.delete()
    return redirect('article:campus')
