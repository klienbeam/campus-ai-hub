from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ArticleVector(models.Model):
    """文章向量存储模型"""
    article_id = models.PositiveIntegerField(verbose_name="文章ID")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    article = GenericForeignKey('content_type', 'article_id')
    
    chunk_text = models.TextField(verbose_name="文本块内容")
    chunk_index = models.PositiveIntegerField(verbose_name="块索引")
    vector_id = models.CharField(max_length=255, unique=True, verbose_name="向量ID")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "文章向量"
        verbose_name_plural = "文章向量"
        unique_together = ['article_id', 'chunk_index']
    
    def __str__(self):
        return f"文章{self.article_id} - 块{self.chunk_index}"


class QASession(models.Model):
    """问答会话记录"""
    question = models.TextField(verbose_name="问题")
    answer = models.TextField(verbose_name="回答")
    related_articles = models.JSONField(default=list, verbose_name="相关文章ID列表")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "问答会话"
        verbose_name_plural = "问答会话"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."