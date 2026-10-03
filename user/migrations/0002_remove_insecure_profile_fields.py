from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(model_name='userinfo', name='UID'),
        migrations.RemoveField(model_name='userinfo', name='username'),
        migrations.RemoveField(model_name='userinfo', name='password'),
        migrations.RemoveField(model_name='userinfo', name='email'),
    ]
