# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Stock

class StocksConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('stocks', self.channel_name)
        await self.accept()
        await self.send_stock_data()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('stocks', self.channel_name)

    async def send_stock_data(self):
        stocks = await sync_to_async(list)(Stock.objects.all().order_by('symbol'))
        
        stock_data = [
            {
                'symbol': stock.symbol,
                'name': stock.name,
                'price': str(stock.price),
                'original_price': str(stock.original_price),
                'price_change': str(stock.price_change),
                'state': stock.state
            }
            for stock in stocks
        ]
        
        await self.send(text_data=json.dumps(stock_data))

    async def send_new_data(self, event):
        new_data = event['text']
        await self.send(text_data=json.dumps(new_data))
