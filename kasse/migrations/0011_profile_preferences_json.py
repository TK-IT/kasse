# Generated by Django 2.2.3 on 2019-07-27 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0010_contest_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='preferences_json',
            field=models.TextField(blank=True, null=True),
        ),
    ]
