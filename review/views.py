from .models import Review
from order.models import Order
from .models import ReviewReport
import uuid
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import IntegrityError
from .models import ReviewLike
from .models import ReviewImage

@login_required(login_url='/user/login/')
def review_create(request, order_id):
    if request.method == "POST":
        rating = request.POST.get("rating")
        content = request.POST.get("content")
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        review, created = Review.objects.get_or_create(
            order=order,
            defaults={"customer": request.user}
        )
        review.rating = rating
        review.content = content
        review.save()

        files = request.FILES.getlist("images")

        for f in files:
            ReviewImage.objects.create(
                review=review,
                image=f
            )

        return JsonResponse({
            "status": "success",
            "created": created
        })

    return JsonResponse({"error": "Invalid request"})




@login_required(login_url='/user/login/')
def review_share(request, review_id):
    review = get_object_or_404(Review, id=review_id, customer=request.user)
    if not review.share_token:
        review.share_token = uuid.uuid4().hex
        review.save()

    share_link = request.build_absolute_uri(
        f"/review/share/{review.share_token}/"
    )

    return JsonResponse({
        "status": "success",
        "share_link": share_link
    })
def review_share_page(request, token):

    review = get_object_or_404(Review, share_token=token)

    return JsonResponse({
        "item": review.order.item.title,
        "rating": review.rating,
        "content": review.content
    })


@login_required(login_url='/user/login/')
def review_report(request, review_id):

    if request.method == "POST":

        reason = request.POST.get("reason")

        review = get_object_or_404(Review, id=review_id)

        report, created = ReviewReport.objects.get_or_create(
            review=review,
            reporter=request.user
        )

        report.reason = reason
        report.save()

        return JsonResponse({
            "status": "reported"
        })

    return JsonResponse({"error": "Invalid request"})

@login_required(login_url='/user/login/')
def review_edit(request, review_id):
    review = get_object_or_404(Review, id=review_id, customer=request.user)
    if request.method == "POST":
        review.rating = request.POST.get("rating")
        review.content = request.POST.get("content")
        review.save()
        files = request.FILES.getlist("images")

        for f in files:
            ReviewImage.objects.create(
                review=review,
                image=f
            )

        return JsonResponse({
            "status": "updated"
        })

    return JsonResponse({
        "rating": review.rating,
        "content": review.content
    })

@login_required(login_url='/user/login/')
def review_delete(request, review_id):

    review = get_object_or_404(Review, id=review_id, customer=request.user)

    review.delete()

    return JsonResponse({
        "status": "deleted"
    })

@login_required(login_url='/user/login/')
def review_score(request, review_id):

    if request.method == "POST":

        score = int(request.POST.get("score"))

        if score < 1 or score > 5:
            return JsonResponse({"error": "Invalid score"})

        review = get_object_or_404(Review, id=review_id, customer=request.user)

        review.rating = score
        review.save()

        return JsonResponse({
            "status": "success",
            "score": score
        })

    return JsonResponse({"error": "Invalid request"})


@login_required(login_url='/user/login/')
def review_list(request):

    reviews = Review.objects.filter(customer=request.user)

    data = []

    for r in reviews:
        data.append({
            "item": r.order.item.title,
            "rating": r.rating,
            "content": r.content
        })

    return JsonResponse({
        "reviews": data
    })


@login_required(login_url='/user/login/')
def review_search(request):

    keyword = request.GET.get("q")

    reviews = Review.objects.filter(
        customer=request.user
    ).filter(
        Q(content__icontains=keyword) |
        Q(order__item__title__icontains=keyword)
    )

    data = []

    for r in reviews:
        data.append({
            "item": r.order.item.title,
            "rating": r.rating,
            "content": r.content
        })

    return JsonResponse({
        "result": data
    })


@login_required(login_url='/user/login/')
def review_like_toggle(request, review_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    review = get_object_or_404(Review, id=review_id)

    like = ReviewLike.objects.filter(review=review, user=request.user).first()
    if like:
        like.delete()
        liked = False
    else:
        ReviewLike.objects.create(review=review, user=request.user)
        liked = True

    return JsonResponse({
        "status": "success",
        "liked": liked,
        "like_count": review.likes.count()
    })