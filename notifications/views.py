from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("event")
        .order_by("-created_at")
    )

    unread_count = notifications.filter(
        is_read=False,
    ).count()

    context = {
        "notifications": notifications,
        "unread_count": unread_count,
    }

    return render(
        request,
        "notifications/notification_list.html",
        context,
    )
@login_required
def mark_notification_read(request, notification_id):
    if request.method != "POST":
        return redirect("notification_list")

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True

        notification.save(
            update_fields=["is_read"]
        )

    return redirect("notification_list")
@login_required
def mark_all_notifications_read(request):
    if request.method != "POST":
        return redirect("notification_list")

    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(
        is_read=True,
    )

    return redirect("notification_list")