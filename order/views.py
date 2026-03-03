from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from .models import Order
from item.models import Item
from django.db import transaction
from django.db.models import Q


#create a new order here | 在这里创建订单
@login_required
def order_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        try:
            product = Item.objects.get(id=product_id, status='active')

            #check if is yours order | 检查是不是你的订单
            if product.seller == request.user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You cannot order yourself'
                })

            #create | 创建订单
            order = Order.objects.create(
                customer=request.user,
                seller=product.seller,
                product=product,
                price=product.price,
                status='paid',
                paid_at=timezone.now()
            )

            #update status to 'sold' | 更新状态为已售出
            product.status = 'sold'
            product.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Purchase successful',
                'redirect_url': reverse('order:order_detail', args=[order.id])
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
        order.save()

        if hasattr(order.item, "status") and order.item.status == "sold":
            order.item.status = "active"
            order.item.save()

    return JsonResponse({
        "status": "success",
        "message": "Order cancelled successfully",
        "redirect_url": reverse("order:order_detail", args=[order.id])
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
    ).select_related('customer', 'seller', 'product')

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
