from django.db.models import Q
from .models import Message

def unread_messages(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
            is_read=False
        ).exclude(sender=request.user).count()
        
        return {'unread_count': count}
    
    return {'unread_count': 0}