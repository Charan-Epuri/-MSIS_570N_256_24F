import os
import random
import requests
import django
import time
from datetime import timedelta
from django.utils.timezone import now
import yfinance as yf
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.forms.models import model_to_dict
from stocks.models import Stock, Watchlist, Notification, UserProfile


# Initialize Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_project.settings")
django.setup()


TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"


@shared_task
def clear_old_notifications(days=1):
    """
    Clears notifications older than a specified number of days.
    Default is 1 day.
    """
    cutoff_date = now() - timedelta(days=days)
    deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff_date).delete()
    print(f"Deleted {deleted_count} old notifications.")


# Function to send a message to Telegram
def send_telegram_message(chat_id, message):
    data = {
        "chat_id": chat_id,
        "text": message,
    }
    try:
        response = requests.post(TELEGRAM_API_URL, data=data)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}, Response: {response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")



# Default stock symbols for monitoring
DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "FB", "NVDA", "BRK-B", "JPM", "JNJ", "UNH", "V", "PG", "HD",
    "MA", "BAC", "DIS", "PFE", "XOM", "KO", "CSCO", "CMCSA", "INTC", "NFLX", "PEP", "VZ", "MRK", "ABT",
    "AVGO", "T"
]



# Celery task to fetch stock data periodically and update users' dashboards
@shared_task
def get_stocks_data(stocks_to_monitor=None):
    """
    Fetch stock data, update the database, and send Telegram notifications for relevant stock updates.
    """
    channel_layer = get_channel_layer()
    symbols = stocks_to_monitor or DEFAULT_SYMBOLS
    iteration = 1

    # Define Telegram API function inside this task
    def send_telegram_message(chat_id, message):
        data = {
            "chat_id": chat_id,
            "text": message,
        }
        try:
            response = requests.post(TELEGRAM_API_URL, data=data)
            if response.status_code == 200:
                print(f"Message sent to Telegram chat {chat_id} successfully!")
            else:
                print(f"Failed to send message. Status code: {response.status_code}, Response: {response.json()}")
        except Exception as e:
            print(f"An error occurred while sending a Telegram message: {e}")

    while True:
        print(f"\n--- Iteration {iteration} ---")
        stocks = []

        for symbol in symbols:
            stock, created = Stock.objects.get_or_create(symbol=symbol, defaults={'name': symbol})

            ticker = yf.Ticker(symbol)
            info = ticker.info
            original_price = info.get('currentPrice')
            if original_price is None:
                print(f"Warning: currentPrice not available for {symbol}")
                continue

            if created or stock.original_price == 0:
                stock.original_price = original_price
                stock.price = stock.original_price

            price_change = round(random.uniform(-1.5, 1.5), 2)
            new_price = stock.original_price + price_change
            stock.price_change = new_price - stock.original_price
            stock.price = round(new_price, 2)

            stock.state = 'raise' if price_change > 0 else 'fall' if price_change < 0 else 'same'

            stock.save()
            print(f"Saved data for {symbol} - Original Price: {stock.original_price}, Current Price: {stock.price}, Price Change: {stock.price_change}")

            stock_dict = model_to_dict(stock)
            stock_dict.update({
                'state': stock.state,
                'price': stock.price,
                'original_price': stock.original_price,
                'price_change': stock.price_change,
                'name': stock.name
            })

            stocks.append(stock_dict)

            # Process watchlists and send Telegram notifications
            watchlists = Watchlist.objects.filter(stock=stock)
            for watchlist in watchlists:
                if (stock.price >= watchlist.price_threshold and stock.price_change > 0) or \
                   (stock.price <= watchlist.price_threshold and stock.price_change < 0):
                    message = f"The price of {stock.symbol} is now ${stock.price}, crossing your threshold of ${watchlist.price_threshold}."
                    Notification.objects.create(user=watchlist.user, message=message)

                    # Check if the user has a Telegram chat ID and send a message
                    try:
                        user_profile = UserProfile.objects.get(user=watchlist.user)
                        chat_id = user_profile.telegram_chat_id

                        if chat_id:
                            send_telegram_message(chat_id, message)
                        else:
                            print(f"No Telegram chat ID for user {watchlist.user.username}")
                    except UserProfile.DoesNotExist:
                        print(f"UserProfile not found for user {watchlist.user.username}")

        # Send stock data updates via WebSocket
        async_to_sync(channel_layer.group_send)(
            'stocks',
            {
                'type': 'send_new_data',
                'text': stocks
            }
        )

        iteration += 1
        # time.sleep(60)




# Celery task to send pending notifications to users on Telegram
@shared_task
def send_telegram_notifications():
    pending_notifications = Notification.objects.filter(status='pending')

    for notification in pending_notifications:
        try:
            user_profile = UserProfile.objects.get(user=notification.user)
            chat_id = user_profile.telegram_chat_id

            if chat_id:
                send_telegram_message(chat_id, notification.message)
                notification.status = 'sent'
                notification.save()
                print("Sent Notification")
            else:
                print(f"No Telegram chat ID for user {notification.user.username}")

        except UserProfile.DoesNotExist:
            print(f"UserProfile not found for user {notification.user.username}")
