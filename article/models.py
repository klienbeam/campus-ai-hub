from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager
from PIL import Image
class ArticleColumn(models.Model):
    #用于标记栏目
    title = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Article(models.Model):
    #文章数据
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='article/%Y%m%d/', blank=True)

    column = models.ForeignKey(
        ArticleColumn,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='article'
    )
    tags = TaggableManager(blank=True)

    title = models.CharField(max_length=64)
    content = models.TextField()

    total_views = models.PositiveIntegerField(default=0)

    likes = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    last_updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created',]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article:detail', args=[self.id])

    def save(self, *args, **kwargs):
        #重写这个方法，用于保存图片
        article = super(Article, self).save(*args, **kwargs)

        if self.avatar and not kwargs.get('update_fields'):
            image = Image.open(self.avatar)
            (x, y) = image.size
            new_x = 400
            new_y = int(new_x * (y / x))
            resized_image = image.resize((new_x, new_y), Image.LANCZOS)
            resized_image.save(self.avatar.path)

        return article

    def was_created_recently(self):
        #标记文章时候是最近创建的
        times = timezone.now() - self.created

        if times.days == 0 and times.seconds >= 0 and times.seconds < 60:
            return True
        else:
            return False


class CampusLink(models.Model):
    # 校内导航的个人自定义链接
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=64)
    url = models.URLField(max_length=512)
    style = models.CharField(max_length=32, blank=True, default='btn-outline-secondary')
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.title} - {self.url}'