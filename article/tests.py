from django.test import TestCase

import datetime
from django.utils import timezone
from article.models import Article
from django.contrib.auth.models import User


class ArticlePostModelTests(TestCase):

    def test_was_created_recently_with_future_article(self):
        # 若文章创建时间为未来，返回 False
        author = User.objects.create_user(username='user', password='test_password')

        future_article = Article(
            author=author,
            title='test',
            content='test',
            created=timezone.now() + datetime.timedelta(days=30)
            )

        self.assertIs(future_article.was_created_recently(), False)

        def was_created_recently(self):
            times = timezone.now() - self.created

            if times.days == 0 and times.seconds >= 0 and times.seconds < 60:
                return True
            else:
                return False

    def test_was_created_recently_with_seconds_before_article(self):
        # 若文章创建时间为 1 分钟内，返回 True
        author = User.objects.create_user(username='user1', password='test_password')
        seconds_before_article = Article(
            author=author,
            title='test1',
            content='test1',
            created=timezone.now() - datetime.timedelta(seconds=45)
        )
        self.assertIs(seconds_before_article.was_created_recently(), True)

    def test_was_created_recently_with_hours_before_article(self):
        # 若文章创建时间为几小时前，返回 False
        author = User.objects.create_user(username='user2', password='test_password')
        hours_before_article = Article(
            author=author,
            title='test2',
            content='test2',
            created=timezone.now() - datetime.timedelta(hours=3)
        )
        self.assertIs(hours_before_article.was_created_recently(), False)

    def test_was_created_recently_with_days_before_article(self):
        # 若文章创建时间为几天前，返回 False
        author = User.objects.create_user(username='user3', password='test_password')
        months_before_article = Article(
            author=author,
            title='test3',
            content='test3',
            created=timezone.now() - datetime.timedelta(days=5)
        )
        self.assertIs(months_before_article.was_created_recently(), False)
