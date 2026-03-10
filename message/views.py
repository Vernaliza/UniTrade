from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from item.models import Item
from .models import Conversation, Message, Notification, UserPresence


#helper function: Determine whether a user is a participant in this session
#辅助函数：判断某个用户是不是这个会话的参与者
def is_conversation_participant(user, conversation):
    return user == conversation.buyer or user == conversation.seller

#helper function: Determine if this user is currently online
#辅助函数：判断这个用户现在是不是在线
def is_user_online(user):
    try:
        return timezone.now() - user.presence.last_seen <= timedelta(minutes=2)
    except UserPresence.DoesNotExist:
        return False

#helper function: Generate status text to be displayed on the page
#辅助函数：生成给页面显示的状态文字
def get_last_seen_display(user):
    try:
        last_seen = user.presence.last_seen
    except UserPresence.DoesNotExist:
        return 'Offline'

    diff = timezone.now() - last_seen
    if diff <= timedelta(minutes=2):
        return 'Online'
    elif diff.total_seconds() < 3600:
        minutes = max(1, int(diff.total_seconds() // 60))
        return f'Last seen {minutes} minute{"s" if minutes != 1 else ""} ago'
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f'Last seen {hours} hour{"s" if hours != 1 else ""} ago'
    else:
        days = diff.days
        return f'Last seen {days} day{"s" if days != 1 else ""} ago'


#watch message list | 查看消息列表
@login_required
def message_list(request):
    conversations = Conversation.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).select_related(
        'buyer', 'seller', 'item'
    ).order_by('-updated_at')

    conversation_data = []
    for conversation in conversations:
        other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer
        last_message = conversation.messages.order_by('-created_at').first()
        unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).count()

        conversation_data.append({
            'conversation': conversation,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
            'other_user_online': is_user_online(other_user),
            'other_user_status': get_last_seen_display(other_user),
        })

    return render(request, 'message/message_list.html', {
        'conversation_data': conversation_data
    })


#display the chat details page of a specific conversation | 显示某一个具体会话的聊天详情页
@login_required
def message_detail(request):
    conversation_id = request.GET.get('conversation_id')
    if not conversation_id:
        django_messages.warning(request, 'Conversation does not exist.')
        return redirect('message_list')

    conversation = get_object_or_404(
        Conversation.objects.select_related('buyer', 'seller', 'item'),
        id=conversation_id
    )

    if not is_conversation_participant(request.user, conversation):
        return HttpResponseForbidden("You are not allowed to view this conversation.")

    # Currently are watching this conversation, message bar will not send.
    cache.set(f'user_{request.user.id}_watching', str(conversation.id), timeout=10)
    Notification.objects.filter(user=request.user, conversation=conversation, is_read=False).update(is_read=True)

    chat_messages = conversation.messages.select_related('sender').order_by('created_at')

    chat_messages.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)

    Notification.objects.filter(
        user=request.user,
        conversation=conversation,
        is_read=False
    ).update(is_read=True)

    other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer

    return render(request, 'message/message_detail.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,
        'other_user': other_user,
        'other_user_online': is_user_online(other_user),
        'other_user_status': get_last_seen_display(other_user),
    })

#initiate a chat from the product page | 从商品页面发起聊天
@login_required
def message_start(request):
    item_id = request.GET.get('item_id')
    if not item_id:
        django_messages.warning(request, 'Item does not exist.')
        return redirect('message_list')

    item = get_object_or_404(Item, id=item_id)

    buyer = request.user
    seller = item.seller

    if buyer == seller:
        django_messages.warning(request, 'You cannot message yourself.')
        return redirect('item:item_detail', item.id)

    conversation, created = Conversation.objects.get_or_create(item=item, buyer=buyer, seller=seller)

    return redirect(f'/message/detail/?conversation_id={conversation.id}')


@login_required
def message_send(request):
    if request.method != 'POST':
        return redirect('/message/list/')

    conversation_id = request.POST.get('conversation_id')
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if not is_conversation_participant(request.user, conversation):
        return HttpResponseForbidden("You are not allowed to send messages in this conversation.")

    text = request.POST.get('text', '').strip()
    image = request.FILES.get('image')

    if not text and not image:
        django_messages.warning(request, 'Message cannot be empty.')
        return redirect(f'/message/detail/?conversation_id={conversation.id}')

    new_message = Message.objects.create(
        conversation=conversation, 
        sender=request.user, 
        text=text if text else None, 
        image=image if image else None, 
        is_read=False
    )

    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['updated_at'])

    receiver = conversation.seller if request.user == conversation.buyer else conversation.buyer

    is_receiver_watching = cache.get(f'user_{receiver.id}_watching') == str(conversation.id)

    if not is_receiver_watching:
        Notification.objects.update_or_create(
            user=receiver, 
            conversation=conversation, 
            is_read=False,
            defaults={
                'message': new_message,
                'content': f'{request.user.username} sent you a new message',
                'created_at': timezone.now()
            }
        )

    # AJAX 无刷新发送消息
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({'status': 'ok'})
        
    return redirect(f'/message/detail/?conversation_id={conversation.id}')

#fetch new message | 拉取新消息
@login_required
def message_fetch(request):
    conversation_id = request.GET.get('conversation_id')
    last_message_id = request.GET.get('last_message_id')

    conversation = get_object_or_404(Conversation, id=conversation_id)

    if not is_conversation_participant(request.user, conversation):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    # 前端来拉消息 就把状态延续10秒
    cache.set(f'user_{request.user.id}_watching', str(conversation.id), timeout=10)
    # Notification.objects.filter(user=request.user, conversation=conversation, is_read=False).update(is_read=True)

    chat_messages = conversation.messages.select_related('sender').order_by('created_at')

    if last_message_id:
        chat_messages = chat_messages.filter(id__gt=last_message_id)

    data = []
    for msg in chat_messages:
        data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'text': msg.text if msg.text else '',
            'image_url': msg.image.url if msg.image else '',
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_mine': msg.sender == request.user,
        })

    conversation.messages.exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).update(is_read=True)

    Notification.objects.filter(
        user=request.user,
        conversation=conversation,
        is_read=False
    ).update(is_read=True)

    other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer

    return JsonResponse({
        'chat_messages': data,
        'other_user_online': is_user_online(other_user),
        'other_user_status': get_last_seen_display(other_user),
    })


#show notification list | 显示当前用户的消息通知列表
@login_required
def message_notification(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related(
        'conversation', 'message', 'order'
    ).order_by('-created_at')

    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'message/message_notification.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


#when clicking on a notification, mark it as read and redirect it to the corresponding chat page | 点开某一条通知时，把它标记为已读，并跳转到对应聊天页
@login_required
def message_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if notification.conversation:
        return redirect(f'/message/detail/?conversation_id={notification.conversation.id}')

    if notification.order:
        return redirect('order:order_detail', order_id=notification.order.id)

    return redirect('message_notification')

# AJAX API for fetching unread message count | 获取未读消息数量的 AJAX API
@login_required
def api_unread_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
            is_read=False
        ).exclude(sender=request.user).count()
        return JsonResponse({'unread_count': count})
    
    return JsonResponse({'unread_count': 0})