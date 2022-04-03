from django.db import models
from django_quill.fields import QuillField

# Create your models here.


class Content (models.Model):
    name = models.CharField(max_length=60, default='')
    content = QuillField()

    def __str__ (self):
        return self.name
