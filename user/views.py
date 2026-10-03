from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth import authenticate,login,logout
from .forms import UserLoginForm,UserRegisterForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import UserInfo

#USER VIEWS

def user_login(request):
    # 用户登录
    if request.method == 'POST':
        user_login_form = UserLoginForm(data=request.POST)
        if user_login_form.is_valid():
            data = user_login_form.cleaned_data
            # 检验账号、密码是否正确匹配数据库
            user = authenticate(username=data['username'], password=data['password'])
            if user:
                # 用户登录
                login(request, user , backend='django.contrib.auth.backends.ModelBackend')
                return redirect("article:list")
            else:
                return HttpResponse("账号或密码输入错误")
        else:
            return HttpResponse("账号或密码输入不合法")
    elif request.method == 'GET':
        user_login_form = UserLoginForm()
        context = { 'form': user_login_form }
        return render(request, 'login_simple.html', context)
    else:
        return HttpResponse("非法请求")

def user_logout(request):
    logout(request)
    # 登出并重定向到文章列表
    return redirect("article:list")

def user_register(request):
    # 用户注册，逻辑与用户登录相似
    if request.method == 'POST':
        user_register_form = UserRegisterForm(data=request.POST)
        if user_register_form.is_valid():
            new_user = user_register_form.save(commit=False)
            # 设置密码
            new_user.set_password(user_register_form.cleaned_data['password'])
            new_user.save()
            # 登录
            login(request, new_user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("article:list")
        else:
            return HttpResponse("用户输入信息有误")
    elif request.method == 'GET':
        user_register_form = UserRegisterForm()
        context = { 'form': user_register_form }
        return render(request, 'register_simple.html', context)
    else:
        return HttpResponse("非法请求")

#删除用户需要用户登录
@login_required(login_url='/user/login/')
def user_delete(request, id):
    if request.method == 'POST':
        user = User.objects.get(id=id)
        #再次验证用户登录id
        if request.user == user:
            #退出登录，删除用户
            logout(request)
            user.delete()
            return redirect("article:list")
        else:
            return HttpResponse("无权删除此用户")
    else:
        return HttpResponse("仅接受POST请求")

# 编辑用户信息
@login_required(login_url='/user/login/')
def profile_edit(request, id):
    user = User.objects.get(id=id)

    if UserInfo.objects.filter(user_id=id).exists():
        profile = UserInfo.objects.get(user_id=id)
    else:
        profile = UserInfo.objects.create(user=user)

    if request.method == 'POST':
        #验证是否为本用户
        if request.user != user:
            return HttpResponse("你没有修更改此用户资料的权限")
        profile_form = ProfileForm(request.POST, request.FILES)
        if profile_form.is_valid():
            profile_cd = profile_form.cleaned_data
            profile.phone = profile_cd['phone']
            profile.bio = profile_cd['bio']
            #如果 request.FILES 存在文件，则保存
            if 'avatar' in request.FILES:
                profile.avatar = profile_cd["avatar"]
            profile.save()
            #重定向回用户详细信息
            return redirect("user:edit", id=id)
        else:
            return HttpResponse("输入非法")

    elif request.method == 'GET':
        profile_form = ProfileForm()
        context = { 'profile_form': profile_form, 'profile': profile, 'user': user }
        return render(request, 'edit.html', context)
    else:
        return HttpResponse("非法请求")