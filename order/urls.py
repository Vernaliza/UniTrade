from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("search/", views.order_search, name="order_search"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/cancel/", views.order_cancel, name="order_cancel"),
    path("<int:order_id>/status/", views.order_status, name="order_status"),
    path("<int:order_id>/delete/", views.order_delete, name="order_delete"),
]