# Generated by Django 3.1.5 on 2021-04-07 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('params', '0002_auto_20210406_1921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]