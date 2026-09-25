from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class EventCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name_plural = "Event Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    class ApprovalStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField()

    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )

    venue = models.CharField(
        max_length=255,
    )

    start_datetime = models.DateTimeField()

    end_datetime = models.DateTimeField()

    registration_deadline = models.DateTimeField()

    capacity = models.PositiveIntegerField(
        default=100,
    )

    banner = models.ImageField(
        upload_to="events/banners/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.DRAFT,
    )

    submitted_for_approval_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_events",
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    rejection_reason = models.TextField(
        blank=True,
    )

    results_published = models.BooleanField(
        default=False,
    )

    results_published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self):
        return self.title

    @property
    def registration_open(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.approval_status
            == self.ApprovalStatus.APPROVED
            and timezone.now()
            <= self.registration_deadline
        )

    @property
    def can_submit_for_approval(self):
        return self.approval_status in {
            self.ApprovalStatus.DRAFT,
            self.ApprovalStatus.REJECTED,
        }

    @property
    def is_approved(self):
        return (
            self.approval_status
            == self.ApprovalStatus.APPROVED
        )


class EventTeamMember(models.Model):

    class TeamRole(models.TextChoices):
        FACULTY_COORDINATOR = (
            "FACULTY_COORDINATOR",
            "Faculty Coordinator",
        )

        EVENT_COORDINATOR = (
            "EVENT_COORDINATOR",
            "Event Coordinator",
        )

        REGISTRATION = (
            "REGISTRATION",
            "Registration Team",
        )

        ATTENDANCE = (
            "ATTENDANCE",
            "Attendance Team",
        )

        TECHNICAL = (
            "TECHNICAL",
            "Technical Team",
        )

        HOSPITALITY = (
            "HOSPITALITY",
            "Hospitality Team",
        )

        MEDIA = (
            "MEDIA",
            "Media Team",
        )

        VOLUNTEER = (
            "VOLUNTEER",
            "Volunteer",
        )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="team_members",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="team_members",
    )

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_team_assignments",
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_team_assignments",
    )

    team_role = models.CharField(
        max_length=50,
        choices=TeamRole.choices,
    )

    responsibility = models.TextField(
        blank=True,
        help_text=(
            "Specific duty or responsibility "
            "for this event."
        ),
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "team_role",
            "member__username",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "event",
                    "member",
                    "team_role",
                ],
                name="unique_event_member_team_role",
            )
        ]

    def clean(self):
        super().clean()

        if not self.member_id:
            return

        allowed_roles = {
            "TEACHER",
            "CORE_COMMITTEE",
        }

        if self.member.role not in allowed_roles:
            raise ValidationError(
                {
                    "member": (
                        "Only Teachers and Core Committee "
                        "members can be assigned to an "
                        "event team."
                    )
                }
            )

        if (
            self.team_role
            == self.TeamRole.FACULTY_COORDINATOR
            and self.member.role != "TEACHER"
        ):
            raise ValidationError(
                {
                    "team_role": (
                        "Faculty Coordinator role can only "
                        "be assigned to a Teacher."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        return super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return (
            f"{self.event.title} - "
            f"{self.member.username} - "
            f"{self.get_team_role_display()}"
        )
class EventAnnouncement(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="announcements",
    )

    title = models.CharField(
        max_length=200,
    )

    message = models.TextField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="event_announcements",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event.title} - {self.title}"
class EventFAQ(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="faqs",
    )
    question = models.CharField(
        max_length=255,
    )

    answer = models.TextField()

    is_active = models.BooleanField(
        default=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "order",
            "created_at",
        ]

    def __str__(self):
        return (
            f"{self.event.title} - "
            f"{self.question}"
        )