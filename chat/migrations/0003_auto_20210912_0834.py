# Generated by Django 3.2.7 on 2021-09-12 11:34

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0002_chatroom_users'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatroom',
            name='users',
        ),
        migrations.AddField(
            model_name='chatroom',
            name='users',
            field=models.ManyToManyField(null=True, to=settings.AUTH_USER_MODEL),
        ),
    ]