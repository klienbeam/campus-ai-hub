from django import forms
from .models import UserInfo
from django.contrib.auth.models import User


# 登录表单
class UserLoginForm(forms.Form):
    username = forms.CharField(label='用户名', widget=forms.TextInput(attrs={'placeholder': '请输入用户名'}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput(attrs={'placeholder': '请输入密码'}))

#用户注册表单
class UserRegisterForm(forms.ModelForm):
    #两遍密码
    username = forms.CharField(label='用户名', widget=forms.TextInput(attrs={'placeholder': '请输入用户名'}))
    email = forms.EmailField(label='邮箱', widget=forms.EmailInput(attrs={'placeholder': '请输入邮箱地址'}, ))
    password = forms.CharField(label='密码', widget=forms.PasswordInput(attrs={'placeholder': '请输入密码'}))
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput(attrs={'placeholder': '请再次输入密码'}))

    class Meta:
        model = User
        fields = ('username', 'email')

    #检查两次密码是否一致
    def clean_password2(self):
        data = self.cleaned_data
        if data.get('password') == data.get('password2'):
            return data.get('password')
        else:
            raise forms.ValidationError("密码输入不一致")

#用户扩展信息表单
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ('phone', 'avatar', 'bio')

#重置密码表单
class RecoveryForm(forms.Form):
    email = forms.EmailField(
        widget=forms.TextInput(attrs={'placeholder': '请输入您的邮箱'}),
        label='邮箱'  # 可选，定义字段标签
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '请输入新密码'}),
        label='新密码'  # 可选
    )
