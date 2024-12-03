from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns =[
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.edit_profile, name='profile'),
    path('', views.index, name='index'),
    path('stocks/<str:symbol>/', views.stock_detail, name='stock_detail'),  # Detailed view for each stock
    path('monitor/', views.index, name='monitor_stocks'),  # The page with real-time updates
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('add_to_watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('register_telegram_chat_id/', views.register_telegram_chat_id, name='register_telegram_chat_id'),
    path('test-telegram-message/', views.test_telegram_message, name='test_telegram_message'),
    path('remove_from_watchlist/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('settings/', views.settings_view, name='settings'),
    path('delete-account/', views.delete_account, name='delete_account'),
        path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='password_change.html',
        success_url='/password-change-done/'
    ), name='password_change'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='password_change_done.html'
    ), name='password_change_done'),
    path('candlestick-chart/<str:symbol>/', views.candlestick_chart, name='candlestick_chart'),

]