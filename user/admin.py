from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserInfo

#定义一个行内admin
class ProfileInline(admin.StackedInline):
    model = UserInfo
    can_delete = False
    verbose_name_plural = 'User'

#将profile与user绑定
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

#注册User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)