from django.urls import path
from . import views

app_name = "item"

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("search/", views.item_search, name="item_search"),
    path("my/", views.my_item, name="my_item"),

    path("create/", views.item_create, name="item_create"),
    path("<int:item_id>/", views.item, name="item_detail"),
    path("<int:item_id>/edit/", views.item_edit, name="item_edit"),
    path("<int:item_id>/delete/", views.item_delete, name="item_delete"),
    path("<int:item_id>/publish/", views.item_publish, name="item_publish"),

    path("category/<slug:slug>/", views.item_category, name="item_category"),
    path("tag/<slug:tag_slug>/", views.item_tag, name="item_tag"),
    path("test/", views.item_test, name="item_test"),
    path("<int:item_id>/sold/", views.item_mark_sold, name="item_mark_sold"),
]