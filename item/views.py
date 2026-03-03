from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItemForm
from .models import Category, Item


def item(request, item_id):
    obj = get_object_or_404(Item, pk=item_id)
    # Public can only view active items; owner can view their own
    if obj.status != Item.Status.ACTIVE and obj.seller_id != getattr(request.user, "id", None):
        raise Http404("Item not found")
    return render(request, "item/item_detail.html", {"item": obj})


@login_required
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.seller = request.user
            obj.status = Item.Status.ACTIVE  # or HIDDEN if you want moderation flow
            obj.save()
            return redirect("item_detail", item_id=obj.id)
    else:
        form = ItemForm()
    return render(request, "item/item_form.html", {"form": form})


@login_required
def item_publish(request, item_id):
    obj = get_object_or_404(Item, pk=item_id, seller=request.user)
    #allow republish from delisted/hidden to active
    obj.status = Item.Status.ACTIVE
    obj.save(update_fields=["status", "updated_at"])
    return redirect("item_detail", item_id=obj.id)


@login_required
def item_edit(request, item_id):
    obj = get_object_or_404(Item, pk=item_id, seller=request.user)
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("item_detail", item_id=obj.id)
    else:
        form = ItemForm(instance=obj)
    return render(request, "item/item_form.html", {"form": form, "item": obj})


@login_required
def item_delete(request, item_id):
    obj = get_object_or_404(Item, pk=item_id, seller=request.user)
    if request.method == "POST":
        obj.status = Item.Status.DELETED
        obj.save(update_fields=["status", "updated_at"])
        return redirect("my_item")
    return render(request, "item/item_confirm_delete.html", {"item": obj})


def item_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    qs = Item.objects.filter(category=category, status=Item.Status.ACTIVE).order_by("-created_at")
    return render(request, "item/item_list.html", {"items": qs, "category": category})


def item_tag(request, tag_slug):
    #currently have no Tag model/field, so this is a placeholder.
    #once add tags, implement filtering here.
    return render(request, "item/not_implemented.html", {"feature": "tag"})


def item_list(request):
    qs = Item.objects.filter(status=Item.Status.ACTIVE).order_by("-created_at")
    return render(request, "item/item_list.html", {"items": qs})


def item_search(request):
    q = (request.GET.get("q") or "").strip()
    qs = Item.objects.filter(status=Item.Status.ACTIVE)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    qs = qs.order_by("-created_at")
    return render(request, "item/item_search.html", {"items": qs, "q": q})


@login_required
def my_item(request):
    qs = Item.objects.filter(seller=request.user).order_by("-created_at")
    return render(request, "item/my_item.html", {"items": qs})


@login_required
def item_mark_sold(request, item_id):
    obj = get_object_or_404(Item, pk=item_id, seller=request.user)
    if request.method == "POST":
        obj.status = Item.Status.SOLD
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, f'"{obj.title}" has been successfully marked as Sold!')
    return redirect("item:my_item")


"""JUST FOR TEST!!!"""
def item_test(request):
    categories = Category.objects.all()
    return render(request, "item/item_test.html", {
        "categories": categories
    })
