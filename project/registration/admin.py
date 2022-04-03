from django.contrib import admin

from .models import Family, Record, CAF, Health, Sibling, SiblingChild

# Register your models here.

admin.site.register(Family)
admin.site.register(CAF)
admin.site.register(Health)
admin.site.register(Record)
admin.site.register(Sibling)
admin.site.register(SiblingChild)
