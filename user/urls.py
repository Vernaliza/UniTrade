from django.urls import path
from user import views
app_name = 'user'

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('change-password/', views.change_password, name='change_password'),
    path('toggle-role/', views.toggle_role, name='toggle_role'),
    path('test-toggle-role/', views.test_toggle_role, name='test_toggle_role'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
