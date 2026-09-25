from django.conf import settings
from django.db import models

from events.models import Event


class Notification(models.Model):

    class Type(models.TextChoices):
        REGISTRATION = (
            "REGISTRATION",
            "Registration",
        )

        ANNOUNCEMENT = (
            "ANNOUNCEMENT",
            "Announcement",
        )

        EVENT_UPDATE = (
            "EVENT_UPDATE",
            "Event Update",
        )

        RESULT = (
            "RESULT",
            "Result",
        )

        GENERAL = (
            "GENERAL",
            "General",
        )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.GENERAL,
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=200,
    )

    message = models.TextField(
        max_length=1000,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.recipient.username} - "
            f"{self.title}"
        )