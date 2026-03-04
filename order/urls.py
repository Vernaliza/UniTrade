from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # order
    path("", views.order_list, name="order_list"),
    path("search/", views.order_search, name="order_search"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/cancel/", views.order_cancel, name="order_cancel"),
    path("<int:order_id>/status/", views.order_status, name="order_status"),
    path("<int:order_id>/delete/", views.order_delete, name="order_delete"),

    # basket
    path("basket/", views.basket_detail, name="basket_detail"),
    path("basket/add/", views.basket_add, name="basket_add"),
    path("basket/update/", views.basket_update_quantity, name="basket_update_quantity"),
    path("basket/remove/", views.basket_remove, name="basket_remove"),
    path("basket/checkout/", views.basket_checkout, name="basket_checkout"),]