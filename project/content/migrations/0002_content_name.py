# Generated by Django 3.2.3 on 2021-05-31 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='name',
            field=models.TextField(default='', max_length=60),
        ),
    ]