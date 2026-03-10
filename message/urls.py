from django.urls import path
from . import views

app_name = 'message'

urlpatterns = [
    path('list/', views.message_list, name='message_list'),
    path('detail/', views.message_detail, name='message_detail'),
    path('start/', views.message_start, name='message_start'),
    path('send/', views.message_send, name='message_send'),
    path('fetch/', views.message_fetch, name='message_fetch'),
    path('notification/', views.message_notification, name='message_notification'),
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
]