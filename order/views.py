from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from item.models import Item
from .models import Basket, BasketItem, Order
import uuid
from order.models import Order
from message.models import Notification

'''The following are the order functions'''


#create a new order here | 在这里创建订单
@login_required
@transaction.atomic
def order_create(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        qty = int(request.POST.get('quantity', 1))

        if qty <= 0:
            return JsonResponse({'status': 'error', 'message': 'quantity must be > 0'})

        try:
            item = Item.objects.select_for_update().get(id=item_id, status=Item.Status.ACTIVE)

            if item.seller == request.user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You cannot order yourself'
                })

            if item.seller is None:
                return JsonResponse({'status': 'error', 'message': 'Item has no seller'})

            if item.stock < qty:
                return JsonResponse({'status': 'error', 'message': f'Not enough stock. Left: {item.stock}'})

            order = Order.objects.create(
                order_id=_new_order_id(),
                customer=request.user,
                seller=item.seller,
                item=item,
                quantity=qty,
                amount=(item.price * qty),
                status='pending',
            )
            # --- NEW: Deduct the stock and update status! ---
            item.stock -= qty
            if item.stock == 0:
                item.status = Item.Status.PENDING # Mark as pending if sold out
            item.save(update_fields=['stock', 'status'])

            return JsonResponse({
                'status': 'success',
                'message': 'Order created, please pay',
                'redirect_url': reverse('payment:pay_order', args=[order.id])
            })

        except Item.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Item does not exist or has been sold'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

#week8 we will learn AJAX, maybe anyone want additional AJAX interface :)
def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


#cancel order
#only the order participants (customer or seller) can cancel.
#only orders in 'pending' or 'paid' status can be cancelled.
#if cancelled, the related item status will be reverted to 'active'
#只有订单参与者（买家 customer 或 卖家 seller）可以取消订单
#只有状态为 pending 或 paid 时才允许取消
#取消后如商品状态为 sold，则恢复为 active
@login_required
def order_cancel(request, order_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    order = get_object_or_404(Order, id=order_id)

    if request.user != order.customer and request.user != order.seller:
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)

    if order.status not in {"pending", "paid"}:
        return JsonResponse(
            {"status": "error", "message": f"Order cannot be cancelled in status '{order.status}'"},
            status=400
        )

    with transaction.atomic():

        order.status = "cancelled"
        order.save(update_fields=["status"])

        notify_user = order.seller if request.user == order.customer else order.customer

        Notification.objects.create(
            user=notify_user,
            order=order,
            notification_type="order_cancelled",
            content=f"Order {order.order_id} has been cancelled."
        )
        order.item.stock += order.quantity
        if order.item.status != "active":
            order.item.status = "active"
            
        order.item.save(update_fields=["stock", "status"])
        # -------------------------------------------
        
        # If the item was hidden/pending/sold because it was out of stock, make it active again!
        if order.item.status != "active":
            order.item.status = "active"
            
        order.item.save(update_fields=["stock", "status"])

        if hasattr(order.item, "status") and order.item.status == "sold":
            order.item.status = "active"
            order.item.save(update_fields=["status"])

    return JsonResponse({
        "status": "success",
        "message": "Order cancelled successfully",
        "redirect_url": reverse("order:order_list") # 取消后跳到订单列表，订单列表里有详细信息了
    })


