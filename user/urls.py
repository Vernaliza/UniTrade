from django.urls import path
from user import views
app_name = 'user'

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
]
