# Generated by Django 3.1.5 on 2021-05-31 17:26

from django.db import migrations, models
import django_quill.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', django_quill.fields.QuillField()),
            ],
        ),
    ]
