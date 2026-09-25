from django.contrib import admin, messages
from django.utils import timezone

from .models import (
    Event,
    EventAnnouncement,
    EventCategory,
    EventFAQ,
    EventTeamMember,
)


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "organizer",
        "start_datetime",
        "status",
        "approval_status",
        "capacity",
    )

    list_filter = (
        "approval_status",
        "status",
        "category",
        "start_datetime",
    )

    search_fields = (
        "title",
        "venue",
        "organizer__username",
        "organizer__email",
    )

    # Approval status and review metadata must not
    # be changed manually from the admin form.
    readonly_fields = (
        "approval_status",
        "submitted_for_approval_at",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    actions = (
        "approve_selected_events",
        "reject_selected_events",
    )

    fieldsets = (
        (
            "Event Information",
            {
                "fields": (
                    "title",
                    "description",
                    "category",
                    "banner",
                )
            },
        ),
        (
            "Organizer & Venue",
            {
                "fields": (
                    "organizer",
                    "venue",
                )
            },
        ),
        (
            "Schedule",
            {
                "fields": (
                    "start_datetime",
                    "end_datetime",
                    "registration_deadline",
                )
            },
        ),
        (
            "Registration & Event Status",
            {
                "fields": (
                    "capacity",
                    "status",
                )
            },
        ),
        (
            "Approval Workflow",
            {
                "fields": (
                    "approval_status",
                    "submitted_for_approval_at",
                    "reviewed_by",
                    "reviewed_at",
                    "rejection_reason",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.action(
        description="Approve selected events"
    )
    def approve_selected_events(
        self,
        request,
        queryset,
    ):
        pending_events = queryset.filter(
            approval_status=Event.ApprovalStatus.PENDING,
        )

        approved_count = 0

        for event in pending_events:
            event.approval_status = (
                Event.ApprovalStatus.APPROVED
            )

            event.reviewed_by = request.user
            event.reviewed_at = timezone.now()

            # Any previous rejection reason is no
            # longer relevant after approval.
            event.rejection_reason = ""

            # Approval does not automatically publish
            # the event. Organizer must publish it.
            event.status = Event.Status.DRAFT

            event.save(
                update_fields=[
                    "approval_status",
                    "reviewed_by",
                    "reviewed_at",
                    "rejection_reason",
                    "status",
                    "updated_at",
                ]
            )

            approved_count += 1

        if approved_count:
            self.message_user(
                request,
                (
                    f"{approved_count} event(s) "
                    "approved successfully."
                ),
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                (
                    "No events were approved. "
                    "Only events with Pending Approval "
                    "status can be approved."
                ),
                level=messages.WARNING,
            )

    @admin.action(
        description="Reject selected events"
    )
    def reject_selected_events(
        self,
        request,
        queryset,
    ):
        pending_events = queryset.filter(
            approval_status=Event.ApprovalStatus.PENDING,
        )

        rejected_count = 0
        skipped_count = 0

        for event in pending_events:

            # Rejection reason is mandatory.
            # Do not modify workflow state before
            # validating the reason.
            if not event.rejection_reason.strip():
                skipped_count += 1
                continue

            event.approval_status = (
                Event.ApprovalStatus.REJECTED
            )

            event.reviewed_by = request.user
            event.reviewed_at = timezone.now()

            # Rejected events must remain private.
            event.status = Event.Status.DRAFT

            event.save(
                update_fields=[
                    "approval_status",
                    "reviewed_by",
                    "reviewed_at",
                    "rejection_reason",
                    "status",
                    "updated_at",
                ]
            )

            rejected_count += 1

        if rejected_count:
            self.message_user(
                request,
                (
                    f"{rejected_count} event(s) "
                    "rejected successfully."
                ),
                level=messages.WARNING,
            )

        if skipped_count:
            self.message_user(
                request,
                (
                    f"{skipped_count} event(s) were not rejected "
                    "because a rejection reason was not provided. "
                    "Open the event, enter a Rejection Reason, "
                    "save it, and run the reject action again."
                ),
                level=messages.WARNING,
            )

        if not rejected_count and not skipped_count:
            self.message_user(
                request,
                (
                    "No events were rejected. "
                    "Only events with Pending Approval "
                    "status can be rejected."
                ),
                level=messages.WARNING,
            )


@admin.register(EventTeamMember)
class EventTeamMemberAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "member",
        "member_role",
        "team_role",
        "assigned_at",
    )

    list_filter = (
        "team_role",
        "member__role",
        "event",
    )

    search_fields = (
        "event__title",
        "member__username",
        "member__email",
        "responsibility",
    )

    readonly_fields = (
        "assigned_at",
    )

    autocomplete_fields = (
        "event",
        "member",
    )

    fieldsets = (
        (
            "Event Assignment",
            {
                "fields": (
                    "event",
                    "member",
                    "team_role",
                )
            },
        ),
        (
            "Responsibility",
            {
                "fields": (
                    "responsibility",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "assigned_at",
                )
            },
        ),
    )

    @admin.display(
        description="CampusX Role"
    )
    def member_role(self, obj):
        return obj.member.get_role_display()

    def formfield_for_foreignkey(
        self,
        db_field,
        request,
        **kwargs,
    ):
        if db_field.name == "member":
            from accounts.models import User

            kwargs["queryset"] = User.objects.filter(
                role__in=[
                    User.Role.TEACHER,
                    User.Role.CORE_COMMITTEE,
                ],
                is_active=True,
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )


@admin.register(EventAnnouncement)
class EventAnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "event",
        "created_by",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "event__title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(EventFAQ)
class EventFAQAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "event",
        "order",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "event",
    )

    search_fields = (
        "question",
        "answer",
        "event__title",
    )

    ordering = (
        "event",
        "order",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )