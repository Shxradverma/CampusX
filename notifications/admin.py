from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "notification_type",
        "event",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "recipient__username",
        "recipient__email",
        "event__title",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )