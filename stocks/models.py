# models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Stock(models.Model):
    # Basic stock information
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50, blank=True, null=True)  # For shorter names if needed

    # Market data
    price = models.FloatField(default=0, blank=True)
    original_price = models.FloatField(default=0)
    price_change = models.FloatField(default=0)
    state = models.CharField(max_length=10, blank=True)  # For tracking price state (raise, fall, same)
    market_cap = models.BigIntegerField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    forward_pe_ratio = models.FloatField(null=True, blank=True)

    # Dividend data
    dividend_yield = models.FloatField(null=True, blank=True)
    dividend_rate = models.FloatField(null=True, blank=True)

    # Risk and volatility data
    beta = models.FloatField(null=True, blank=True)

    # Day and 52-week range
    day_high = models.FloatField(null=True, blank=True)
    day_low = models.FloatField(null=True, blank=True)
    fifty_two_week_high = models.FloatField(null=True, blank=True)
    fifty_two_week_low = models.FloatField(null=True, blank=True)

    # Volume data
    volume = models.BigIntegerField(null=True, blank=True)
    average_volume = models.BigIntegerField(null=True, blank=True)

    # Financial ratios
    total_cash = models.BigIntegerField(null=True, blank=True)
    total_debt = models.BigIntegerField(null=True, blank=True)
    gross_margin = models.FloatField(null=True, blank=True)
    operating_margin = models.FloatField(null=True, blank=True)
    profit_margin = models.FloatField(null=True, blank=True)
    return_on_assets = models.FloatField(null=True, blank=True)
    return_on_equity = models.FloatField(null=True, blank=True)

    # Analyst information
    target_high_price = models.FloatField(null=True, blank=True)
    target_low_price = models.FloatField(null=True, blank=True)
    recommendation_key = models.CharField(max_length=50, null=True, blank=True)

    def update_price(self, new_price):
        """Update stock price and calculate price change."""
        if self.original_price == 0:
            self.original_price = new_price
            self.price_change = 0  # No change on the first update
        else:
            # Calculate the change as the difference between the new price and the last recorded price
            self.price_change = new_price - self.price
        # Update the current price
        self.price = new_price
        self.save()

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    class Meta:
        ordering = ['symbol']


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    price_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Watchlist: {self.stock.symbol} with threshold ${self.price_threshold}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='pending')  # Status: 'pending' or 'sent'

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message} at {self.created_at}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)
    notifications = models.CharField(max_length=10, choices=[('enabled', 'Enabled'), ('disabled', 'Disabled')], default='enabled')

    def __str__(self):
        return f"{self.user.username}'s Profile"



# Signal to automatically create a UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile instance when a User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)
        print(f"UserProfile created for {instance.username}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.
    """
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
