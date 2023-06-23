from django.contrib import admin

from .models import *

admin.site.register(Store)
admin.site.register(Product)
admin.site.register(Stock)
admin.site.register(Supplier)
admin.site.register(Sale)
admin.site.register(Purchase)
