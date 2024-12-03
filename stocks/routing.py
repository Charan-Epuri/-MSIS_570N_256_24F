from django.urls import path
from .consumers import StocksConsumer

ws_urlpatterns = [
    path('ws/stocks/', StocksConsumer.as_asgi())  # Update path and consumer name
]
