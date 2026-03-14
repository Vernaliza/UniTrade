import uuid
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponseForbidden

from order.models import Order
from item.models import Item
from message.models import Notification
from .models import Payment


@login_required(login_url='/user/login/')
def pay_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if order.status != "pending":
        return redirect("order:order_detail", order_id=order.id)

    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={
            "user": request.user,
            "amount": order.amount,
            "transaction_no": f"MOCK-{uuid.uuid4().hex[:12].upper()}",
            "status": "pending",
        }
    )

    return render(request, "payment/pay_order.html", {
        "order": order,
        "payment": payment,
    })


@login_required(login_url='/user/login/')
@transaction.atomic
def pay_confirm(request, order_id):
    if request.method != "POST":
        return HttpResponseForbidden("Invalid request method")

    order = get_object_or_404(
        Order.objects.select_for_update(),
        id=order_id,
        customer=request.user
    )

    if order.status != "pending":
        return redirect("order:order_list")  # 跳到order list就行了因为订单列表已经有详细信息
        # return redirect("order:order_detail", order_id=order.id)

    item = get_object_or_404(Item.objects.select_for_update(), id=order.item_id)

    # if item.status != Item.Status.ACTIVE:
    #     payment = Payment.objects.filter(order=order, user=request.user).first()
    #     if payment:
    #         payment.status = "failed"
    #         payment.save(update_fields=["status"])

    #     return render(request, "payment/pay_failed.html", {
    #         "message": "Item is no longer available. Mock payment failed."
    #     })

    # Stock already checked when order was created!
    # 库存已经在下订单时检查了，所以这里不需要再检查库存。
    # if item.stock < order.quantity:
    #     payment = Payment.objects.filter(order=order, user=request.user).first()
    #     if payment:
    #         payment.status = "failed"
    #         payment.save(update_fields=["status"])

    #     return render(request, "payment/pay_failed.html", {
    #         "message": "Not enough stock. Mock payment failed."
    #     })

    payment = get_object_or_404(Payment, order=order, user=request.user)
    payment.status = "success"
    payment.paid_time = timezone.now()
    payment.save(update_fields=["status", "paid_time"])

    order.status = "paid"
    order.paid_time = timezone.now()
    order.save(update_fields=["status", "paid_time"])

    # 这里不需要再扣库存了，因为在下订单时已经扣库存了。
    # Do not need to decrease stock here because stock was already decreased when order was created.
    # item.stock -= order.quantity
    # if item.stock <= 0:
    #     item.stock = 0
    #     item.status = Item.Status.PENDING
    #     item.save(update_fields=["stock", "status"])
    # else:
    #     item.save(update_fields=["stock"])

    Notification.objects.create(
        user=order.seller,
        order=order,
        notification_type="new_order",
        content=f"You received a new paid order {order.order_id} for {order.item.title}."
    )

    return redirect("payment:pay_success", order_id=order.id)


@login_required(login_url='/user/login/')
def pay_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, "payment/pay_success.html", {"order": order})