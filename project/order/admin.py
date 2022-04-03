from django.contrib import admin

from .models import Order, Ticket, OrderMethod, OrderStatus, TicketStatus

# Register your models here.

admin.site.register(Order)
admin.site.register(Ticket)
admin.site.register(OrderMethod)
admin.site.register(OrderStatus)
admin.site.register(TicketStatus)
