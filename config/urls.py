"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.urls import include
from django.shortcuts import render
from django.views.generic import RedirectView

from django.conf import settings
from django.conf.urls.static import static

from item.models import Item
import os

def index(request):
    latest_items = Item.objects.filter(status=Item.Status.ACTIVE).order_by("-created_at")[:4]
    # banner images
    banner_images = []
    images_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    
    if os.path.exists(images_dir):
        for filename in os.listdir(images_dir):
            if filename.startswith('banner') and filename.endswith(('.jpg', '.jpeg', '.png', 'webp')):
                banner_images.append(f'images/{filename}')
    # sort
    banner_images.sort()
    context = {
        'latest_items': latest_items,
        'banner_images': banner_images,
    }
    # return render(request, 'index.html', {'latest_items': latest_items})context
    return render(request, 'index.html', context)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', index, name='index'),
    # path('', RedirectView.as_view(pattern_name='item:item_list', permanent=False), name='index'),
    path('administrator/', include('administrator.urls')),
    path('payment/', include('payment.urls')),
    path('message/', include('message.urls')),
    path('order', include('order.urls')),
    path('review/', include('review.urls')),
    path('user/', include('user.urls')),
    path("item/", include("item.urls")),
    path('accounts/', include('allauth.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)