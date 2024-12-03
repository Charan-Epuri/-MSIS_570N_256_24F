from django.shortcuts import render, redirect
import yfinance as yf
import pandas as pd
import json 
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Stock, Watchlist, Notification, UserProfile
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import plotly.graph_objs as go
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')  # Redirect to the homepage after successful signup
        else:
            print("Form errors:", form.errors)  # Log errors for debugging
            return render(request, 'signup.html', {'form': form, 'errors': form.errors})
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        telegram_chat_id = request.POST.get('telegram_chat_id')
        
        # Update user's email
        request.user.email = email
        request.user.save()
        
        # Update or create UserProfile with the Telegram Chat ID
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.telegram_chat_id = telegram_chat_id
        user_profile.save()
        
        return redirect('profile')  # Redirect back to the profile page
    
    # Render the profile page with the current user data
    return render(request, 'profile.html', {'user': request.user})


@login_required
def index(request):
    return render(request, 'index.html')

def stock_detail(request, symbol):
    stock_data = yf.Ticker(symbol)
    historical = stock_data.history(period="1mo")

    # Collect data for the chart
    price_data = {
        'dates': historical.index.strftime('%Y-%m-%d').tolist(),
        'prices': historical['Close'].tolist()
    }
    
    # Convert price_data to JSON format for the template
    price_data_json = json.dumps(price_data)

    # Stock details with more attributes and checked field names
    context = {
        'stock': {
            'symbol': symbol,
            'name': stock_data.info.get('longName', 'N/A'),
            'short_name': stock_data.info.get('shortName', 'N/A'),
            'current_price': stock_data.info.get('currentPrice', 'N/A'),
            'market_cap': stock_data.info.get('marketCap', 'N/A'),
            'pe_ratio': stock_data.info.get('trailingPE', 'N/A'),
            'forward_pe_ratio': stock_data.info.get('forwardPE', 'N/A'),
            'dividend_yield': stock_data.info.get('dividendYield', 'N/A'),
            'dividend_rate': stock_data.info.get('dividendRate', 'N/A'),
            'beta': stock_data.info.get('beta', 'N/A'),
            'day_high': stock_data.info.get('dayHigh', 'N/A'),
            'day_low': stock_data.info.get('dayLow', 'N/A'),
            'fifty_two_week_high': stock_data.info.get('fiftyTwoWeekHigh', 'N/A'),
            'fifty_two_week_low': stock_data.info.get('fiftyTwoWeekLow', 'N/A'),
            'volume': stock_data.info.get('volume', 'N/A'),
            'average_volume': stock_data.info.get('averageVolume', 'N/A'),
            'total_cash': stock_data.info.get('totalCash', 'N/A'),
            'total_debt': stock_data.info.get('totalDebt', 'N/A'),
            'gross_margin': stock_data.info.get('grossMargins', 'N/A'),
            'operating_margin': stock_data.info.get('operatingMargins', 'N/A'),
            'profit_margin': stock_data.info.get('profitMargins', 'N/A'),
            'return_on_assets': stock_data.info.get('returnOnAssets', 'N/A'),
            'return_on_equity': stock_data.info.get('returnOnEquity', 'N/A'),
            'target_high_price': stock_data.info.get('targetHighPrice', 'N/A'),
            'target_low_price': stock_data.info.get('targetLowPrice', 'N/A'),
            'recommendation_key': stock_data.info.get('recommendationKey', 'N/A'),
        },
        'price_data': price_data_json
    }

    return render(request, 'detail.html', context)

def get_sp500_symbols():
    """Fetch S&P 500 company symbols and names from Wikipedia."""
    # URL for S&P 500 companies on Wikipedia
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    # Use pandas to read the table
    sp500_table = pd.read_html(url)
    sp500_data = sp500_table[0][['Symbol', 'Security']]  # Extracting Symbol and Security columns
    # Convert to dictionary format for easy access to symbol-name pairs
    return sp500_data.set_index('Symbol')['Security'].to_dict()

# Fetch symbols and names dynamically for stock selection
ALL_SYMBOLS = get_sp500_symbols()

def select_stocks(request):
    if request.method == 'POST':
        selected_stocks = request.POST.getlist('stocks')
        # Redirect to the monitoring page with selected stocks as a query parameter
        return redirect(reverse('monitor_stocks') + f"?stocks={','.join(selected_stocks)}")
    return render(request, 'stock_selection.html', {'symbols': ALL_SYMBOLS})

@login_required
def user_dashboard(request):
    watchlist = Watchlist.objects.filter(user=request.user)
    # Prepare watchlist data with current prices
    watchlist_data = []
    for item in watchlist:
        try:
            stock_data = yf.Ticker(item.stock.symbol)
            current_price = stock_data.info.get('currentPrice', 'N/A')
        except Exception as e:
            current_price = 'N/A'
        
        watchlist_data.append({
            'symbol': item.stock.symbol,
            'current_price': current_price,
            'price_threshold': item.price_threshold,
            'stock_id': item.stock.id,
        })
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]  # Last 5 notifications
    
    context = {
        'watchlist': watchlist_data,
        'notifications': notifications,
    }
    return render(request, 'dashboard.html', context)

@login_required
def add_to_watchlist(request):
    if request.method == 'POST':
        symbol = request.POST.get('stock_symbol')
        price_threshold = request.POST.get('price_threshold')
        
        # Find or create the stock entry
        stock, created = Stock.objects.get_or_create(symbol=symbol.upper())
        
        # Add stock to the user's watchlist
        Watchlist.objects.create(
            user=request.user,
            stock=stock,
            price_threshold=price_threshold if price_threshold else None
        )
        
    return redirect('dashboard')

@login_required
def register_telegram_chat_id(request):
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        
        # Save the chat ID in the user's profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.telegram_chat_id = chat_id
        user_profile.save()
        
        return redirect('dashboard')
    
    return render(request, 'register_telegram_chat_id.html')


# Use the bot token from settings
TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

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

def test_telegram_message(request):
    chat_id = 761841281  
    message = "Hello from Django test view using settings!"
    send_telegram_message(chat_id, message)
    return HttpResponse("Hello message sent to Telegram!")

@csrf_exempt
@login_required
def remove_from_watchlist(request):
    if request.method == 'POST':
        stock_id = request.POST.get('stock_id')
        try:
            # Ensure the stock is in the user's watchlist before deleting
            Watchlist.objects.filter(user=request.user, stock_id=stock_id).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def settings_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        notifications = request.POST.get('notifications')
        telegram_chat_id = request.POST.get('telegram_chat_id')

        # Update user email
        request.user.email = email
        request.user.save()

        # Update UserProfile with notifications and telegram_chat_id
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.notifications = notifications
        user_profile.telegram_chat_id = telegram_chat_id
        user_profile.save()

        return redirect('settings')  # Redirect to the same page after saving

    return render(request, 'settings.html', {'user': request.user})


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('signup')  # Redirect to the signup page after account deletion
    return render(request, 'delete_account.html')


@login_required
def candlestick_chart(request, symbol):
    # Fetch historical data for the stock
    stock_data = yf.Ticker(symbol)
    historical = stock_data.history(period="3mo")
    
    # Create the candlestick chart using Plotly
    fig = go.Figure(data=[go.Candlestick(
        x=historical.index,
        open=historical['Open'],
        high=historical['High'],
        low=historical['Low'],
        close=historical['Close']
    )])

    # Convert the chart to JSON for rendering in the frontend
    chart_json = fig.to_json()
    return JsonResponse({'chart': chart_json})
