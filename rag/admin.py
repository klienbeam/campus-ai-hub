from django.contrib import admin
from .models import ArticleVector, QASession


@admin.register(ArticleVector)
class ArticleVectorAdmin(admin.ModelAdmin):
    list_display = ['article_id', 'chunk_index', 'vector_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['article_id', 'chunk_text']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QASession)
class QASessionAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer', 'created_at']
    list_filter = ['created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at']