import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from events.models import Event


class Registration(models.Model):

    class Status(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        CANCELLED = "CANCELLED", "Cancelled"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REGISTERED,
    )

    registered_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-registered_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["event", "student"],
                name="unique_student_event_registration",
            )
        ]

    def __str__(self):
        return f"{self.student.username} - {self.event.title}"


class Attendance(models.Model):

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="attendance",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    checked_in_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_attendances",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.registration.student.username} - "
            f"{self.registration.event.title} - "
            f"{self.status}"
        )
class FavoriteEvent(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_events",
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["student", "event"],
                name="unique_student_favorite_event",
            )
        ]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.event.title}"
        )
class EventFeedback(models.Model):

    RATING_CHOICES = [
        (1, "1 - Poor"),
        (2, "2 - Fair"),
        (3, "3 - Good"),
        (4, "4 - Very Good"),
        (5, "5 - Excellent"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_feedbacks",
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
    )

    comment = models.TextField(
        blank=True,
        max_length=1000,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["student", "event"],
                name="unique_student_event_feedback",
            )
        ]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.event.title} - "
            f"{self.rating}/5"
        )
class EventResult(models.Model):

    class Position(models.TextChoices):
        FIRST = "FIRST", "1st Place"
        SECOND = "SECOND", "2nd Place"
        THIRD = "THIRD", "3rd Place"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="results",
    )

    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="results",
    )

    position = models.CharField(
        max_length=20,
        choices=Position.choices,
    )

    prize = models.CharField(
        max_length=200,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
        max_length=1000,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    def clean(self):
        super().clean()

        if not self.event_id or not self.registration_id:
            return

        if self.registration.event_id != self.event_id:
            raise ValidationError(
                {
                    "registration": (
                        "Selected participant is not registered "
                        "for this event."
                    )
                }
            )

        if (
            self.registration.status
            != Registration.Status.REGISTERED
        ):
            raise ValidationError(
                {
                    "registration": (
                        "Only an active registered participant "
                        "can be declared as a winner."
                    )
                }
            )

    class Meta:
        ordering = ["position"]

        constraints = [
            models.UniqueConstraint(
                fields=["event", "registration"],
                name="unique_event_result_participant",
            ),
            models.UniqueConstraint(
                fields=["event", "position"],
                name="unique_event_result_position",
            ),
        ]

    def __str__(self):
        return (
            f"{self.event.title} - "
            f"{self.registration.student.username} - "
            f"{self.get_position_display()}"
        )
class Certificate(models.Model):

    certificate_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="certificate",
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
    )

    is_valid = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["-issued_at"]

    @property
    def event(self):
        return self.registration.event

    @property
    def student(self):
        return self.registration.student

    def __str__(self):
        return (
            f"{self.registration.student.username} - "
            f"{self.registration.event.title} - "
            f"{self.certificate_id}"
        )