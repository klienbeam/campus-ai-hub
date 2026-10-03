from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

#用户数据类
class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # 认证信息由 Django User 模型安全管理，此处只保存扩展资料。
    phone = models.CharField(max_length=32,blank=True)
    #个人简介
    bio = models.TextField(max_length=500, blank=True)
    #头像
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)

    def __str__(self):
        return 'user {}'.format(self.user.username)

