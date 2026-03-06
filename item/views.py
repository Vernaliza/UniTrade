from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ItemForm
from .models import Category, Item
from django.http import Http404, JsonResponse  # <-- Added JsonResponse here
from django.db.models import Count
from review.models import Review


# def item(request, item_id):
#     obj = get_object_or_404(Item, pk=item_id)
#     # Public can only view active items; owner can view their own
#     if obj.status != Item.Status.ACTIVE and obj.seller_id != getattr(request.user, "id", None):
#         raise Http404("Item not found")
#     return render(request, "item/item_detail.html", {"item": obj})
def item(request, item_id):
    obj = get_object_or_404(Item, pk=item_id)

    # Public can only view active items; owner can view their own
    if obj.status != Item.Status.ACTIVE and obj.seller_id != getattr(request.user, "id", None):
        raise Http404("Item not found")

    reviews = (
        Review.objects.filter(order__item=obj)
        .select_related("customer", "order")
        .prefetch_related("images", "likes")
        .annotate(like_count=Count("likes"))
        .order_by("-created_time")
    )

    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(
            request.user.reviewlike_set.filter(
                review__order__item=obj
            ).values_list("review_id", flat=True)
        )

    return render(request, "item/item_detail.html", {
        "item": obj,
        "reviews": reviews,
        "liked_ids": liked_ids,
    })

@login_required
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.seller = request.user
            obj.status = Item.Status.ACTIVE  # or HIDDEN if you want moderation flow
            obj.save()
            return redirect("item:item_detail", item_id=obj.id)
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
    categories = Category.objects.all()
    category = get_object_or_404(Category, slug=slug)
    qs = Item.objects.filter(category=category, status=Item.Status.ACTIVE).order_by("-created_at")
    return render(request, "item/item_list.html", {"items": qs, "category": category, "categories": categories})

def item_tag(request, tag_slug):
    return render(request, "item/not_implemented.html", {"feature": "tag"})

def item_list(request):
    categories = Category.objects.all()
    qs = Item.objects.filter(status=Item.Status.ACTIVE).order_by("-created_at")
    return render(request, "item/item_list.html", {"items": qs, "categories": categories})

def item_search(request):
    q = (request.GET.get("q") or "").strip()
    category_slug = request.GET.get("category")  
    
    qs = Item.objects.filter(status=Item.Status.ACTIVE)
    
    # 1. Filter by category if one is provided
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        qs = qs.filter(category=current_category)
        
    # 2. Filter by search text
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        
    qs = qs.order_by("-created_at")
    
    # 3. RESTORED: Check if this is an AJAX "live search" request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        results = []
        for item in qs[:5]:
            results.append({
                'id': item.id,
                'title': item.title,
                'price': str(item.price),
                'image_url': item.image.url if item.image else '',
            })
        from django.http import JsonResponse
        return JsonResponse({'status': 'success', 'results': results})
    
    # 4. Standard response for when they press "Enter"
    categories = Category.objects.all()
    return render(request, "item/item_list.html", {
        "items": qs, 
        "categories": categories,
        "category": current_category,  
        "search_query": q
    })
    q = (request.GET.get("q") or "").strip()
    category_slug = request.GET.get("category")  # Catch the hidden category parameter
    
    qs = Item.objects.filter(status=Item.Status.ACTIVE)
    
    # 1. If a category was passed, filter the items by that category FIRST
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        qs = qs.filter(category=current_category)
        
    # 2. Then apply the text search keyword
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        
    qs = qs.order_by("-created_at")
    
    # Pass everything back to your beautiful item_list grid
    categories = Category.objects.all()
    return render(request, "item/item_list.html", {
        "items": qs, 
        "categories": categories,
        "category": current_category,  # Keeps the sidebar category highlighted!
        "search_query": q
    })
    q = (request.GET.get("q") or "").strip()
    qs = Item.objects.filter(status=Item.Status.ACTIVE)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    qs = qs.order_by("-created_at")
    
    # NEW: Check if this is an AJAX "live search" request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # We only return the top 5 results for the dropdown to keep it clean
        results = []
        for item in qs[:5]:
            results.append({
                'id': item.id,
                'title': item.title,
                'price': str(item.price),
                'image_url': item.image.url if item.image else '',
            })
        return JsonResponse({'status': 'success', 'results': results})

    # Existing standard response (for when they press Enter)
    categories = Category.objects.all()
    return render(request, "item/item_list.html", {
        "items": qs, 
        "categories": categories, 
        "search_query": q  
    })


