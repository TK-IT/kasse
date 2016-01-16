# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-16 16:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_time', models.DateTimeField(auto_now_add=True)),
                ('fbid', models.CharField(max_length=50)),
                ('text', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.CharField(blank=True, max_length=100)),
                ('app_secret', models.CharField(blank=True, max_length=100)),
                ('app_access_token', models.TextField(blank=True)),
                ('app_access_token_expiry', models.DateTimeField(blank=True, null=True)),
                ('user_access_token', models.TextField(blank=True)),
                ('user_access_token_expiry', models.DateTimeField(blank=True, null=True)),
                ('page_access_token', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_time', models.DateTimeField(auto_now_add=True)),
                ('fbid', models.CharField(max_length=50)),
                ('text', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='news.Post'),
        ),
    ]
