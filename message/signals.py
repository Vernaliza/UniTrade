from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

@receiver(user_logged_out)
def force_offline_on_logout(sender, request, user, **kwargs):
    #用户登出时，last_seen -5，下线
    if user and hasattr(user, 'presence'):
        user.presence.last_seen = timezone.now() - timedelta(minutes=5)
        user.presence.save(update_fields=['last_seen'])