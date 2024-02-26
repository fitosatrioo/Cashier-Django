from django.contrib import admin
from .models import Gun, Order, Payment

admin.site.register(Gun)
admin.site.register(Order)
admin.site.register(Payment)
