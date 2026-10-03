from django.urls import path
from . import views as article_views
# article部分的url表
app_name = 'article'

urlpatterns = [
    path("index/", article_views.index,name = 'index'),
    path("qaa/<int:article_id>/", article_views.ArticleSumView.as_view(), name ='qaa'),
    path("list/", article_views.ArticleListView.as_view(), name ='list'),
    path("detail/<int:article_id>/", article_views.ArticleDetailView.as_view(),name='detail'),
    path("newpage/", article_views.ArticleNewPageView.as_view(),name = 'newpage'),
    path('delete/<int:article_id>/', article_views.ArticleDeleteView.as_view(), name='article_delete'),
    path('update/<int:article_id>/', article_views.ArticleUpdateView.as_view(), name='article_update'),
    path('increase-likes/<int:id>/',article_views.IncreaseLikesView.as_view(),name='increase_likes'),
    path('api/latest/', article_views.latest_articles_api, name='latest_articles_api'),
    path('import_oa/', article_views.import_oa_articles, name='import_oa'),
    path("campus/", article_views.campus_nav, name="campus"),
    path("campus_links/add/", article_views.campus_link_add, name="campus_link_add"),
    path("campus_links/delete/<int:link_id>/", article_views.campus_link_delete, name="campus_link_delete"),
]