@login_required
def my_item(request):
    from order.models import Order
    display_items = []
    
    # 1. Fetch remaining active items (not reserved)
    active_items = Item.objects.filter(seller=request.user, status=Item.Status.ACTIVE).order_by("-created_at")
    for item in active_items:
        display_items.append({
            'is_order': False,
            'item_id': item.id,
            'title': item.title,
            'price': item.price,
            'status': item.status,
            'status_display': item.get_status_display(),
        })
        
    # 2. Fetch pending orders and SPLIT them into individual rows for the template
    pending_orders = Order.objects.filter(seller=request.user, status="pending").order_by("-created_time")
    for order in pending_orders:
        unit_price = order.amount / order.quantity if order.quantity else order.item.price
        
        # If the buyer bought 2, this loop runs 2 times!
        for _ in range(order.quantity):
            display_items.append({
                'is_order': True,
                'order_id': order.id,
                'item_id': order.item.id,
                'title': order.item.title,
                'price': unit_price,
                'status': 'pending',
                'status_display': 'Pending',
                'buyer_name': order.customer.username,
                'buyer_email': order.customer.email,
            })
            
    return render(request, "item/my_item.html", {"display_items": display_items})

@login_required
def item_mark_sold(request, item_id):
    # Manual sold button for Active items
    obj = get_object_or_404(Item, pk=item_id, seller=request.user)
    if request.method == "POST":
        obj.status = Item.Status.SOLD
        obj.stock = 0
        obj.save(update_fields=["status", "stock", "updated_at"])
        messages.success(request, f'"{obj.title}" manually marked as Sold!')
    return redirect("item:my_item")

@login_required
def order_approve(request, order_id):
    from order.models import Order
    order = get_object_or_404(Order, pk=order_id, seller=request.user)
    if request.method == "POST":
        unit_price = order.amount / order.quantity if order.quantity else 0
        
        # If order quantity is > 1, we peel off 1 item from the order and complete it
        if order.quantity > 1:
            order.quantity -= 1
            order.amount -= unit_price
            order.save()
            Order.objects.create(
                order_id=order.order_id + "-A", customer=order.customer, seller=order.seller,
                item=order.item, quantity=1, amount=unit_price, status="completed"
            )
        else:
            order.status = "completed"
            order.save(update_fields=["status"])
            
        item = order.item
        if item.stock == 0 and not Order.objects.filter(item=item, status="pending").exists():
            item.status = Item.Status.SOLD
            item.save(update_fields=["status", "updated_at"])
        messages.success(request, f'One unit of {item.title} approved!')
    return redirect("item:my_item")

@login_required
def order_refuse(request, order_id):
    from order.models import Order
    order = get_object_or_404(Order, pk=order_id, seller=request.user)
    if request.method == "POST":
        unit_price = order.amount / order.quantity if order.quantity else 0
        
        if order.quantity > 1:
            order.quantity -= 1
            order.amount -= unit_price
            order.save()
        else:
            order.status = "cancelled"
            order.save(update_fields=["status"])
            
        item = order.item
        item.stock += 1
        if item.status in [Item.Status.PENDING, Item.Status.SOLD]:
            item.status = Item.Status.ACTIVE
        item.save(update_fields=["stock", "status", "updated_at"])
        messages.success(request, f'Sale refused. Stock returned to the market.')
    return redirect("item:my_item")
    obj = get_object_or_404(Item, pk=item_id, seller=request.user)
    if request.method == "POST":
        if obj.status == Item.Status.PENDING:
            from order.models import Order
            
            # Find the active orders holding this item hostage and cancel them
            active_orders = Order.objects.filter(item=obj, status__in=["pending", "paid"])
            restored_stock = 0
            for order in active_orders:
                restored_stock += order.quantity
                order.status = "cancelled"
                order.save(update_fields=["status"])
            
            # Put the item back on the market and restore its stock!
            obj.status = Item.Status.ACTIVE
            obj.stock += restored_stock
            obj.save(update_fields=["status", "stock", "updated_at"])
            
            messages.success(request, f'Sale refused. "{obj.title}" is back on the active market!')
            
    return redirect("item:my_item")

"""JUST FOR TEST!!!"""
def item_test(request):
    categories = Category.objects.all()
    return render(request, "item/item_test.html", {
        "categories": categories
    })
