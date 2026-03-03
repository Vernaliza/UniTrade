
from django.urls import path
from . import views

app_name = 'administrator'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    # Add the delete route
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]