#update order status | 修改订单状态
@login_required
def order_status(request, order_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    order = get_object_or_404(Order, id=order_id)
    new_status = (request.POST.get("status") or "").strip().lower()

    if new_status not in {"pending", "paid", "completed", "cancelled"}:
        return JsonResponse({"status": "error", "message": "Invalid status value"}, status=400)

    if request.user != order.customer and request.user != order.seller:
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)

    if order.status == "cancelled":
        return JsonResponse({"status": "error", "message": "Cancelled orders cannot be modified"}, status=400)

    allowed_transitions = {
        "pending": {"paid", "cancelled"},
        "paid": {"completed", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }

    if new_status not in allowed_transitions.get(order.status, set()):
        return JsonResponse(
            {"status": "error", "message": f"Cannot change status from '{order.status}' to '{new_status}'"},
            status=400
        )

    order.status = new_status

    if new_status == "paid":
        order.paid_time = timezone.now()

    order.save()

    notify_user = order.seller if request.user == order.customer else order.customer

    Notification.objects.create(
        user=notify_user,
        order=order,
        notification_type='order_status',
        content=f'Order {order.order_id} status has been updated to {new_status}.'
    )

    return JsonResponse({
        "status": "success",
        "message": f"Order status updated to '{new_status}'",
        "redirect_url": reverse("order:order_detail", args=[order.id])
    })


#delete order | 删除订单
@login_required
def order_delete(request, order_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    order = get_object_or_404(Order, id=order_id)

    if request.user != order.customer and request.user != order.seller:
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)

    if order.status not in {"cancelled", "completed"}:
        return JsonResponse(
            {"status": "error", "message": "Order cannot be deleted in its current status"},
            status=400
        )

    order.delete()

    return JsonResponse({
        "status": "success",
        "message": "Order deleted successfully",
        "redirect_url": reverse("order:order_list")
    })


#obtain all orders from both customers and sellers of the user | 获取用户买卖双方的所有订单
@login_required
def order_list(request):
    orders = Order.objects.filter(
        Q(customer=request.user) | Q(seller=request.user)
    ).select_related('customer', 'seller', 'item')

    return render(request, 'order/order_list.html', {
        'orders': orders
    })


#search order | 搜索订单
@login_required
def order_search(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip().lower()

    orders = Order.objects.filter(
        Q(customer=request.user) | Q(seller=request.user)
    ).select_related("customer", "seller", "item").order_by("-created_time")

    if q:
        orders = orders.filter(
            Q(order_id__icontains=q) |
            Q(customer__username__icontains=q) |
            Q(seller__username__icontains=q) |
            Q(item__title__icontains=q) |
            Q(item__name__icontains=q)
        )

    if status in {"pending", "paid", "completed", "cancelled"}:
        orders = orders.filter(status=status)

    if _is_ajax(request):
        data = [{
            "id": o.id,
            "order_id": o.order_id,
            "status": o.status,
            "amount": str(o.amount),
            "customer": o.customer.username,
            "seller": o.seller.username,
            "item_id": o.item_id,
            "item": getattr(o.item, "title", None) or getattr(o.item, "name", ""),
            "created_time": o.created_time.isoformat() if o.created_time else None,
            "paid_time": o.paid_time.isoformat() if o.paid_time else None,
        } for o in orders]

        return JsonResponse({
            "status": "success",
            "count": len(data),
            "results": data
        })

    return render(request, "order/order_list.html", {
        "orders": orders,
        "q": q,
        "status": status
    })


#view order details here | 在这里查看订单详情
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    #check permissions | 检查权限
    if order.customer != request.user and order.seller != request.user:
        return redirect('order:order_list')

    return render(request, 'order/order_detail.html', {
        'order': order
    })



'''The following are the shopping cart functions'''



#Ensure that the creation is completed on the first visit and the same basket is reused thereafter
#保证第一次访问就完成创建，之后一直复用同一个 Basket
def _get_or_create_basket(user) -> Basket:
    basket, _ = Basket.objects.get_or_create(user=user)
    return basket


#view basket details here | 在这里查看购物车详情
@login_required
def basket_detail(request):
    basket = _get_or_create_basket(request.user)
    items = basket.items.select_related("item")
    return render(request, "order/basket_detail.html", {
        "basket": basket,
        "items": items,
        "total": basket.total_amount(),
    })


#add to the basket | 加入购物车
@login_required
@transaction.atomic
def basket_add(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    item_id = request.POST.get("item_id")
    qty = int(request.POST.get("quantity", 1))

    if qty <= 0:
        return JsonResponse({"status": "error", "message": "quantity must be > 0"}, status=400)

    item = get_object_or_404(Item, id=item_id)

    #verify | 校验
    if hasattr(item, "status") and item.status != "active":
        return JsonResponse({"status": "error", "message": "Item is not available"}, status=400)
    if hasattr(item, "seller") and item.seller == request.user:
        return JsonResponse({"status": "error", "message": "You cannot add your own item"}, status=400)

    basket = _get_or_create_basket(request.user)

    bi, created = BasketItem.objects.select_for_update().get_or_create(
        basket=basket,
        item=item,
        defaults={"quantity": qty, "unit_price": getattr(item, "price", Decimal("0.00"))},
    )
    if not created:
        bi.quantity += qty
        bi.unit_price = getattr(item, "price", bi.unit_price)
        bi.save()

    return JsonResponse({
        "status": "success",
        "message": "Added to basket",
        "redirect_url": reverse("order:basket_detail"),
    })


#modify quantity | 修改数量
@login_required
@transaction.atomic
def basket_update_quantity(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    basket = _get_or_create_basket(request.user)
    bi_id = request.POST.get("basket_item_id")
    qty = int(request.POST.get("quantity", 1))

    bi = get_object_or_404(BasketItem.objects.select_for_update(), id=bi_id, basket=basket)

    if qty <= 0:
        bi.delete()
    else:
        bi.quantity = qty
        bi.save()

    return JsonResponse({"status": "success", "redirect_url": reverse("order:basket_detail")})


#remove item | 移除商品
@login_required
@transaction.atomic
def basket_remove(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    basket = _get_or_create_basket(request.user)
    bi_id = request.POST.get("basket_item_id")

    bi = get_object_or_404(BasketItem.objects.select_for_update(), id=bi_id, basket=basket)
    bi.delete()

    return JsonResponse({"status": "success", "redirect_url": reverse("order:basket_detail")})

def _new_order_id():
    return uuid.uuid4().hex[:20].upper()

#checkout, turn the status of order to "pending", turn the status of item to "sold" | 结算
@login_required
@transaction.atomic
def basket_checkout(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    basket = _get_or_create_basket(request.user)

    basket_items = list(basket.items.select_for_update().select_related("item"))
    if not basket_items:
        return JsonResponse({"status": "error", "message": "Basket is empty"}, status=400)

    created_order_ids = []

    for bi in basket_items:
        item = Item.objects.select_for_update().get(id=bi.item_id)

        if item.status != Item.Status.ACTIVE:
            return JsonResponse({"status": "error", "message": f"Item {item.id} is not available"}, status=400)

        if item.seller_id == request.user.id:
            return JsonResponse({"status": "error", "message": "You cannot checkout your own item"}, status=400)

        if item.seller is None:
            return JsonResponse({"status": "error", "message": "Item has no seller"}, status=400)

        if item.stock < bi.quantity:
            return JsonResponse({"status": "error", "message": f"Not enough stock for item {item.title}"}, status=400)

        order = Order.objects.create(order_id=_new_order_id(), customer=request.user, seller=item.seller, item=item,
                                     quantity=bi.quantity, amount=bi.subtotal(), status="pending", )

        created_order_ids.append(order.id)
        item.stock -= bi.quantity
        if item.stock == 0:
            item.status = Item.Status.PENDING 
        item.save(update_fields=['stock', 'status'])

    basket.items.all().delete()

    return JsonResponse({
        "status": "success",
        "message": "Checkout success, please pay your orders",
        "redirect_url": reverse("payment:pay_order", args=[created_order_ids[0]]),
        "orders": created_order_ids,
    })