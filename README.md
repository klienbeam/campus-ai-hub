# Campus AI Hub · 校园智能信息平台

基于 Django 的校园信息聚合与协作平台，整合文章发布、分类检索、树形评论、通知、个性化校园导航和可选的 RAG 问答。项目可以先以轻量博客模式运行，再按需启用 DeepSeek 与本地向量库。

## 核心功能

- 文章发布、编辑、标签、栏目、全文搜索与浏览量统计
- 用户注册登录、资料编辑与权限校验
- 多级评论、回复通知和未读消息
- 校园链接导航与 OA 公告批量导入
- 可选的 DeepSeek 文章总结与 Chroma RAG 问答
- SQLite 开箱即用，也支持通过环境变量连接 MySQL

## 快速开始

建议使用 Python 3.10 或更高版本。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

默认访问地址为 `http://127.0.0.1:8000/`。开发环境使用 SQLite，邮件会输出到终端，不需要数据库或 SMTP 账号。

> `.env` 文件不会被 Git 跟踪。项目本身不自动读取 `.env`；可由 IDE、部署平台或 shell 注入其中的变量。

## 启用 AI / RAG

AI 功能默认延迟加载，因此未安装模型依赖时不影响文章、评论等核心功能。

```bash
pip install -r requirements-ai.txt
set DEEPSEEK_API_KEY=your_key
python manage.py init_rag
```

首次初始化会下载 `BAAI/bge-small-zh-v1.5`。可以通过 `EMBEDDING_MODEL` 更换嵌入模型。向量库、模型缓存和 API Key 都不会提交到仓库。

## 质量检查

```bash
python manage.py check
python manage.py test
```

## 安全说明

- Django 密钥、数据库密码、邮箱授权码和模型 API Key 全部通过环境变量提供
- 用户密码仅由 Django 的认证系统哈希保存，资料表不重复保存密码
- 生产环境请设置强随机 `DJANGO_SECRET_KEY`、关闭 `DJANGO_DEBUG` 并限制 `DJANGO_ALLOWED_HOSTS`
- OA 抓取功能仅应用于有权访问和再使用的公开内容，请遵守来源站点规则

## 目录结构

```text
article/             文章、搜索、OA 导入与校园导航
comment/             树形评论
notice/              消息通知
rag/                 可选的 RAG 问答和向量索引
user/                认证与个人资料
blog_site_django/    项目配置与路由
```
