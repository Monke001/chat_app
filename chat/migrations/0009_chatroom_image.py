# Generated by Django 3.2.7 on 2021-09-18 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_alter_chatroom_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='image',
            field=models.ImageField(blank=True, default='img_room/default.gif', upload_to='img_room/'),
        ),
    ]
