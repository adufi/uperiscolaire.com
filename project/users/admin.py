from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserAuth)
admin.site.register(UserEmail)
admin.site.register(UserPhone)
admin.site.register(UserAddress)
