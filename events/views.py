import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.core.mail import send_mass_mail
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification
from registrations.forms import EventResultForm
from registrations.models import (
    EventFeedback,
    EventResult,
    FavoriteEvent,
    Registration,
)

from .forms import (
    EventAnnouncementForm,
    EventFAQForm,
    EventForm,
    EventTeamMemberForm,
)
from .models import (
    Event,
    EventAnnouncement,
    EventFAQ,
    EventTeamMember,
)
from .permissions import (
    can_delete_event,
    can_edit_event,
    can_scan_attendance,
    can_view_event_management,
    can_view_participants,
)


@login_required
def create_event(request):
    if request.user.role != User.Role.ORGANIZER:
        raise PermissionDenied

    if request.method == "POST":
        form = EventForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            event = form.save(commit=False)

            event.organizer = request.user

            # New events always begin inside
            # the approval workflow as Draft.
            event.approval_status = (
                Event.ApprovalStatus.DRAFT
            )

            # An unapproved event must not
            # become publicly published.
            event.status = Event.Status.DRAFT

            event.save()

            messages.success(
                request,
                (
                    "Event created successfully. "
                    "Review the event and submit it "
                    "for approval when ready."
                ),
            )

            return redirect(
                "event_detail",
                event_id=event.id,
            )

    else:
        form = EventForm()

    return render(
        request,
        "events/create_event.html",
        {
            "form": form,
        },
    )


