from django.contrib import admin

from .models import Stock, Watchlist, Notification, UserProfile

# Register each model so it appears in the admin interface
admin.site.register(Stock)
admin.site.register(Watchlist)
admin.site.register(Notification)
admin.site.register(UserProfile)

