from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg
from django.shortcuts import render

from accounts.models import User
from events.models import Event, EventTeamMember
from registrations.models import (
    Attendance,
    EventFeedback,
    EventResult,
    Registration,
)


@login_required
def student_dashboard(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    registrations = (
        Registration.objects
        .filter(
            student=request.user,
            status=Registration.Status.REGISTERED,
        )
        .select_related(
            "event",
            "event__category",
            "event__organizer",
        )
        .order_by("event__start_datetime")
    )

    context = {
        "registrations": registrations,
        "total_registrations": registrations.count(),
    }

    return render(
        request,
        "student/dashboard.html",
        context,
    )


@login_required
def organizer_dashboard(request):
    if request.user.role != User.Role.ORGANIZER:
        raise PermissionDenied

    events = (
        Event.objects
        .filter(organizer=request.user)
        .select_related("category")
        .order_by("-start_datetime")
    )

    registrations = Registration.objects.filter(
        event__organizer=request.user,
        status=Registration.Status.REGISTERED,
    )

    attendances = Attendance.objects.filter(
        registration__event__organizer=request.user,
        registration__status=Registration.Status.REGISTERED,
        status=Attendance.Status.PRESENT,
    )

    feedbacks = EventFeedback.objects.filter(
        event__organizer=request.user,
    )

    results = EventResult.objects.filter(
        event__organizer=request.user,
    )

    total_events = events.count()
    total_registrations = registrations.count()
    total_attendance = attendances.count()
    total_feedback = feedbacks.count()
    total_winners = results.count()

    average_rating = feedbacks.aggregate(
        average=Avg("rating")
    )["average"]

    if average_rating is not None:
        average_rating = round(average_rating, 1)
    else:
        average_rating = 0

    if total_registrations > 0:
        attendance_rate = round(
            (total_attendance / total_registrations) * 100,
            1,
        )
    else:
        attendance_rate = 0

    total_capacity = sum(
        event.capacity
        for event in events
        if event.capacity
    )

    if total_capacity > 0:
        capacity_utilization = round(
            (total_registrations / total_capacity) * 100,
            1,
        )
    else:
        capacity_utilization = 0

    event_analytics = []

    for event in events:
        event_registrations = (
            Registration.objects
            .filter(
                event=event,
                status=Registration.Status.REGISTERED,
            )
            .count()
        )

        event_attendance = (
            Attendance.objects
            .filter(
                registration__event=event,
                registration__status=Registration.Status.REGISTERED,
                status=Attendance.Status.PRESENT,
            )
            .count()
        )

        event_feedbacks = EventFeedback.objects.filter(
            event=event,
        )

        event_average_rating = (
            event_feedbacks.aggregate(
                average=Avg("rating")
            )["average"]
        )

        if event_average_rating is not None:
            event_average_rating = round(
                event_average_rating,
                1,
            )
        else:
            event_average_rating = 0

        if event_registrations > 0:
            event_attendance_rate = round(
                (event_attendance / event_registrations) * 100,
                1,
            )
        else:
            event_attendance_rate = 0

        if event.capacity:
            event_capacity_utilization = round(
                (event_registrations / event.capacity) * 100,
                1,
            )
        else:
            event_capacity_utilization = 0

        event_analytics.append(
            {
                "event": event,
                "registrations": event_registrations,
                "attendance": event_attendance,
                "attendance_rate": event_attendance_rate,
                "capacity_utilization": event_capacity_utilization,
                "feedback_count": event_feedbacks.count(),
                "average_rating": event_average_rating,
                "winner_count": (
                    EventResult.objects
                    .filter(event=event)
                    .count()
                ),
            }
        )

    context = {
        "events": events,
        "total_events": total_events,
        "total_registrations": total_registrations,
        "total_attendance": total_attendance,
        "attendance_rate": attendance_rate,
        "capacity_utilization": capacity_utilization,
        "average_rating": average_rating,
        "total_feedback": total_feedback,
        "total_winners": total_winners,
        "event_analytics": event_analytics,
    }

    return render(
        request,
        "organizer/dashboard.html",
        context,
    )


@login_required
def teacher_dashboard(request):
    if request.user.role != User.Role.TEACHER:
        raise PermissionDenied

    assignments = (
        EventTeamMember.objects
        .filter(member=request.user)
        .select_related(
            "event",
            "event__category",
            "event__organizer",
        )
        .order_by("event__start_datetime")
    )

    event_ids = assignments.values_list(
        "event_id",
        flat=True,
    ).distinct()

    registrations = Registration.objects.filter(
        event_id__in=event_ids,
        status=Registration.Status.REGISTERED,
    )

    attendances = Attendance.objects.filter(
        registration__event_id__in=event_ids,
        status=Attendance.Status.PRESENT,
    )

    context = {
        "teacher": request.user,
        "assignments": assignments,
        "total_events": event_ids.count(),
        "total_participants": registrations.count(),
        "total_attendance": attendances.count(),
    }

    return render(
        request,
        "teacher/dashboard.html",
        context,
    )


@login_required
def core_committee_dashboard(request):
    if request.user.role != User.Role.CORE_COMMITTEE:
        raise PermissionDenied

    assignments = (
        EventTeamMember.objects
        .filter(member=request.user)
        .select_related(
            "event",
            "event__category",
            "event__organizer",
        )
        .order_by("event__start_datetime")
    )

    event_ids = assignments.values_list(
        "event_id",
        flat=True,
    ).distinct()

    attendances_verified = Attendance.objects.filter(
        verified_by=request.user,
        status=Attendance.Status.PRESENT,
    ).count()

    context = {
        "committee_member": request.user,
        "assignments": assignments,
        "total_events": event_ids.count(),
        "total_duties": assignments.count(),
        "attendance_verified": attendances_verified,
    }

    return render(
        request,
        "committee/dashboard.html",
        context,
    )