@login_required
def edit_event(request, event_id):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if (
        event.approval_status
        == Event.ApprovalStatus.PENDING
    ):
        messages.warning(
            request,
            (
                "This event is currently pending approval "
                "and cannot be edited."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if request.method == "POST":
        form = EventForm(
            request.POST,
            request.FILES,
            instance=event,
        )

        if form.is_valid():
            updated_event = form.save(
                commit=False
            )

            # Any organizer edit invalidates the
            # previous approval. The updated event
            # must be reviewed again.
            if (
                event.approval_status
                == Event.ApprovalStatus.APPROVED
            ):
                updated_event.approval_status = (
                    Event.ApprovalStatus.DRAFT
                )

                updated_event.status = (
                    Event.Status.DRAFT
                )

                updated_event.submitted_for_approval_at = None
                updated_event.reviewed_by = None
                updated_event.reviewed_at = None
                updated_event.rejection_reason = ""

                messages.info(
                    request,
                    (
                        "The event was updated. "
                        "Because an approved event was changed, "
                        "it must be submitted for approval again."
                    ),
                )

            else:
                updated_event.status = (
                    Event.Status.DRAFT
                )

            updated_event.save()

            messages.success(
                request,
                "Event updated successfully.",
            )

            return redirect(
                "event_detail",
                event_id=event.id,
            )

    else:
        form = EventForm(
            instance=event,
        )

    return render(
        request,
        "events/edit_event.html",
        {
            "form": form,
            "event": event,
        },
    )


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_delete_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method == "POST":
        event_title = event.title

        event.delete()

        messages.success(
            request,
            f'"{event_title}" deleted successfully.',
        )

        return redirect(
            "organizer_dashboard"
        )

    return render(
        request,
        "events/delete_event.html",
        {
            "event": event,
        },
    )


@login_required
def submit_event_for_approval(
    request,
    event_id,
):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if not event.can_submit_for_approval:
        messages.warning(
            request,
            (
                "This event cannot currently be "
                "submitted for approval."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if event.start_datetime <= timezone.now():
        messages.error(
            request,
            (
                "An event that has already started "
                "cannot be submitted for approval."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if (
        event.registration_deadline
        >= event.start_datetime
    ):
        messages.error(
            request,
            (
                "Registration deadline must be "
                "before the event start time."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    event.approval_status = (
        Event.ApprovalStatus.PENDING
    )

    event.submitted_for_approval_at = (
        timezone.now()
    )

    event.reviewed_by = None
    event.reviewed_at = None
    event.rejection_reason = ""

    # Pending events must never be visible
    # in the student event catalogue.
    event.status = Event.Status.DRAFT

    event.save(
        update_fields=[
            "approval_status",
            "submitted_for_approval_at",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            "Event submitted for approval successfully. "
            "You can publish it after administrator approval."
        ),
    )

    return redirect(
        "event_detail",
        event_id=event.id,
    )


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "category",
            "organizer",
            "reviewed_by",
        ),
        id=event_id,
    )

    if not can_view_event_management(
        request.user,
        event,
    ):
        raise PermissionDenied

    context = {
        "event": event,
        "can_edit": can_edit_event(
            request.user,
            event,
        ),
        "can_delete": can_delete_event(
            request.user,
            event,
        ),
        "can_scan": can_scan_attendance(
            request.user,
            event,
        ),
        "can_submit_for_approval": (
            can_edit_event(
                request.user,
                event,
            )
            and event.can_submit_for_approval
        ),
    }

    return render(
        request,
        "events/event_detail.html",
        context,
    )
@login_required
def manage_event_results(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "organizer",
            "category",
        ),
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    results = (
        EventResult.objects
        .filter(event=event)
        .select_related(
            "registration",
            "registration__student",
            "registration__student__student_profile",
        )
        .order_by("position")
    )

    if request.method == "POST":
        if event.results_published:
            messages.error(
                request,
                (
                    "Published results cannot be changed. "
                    "No new winner can be added."
                ),
            )

            return redirect(
                "manage_event_results",
                event_id=event.id,
            )

        form = EventResultForm(
            request.POST,
            event=event,
        )

        if form.is_valid():
            result = form.save(commit=False)
            result.event = event

            participant_exists = (
                EventResult.objects
                .filter(
                    event=event,
                    registration=result.registration,
                )
                .exists()
            )

            if participant_exists:
                form.add_error(
                    "registration",
                    (
                        "This participant has already been "
                        "declared in the event results."
                    ),
                )

            position_exists = (
                EventResult.objects
                .filter(
                    event=event,
                    position=result.position,
                )
                .exists()
            )

            if position_exists:
                form.add_error(
                    "position",
                    (
                        "This winning position has already "
                        "been assigned."
                    ),
                )

            if not form.errors:
                result.full_clean()
                result.save()

                messages.success(
                    request,
                    (
                        f"{result.get_position_display()} "
                        "declared successfully."
                    ),
                )

                return redirect(
                    "manage_event_results",
                    event_id=event.id,
                )

    else:
        form = EventResultForm(
            event=event,
        )

    context = {
        "event": event,
        "form": form,
        "results": results,
    }

    return render(
        request,
        "events/manage_event_results.html",
        context,
    )


@login_required
def publish_event_results(request, event_id):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method != "POST":
        raise PermissionDenied

    if timezone.now() < event.end_datetime:
        messages.error(
            request,
            "Results cannot be published before the event ends.",
        )

        return redirect(
            "manage_event_results",
            event_id=event.id,
        )

    if not EventResult.objects.filter(
        event=event,
    ).exists():
        messages.error(
            request,
            (
                "Declare at least one winner "
                "before publishing results."
            ),
        )

        return redirect(
            "manage_event_results",
            event_id=event.id,
        )

    if event.results_published:
        messages.info(
            request,
            "Results are already published.",
        )

        return redirect(
            "manage_event_results",
            event_id=event.id,
        )

    event.results_published = True
    event.results_published_at = timezone.now()

    event.save(
        update_fields=[
            "results_published",
            "results_published_at",
        ]
    )

    registered_students = (
        Registration.objects
        .filter(
            event=event,
            status=Registration.Status.REGISTERED,
        )
        .select_related("student")
    )

    notifications_to_create = [
        Notification(
            recipient=registration.student,
            notification_type=Notification.Type.RESULT,
            event=event,
            title="Event Results Published",
            message=(
                f"Results for {event.title} "
                "have been published. "
                "Check the event page to view the results."
            ),
        )
        for registration in registered_students
    ]

    if notifications_to_create:
        Notification.objects.bulk_create(
            notifications_to_create
        )
    # Send result published emails to registered students.
    email_messages = []

    for registration in registered_students:
        student = registration.student

        if not student.email:
            continue

        email_messages.append(
            (
                f"Results Published - {event.title}",
                (
                    f"Hello {student.username},\n\n"
                    f"The results for {event.title} "
                    f"have been published.\n\n"
                    f"Please log in to CampusX and open the "
                    f"event page to view the results.\n\n"
                    f"Thank you for participating.\n\n"
                    f"CampusX Team"
                ),
                settings.DEFAULT_FROM_EMAIL,
                [student.email],
            )
        )

    if email_messages:
        send_mass_mail(
            email_messages,
            fail_silently=True,
        )

    messages.success(
        request,
        "Event results published successfully.",
    )

    return redirect(
        "manage_event_results",
        event_id=event.id,
    )


@login_required
def remove_event_result(request, event_id, result_id):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method != "POST":
        raise PermissionDenied

    if event.results_published:
        messages.error(
            request,
            (
                "Published results cannot be changed. "
                "The winner was not removed."
            ),
        )

        return redirect(
            "manage_event_results",
            event_id=event.id,
        )

    result = get_object_or_404(
        EventResult,
        id=result_id,
        event=event,
    )
@login_required
def event_feedback_dashboard(request, event_id):

    position = result.get_position_display()

    result.delete()

    messages.success(
        request,
        f"{position} winner removed successfully.",
    )

    return redirect(
        "manage_event_results",
        event_id=event.id,
    )
@login_required
def event_feedback_dashboard(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "category",
            "organizer",
        ),
        id=event_id,
    )

    # Feedback analytics are part of event management.
    # Only users authorized to manage/view this event
    # can access this page.
    if not can_view_event_management(
        request.user,
        event,
    ):
        raise PermissionDenied

    feedbacks = (
        EventFeedback.objects
        .filter(event=event)
        .select_related(
            "student",
            "student__student_profile",
        )
        .order_by("-created_at")
    )

    summary = feedbacks.aggregate(
        average_rating=Avg("rating"),
        total_reviews=Count("id"),
    )

    average_rating = (
        round(summary["average_rating"], 1)
        if summary["average_rating"] is not None
        else 0
    )

    total_reviews = summary["total_reviews"]

    rating_counts = {
        rating: feedbacks.filter(
            rating=rating
        ).count()
        for rating in range(5, 0, -1)
    }

    rating_distribution = []

    for rating in range(5, 0, -1):
        count = rating_counts[rating]

        percentage = (
            round(
                (count / total_reviews) * 100,
                1,
            )
            if total_reviews
            else 0
        )

        rating_distribution.append(
            {
                "rating": rating,
                "count": count,
                "percentage": percentage,
            }
        )

    context = {
        "event": event,
        "feedbacks": feedbacks,
        "average_rating": average_rating,
        "total_reviews": total_reviews,
        "rating_distribution": rating_distribution,
    }

    return render(
        request,
        "events/event_feedback_dashboard.html",
        context,
    )
@login_required
def event_participants(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "category",
            "organizer",
        ),
        id=event_id,
    )

    if not can_view_participants(
        request.user,
        event,
    ):
        raise PermissionDenied

    all_registrations = (
        Registration.objects
        .filter(
            event=event,
            status=Registration.Status.REGISTERED,
        )
        .select_related(
            "student",
            "student__student_profile",
        )
    )

    total_registered = (
        all_registrations.count()
    )

    total_present = (
        all_registrations
        .filter(
            attendance__status="PRESENT",
        )
        .count()
    )

    total_absent = (
        total_registered
        - total_present
    )

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    registrations = all_registrations

    if search_query:
        registrations = registrations.filter(
            Q(
                student__username__icontains=
                search_query
            )
            |
            Q(
                student__email__icontains=
                search_query
            )
            |
            Q(
                student__student_profile__full_name__icontains=
                search_query
            )
            |
            Q(
                student__student_profile__roll_number__icontains=
                search_query
            )
        )

    registrations = registrations.order_by(
        "student__username"
    )

    context = {
        "event": event,
        "registrations": registrations,
        "total_registered": total_registered,
        "total_present": total_present,
        "total_absent": total_absent,
        "search_query": search_query,
        "can_edit": can_edit_event(
            request.user,
            event,
        ),
        "can_delete": can_delete_event(
            request.user,
            event,
        ),
        "can_scan": can_scan_attendance(
            request.user,
            event,
        ),
    }

    return render(
        request,
        "events/event_participants.html",
        context,
    )
@login_required
def export_event_participants_csv(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "category",
            "organizer",
        ),
        id=event_id,
    )

    if not can_view_participants(
        request.user,
        event,
    ):
        raise PermissionDenied

    registrations = (
        Registration.objects
        .filter(
            event=event,
            status=Registration.Status.REGISTERED,
        )
        .select_related(
            "student",
            "student__student_profile",
            "attendance",
        )
        .order_by("student__username")
    )

    safe_event_name = "".join(
        character
        if character.isalnum()
        else "_"
        for character in event.title
    ).strip("_")

    response = HttpResponse(
        content_type="text/csv; charset=utf-8",
    )

    response["Content-Disposition"] = (
        'attachment; filename="'
        f'{safe_event_name}_participants.csv"'
    )

    # UTF-8 BOM helps Excel display Unicode correctly.
    response.write("\ufeff")

    writer = csv.writer(response)

    writer.writerow(
        [
            "Username",
            "Full Name",
            "Email",
            "Roll Number",
            "Course",
            "Registration Status",
            "Registered At",
            "Attendance",
            "Checked In At",
        ]
    )

    for registration in registrations:
        student = registration.student

        try:
            profile = student.student_profile
        except User.student_profile.RelatedObjectDoesNotExist:
            profile = None

        attendance = getattr(
            registration,
            "attendance",
            None,
        )

        if attendance:
            attendance_status = (
                attendance.get_status_display()
            )

            checked_in_at = attendance.checked_in_at

            if checked_in_at:
                checked_in_at = timezone.localtime(
                    checked_in_at
                ).strftime(
                    "%d-%m-%Y %I:%M %p"
                )
            else:
                checked_in_at = ""

        else:
            attendance_status = "Absent"
            checked_in_at = ""

        registered_at = timezone.localtime(
            registration.registered_at
        ).strftime(
            "%d-%m-%Y %I:%M %p"
        )

        writer.writerow(
            [
                student.username,
                (
                    profile.full_name
                    if profile
                    else student.get_full_name()
                ),
                student.email,
                (
                    profile.roll_number
                    if profile
                    else ""
                ),
                (
                    profile.course
                    if profile
                    else ""
                ),
                registration.get_status_display(),
                registered_at,
                attendance_status,
                checked_in_at,
            ]
        )

    return response

@login_required
def manage_event_team(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "category",
            "organizer",
        ),
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = EventTeamMemberForm(
            request.POST,
            event=event,
        )

        if form.is_valid():
            team_member = form.save(
                commit=False
            )

            team_member.event = event
            team_member.save()

            messages.success(
                request,
                (
                    f"{team_member.member.username} "
                    "has been added to the event team."
                ),
            )

            return redirect(
                "manage_event_team",
                event_id=event.id,
            )

    else:
        form = EventTeamMemberForm(
            event=event,
        )

    team_members = (
        EventTeamMember.objects
        .filter(
            event=event,
        )
        .select_related(
            "member",
        )
        .order_by(
            "team_role",
            "member__username",
        )
    )

    context = {
        "event": event,
        "form": form,
        "team_members": team_members,
        "total_team_members": (
            team_members.count()
        ),
    }

    return render(
        request,
        "events/manage_event_team.html",
        context,
    )


@login_required
def remove_event_team_member(
    request,
    event_id,
    assignment_id,
):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "manage_event_team",
            event_id=event.id,
        )

    assignment = get_object_or_404(
        EventTeamMember.objects.select_related(
            "member",
        ),
        id=assignment_id,
        event=event,
    )

    member_name = (
        assignment.member.username
    )

    role_name = (
        assignment.get_team_role_display()
    )

    assignment.delete()

    messages.success(
        request,
        (
            f"{member_name} has been removed "
            f"from {role_name}."
        ),
    )

    return redirect(
        "manage_event_team",
        event_id=event.id,
    )


@login_required
def student_event_list(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    events = (
        Event.objects
        .filter(
            status=Event.Status.PUBLISHED,
            approval_status=(
                Event.ApprovalStatus.APPROVED
            ),
        )
        .select_related(
            "category",
            "organizer",
        )
        .order_by(
            "start_datetime",
        )
    )

    return render(
        request,
        "events/student_event_list.html",
        {
            "events": events,
        },
    )


@login_required
def student_event_detail(
    request,
    event_id,
):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    event = get_object_or_404(
        Event.objects.select_related(
            "category",
            "organizer",
        ),
        id=event_id,
        status=Event.Status.PUBLISHED,
        approval_status=(
            Event.ApprovalStatus.APPROVED
        ),
    )

    is_registered = (
        Registration.objects
        .filter(
            event=event,
            student=request.user,
            status=Registration.Status.REGISTERED,
        )
        .exists()
    )
    is_favorite = FavoriteEvent.objects.filter(
        event=event,
        student=request.user,
    ).exists()
    is_favorite = FavoriteEvent.objects.filter(
        event=event,
        student=request.user,
    ).exists()
    has_feedback = EventFeedback.objects.filter(
        event=event,
        student=request.user,
    ).exists()

    can_give_feedback = (
        is_registered
        and timezone.now() >= event.end_datetime
        and not has_feedback
    )

    announcements = EventAnnouncement.objects.filter(
        event=event,
        is_active=True,
    ).select_related(
        "created_by",
    )
    faqs = EventFAQ.objects.filter(
        event=event,
        is_active=True,
    )
    published_results = EventResult.objects.none()

    if event.results_published:
        published_results = (
            EventResult.objects
            .filter(event=event)
            .select_related(
                "registration",
                "registration__student",
                "registration__student__student_profile",
            )
            .order_by("position")
        )
    return render(
        request,
        "events/student_event_detail.html",
        {
            "event": event,
            "is_registered": is_registered,
            "is_favorite": is_favorite,
            "announcements": announcements,
            "faqs": faqs,
            "has_feedback": has_feedback,
            "can_give_feedback": can_give_feedback,
            "published_results": published_results,
        },
    )
@login_required
def publish_event(request, event_id):
    event = get_object_or_404(
        Event,
        id=event_id,
    )

    if not can_edit_event(
        request.user,
        event,
    ):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if (
        event.approval_status
        != Event.ApprovalStatus.APPROVED
    ):
        messages.error(
            request,
            (
                "This event cannot be published "
                "until it is approved by an administrator."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if event.status == Event.Status.PUBLISHED:
        messages.warning(
            request,
            "This event is already published.",
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if event.start_datetime <= timezone.now():
        messages.error(
            request,
            (
                "An event that has already started "
                "cannot be published."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    if (
        event.registration_deadline
        <= timezone.now()
    ):
        messages.error(
            request,
            (
                "This event cannot be published because "
                "its registration deadline has passed."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    event.status = Event.Status.PUBLISHED

    event.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            "Event published successfully. "
            "Students can now discover and register "
            "for this event."
        ),
    )

    return redirect(
        "event_detail",
        event_id=event.id,
    )
@login_required
def create_event_announcement(request, event_id):
    if request.user.role != User.Role.ORGANIZER:
        raise PermissionDenied

    event = get_object_or_404(
        Event,
        id=event_id,
        organizer=request.user,
    )

    if request.method == "POST":
        form = EventAnnouncementForm(request.POST)

        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.event = event
            announcement.created_by = request.user
            announcement.save()

            registered_students = (
                Registration.objects
                .filter(
                    event=event,
                    status=Registration.Status.REGISTERED,
                )
                .select_related("student")
            )

            notifications_to_create = [
                Notification(
                    recipient=registration.student,
                    notification_type=(
                        Notification.Type.ANNOUNCEMENT
                    ),
                    event=event,
                    title=announcement.title,
                    message=announcement.message,
                )
                for registration in registered_students
            ]

            if notifications_to_create:
                Notification.objects.bulk_create(
                    notifications_to_create
                )
            # Send announcement emails to registered students.
            email_messages = []

            for registration in registered_students:
                student = registration.student

                if not student.email:
                    continue

                email_messages.append(
                    (
                        f"CampusX Announcement - {event.title}",
                        (
                            f"Hello {student.username},\n\n"
                            f"There is a new announcement for "
                            f"{event.title}.\n\n"
                            f"{announcement.title}\n\n"
                            f"{announcement.message}\n\n"
                            f"Venue: {event.venue}\n\n"
                            f"Please check CampusX for more details.\n\n"
                            f"CampusX Team"
                        ),
                        settings.DEFAULT_FROM_EMAIL,
                        [student.email],
                    )
                )

            if email_messages:
                send_mass_mail(
                    email_messages,
                    fail_silently=True,
                )

            messages.success(
                request,
                "Announcement published successfully.",
            )

            return redirect(
                "event_detail",
                event_id=event.id,
            )

    else:
        form = EventAnnouncementForm()

    return render(
        request,
        "events/create_announcement.html",
        {
            "event": event,
            "form": form,
        },
    )


@login_required
def create_event_faq(request, event_id):
    if request.user.role != User.Role.ORGANIZER:
        raise PermissionDenied

    event = get_object_or_404(
        Event,
        id=event_id,
        organizer=request.user,
    )

    if request.method == "POST":
        form = EventFAQForm(request.POST)

        if form.is_valid():
            faq = form.save(commit=False)
            faq.event = event
            faq.save()

            messages.success(
                request,
                "FAQ added successfully.",
            )

            return redirect(
                "event_detail",
                event_id=event.id,
            )

    else:
        form = EventFAQForm()

    return render(
        request,
        "events/create_faq.html",
        {
            "event": event,
            "form": form,
        },
    )