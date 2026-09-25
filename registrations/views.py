import base64
from datetime import timedelta
from io import BytesIO

import qrcode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from events.models import Event
from events.permissions import can_scan_attendance
from notifications.models import Notification
from .forms import EventFeedbackForm

from .models import (
    Attendance,
    Certificate,
    EventFeedback,
    FavoriteEvent,
    Registration,
)
from .utils import (
    generate_attendance_token,
    verify_attendance_token,
)


@login_required
def register_for_event(request, event_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "student_event_detail",
            event_id=event_id,
        )

    event = get_object_or_404(
        Event,
        id=event_id,
        status=Event.Status.PUBLISHED,
        approval_status=Event.ApprovalStatus.APPROVED,
    )

    now = timezone.now()

    if now >= event.start_datetime:
        messages.error(
            request,
            "Registration is not available after the event has started.",
        )

        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    if now > event.registration_deadline:
        messages.error(
            request,
            "Registration for this event has closed.",
        )

        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    existing_registration = Registration.objects.filter(
        event=event,
        student=request.user,
    ).first()

    if (
        existing_registration
        and existing_registration.status
        == Registration.Status.REGISTERED
    ):
        messages.warning(
            request,
            "You are already registered for this event.",
        )

        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    with transaction.atomic():
        locked_event = get_object_or_404(
            Event.objects.select_for_update(),
            id=event.id,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        now = timezone.now()

        if now >= locked_event.start_datetime:
            messages.error(
                request,
                "Registration is not available after the event has started.",
            )

            return redirect(
                "student_event_detail",
                event_id=locked_event.id,
            )

        if now > locked_event.registration_deadline:
            messages.error(
                request,
                "Registration for this event has closed.",
            )

            return redirect(
                "student_event_detail",
                event_id=locked_event.id,
            )

        registered_count = Registration.objects.filter(
            event=locked_event,
            status=Registration.Status.REGISTERED,
        ).count()

        if registered_count >= locked_event.capacity:
            messages.error(
                request,
                "Sorry, this event is full.",
            )

            return redirect(
                "student_event_detail",
                event_id=locked_event.id,
            )

        if existing_registration:
            existing_registration.status = (
                Registration.Status.REGISTERED
            )

            existing_registration.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        else:
            Registration.objects.create(
                event=locked_event,
                student=request.user,
                status=Registration.Status.REGISTERED,
            )
    Notification.objects.create(
        recipient=request.user,
        notification_type=Notification.Type.REGISTRATION,
        event=event,
        title="Event Registration Confirmed",
        message=(
            f"You have successfully registered for "
            f"{event.title}."
        ),
    )
    # Send registration confirmation email.
    if request.user.email:
        send_mail(
            subject=f"Registration Confirmed - {event.title}",
            message=(
                f"Hello {request.user.username},\n\n"
                f"Your registration for {event.title} "
                f"has been confirmed successfully.\n\n"
                f"Venue: {event.venue}\n"
                f"Date: "
                f"{timezone.localtime(event.start_datetime).strftime('%d %B %Y')}\n"
                f"Time: "
                f"{timezone.localtime(event.start_datetime).strftime('%I:%M %p')}\n\n"
                f"Thank you for using CampusX.\n\n"
                f"CampusX Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )
    messages.success(
        request,
        "You have successfully registered for this event.",
    )

    return redirect(
        "student_event_detail",
        event_id=event.id,
    )


@login_required
def cancel_registration(request, event_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "student_event_detail",
            event_id=event_id,
        )

    registration = get_object_or_404(
        Registration.objects.select_related(
            "event"
        ),
        event_id=event_id,
        student=request.user,
        status=Registration.Status.REGISTERED,
    )

    if timezone.now() >= registration.event.start_datetime:
        messages.error(
            request,
            (
                "Registration cannot be cancelled "
                "after the event has started."
            ),
        )

        return redirect(
            "student_event_detail",
            event_id=event_id,
        )

    registration.status = Registration.Status.CANCELLED

    registration.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            "Your event registration has been "
            "cancelled successfully."
        ),
    )

    return redirect(
        "student_event_detail",
        event_id=event_id,
    )


@login_required
def student_event_qr(request, event_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    registration = get_object_or_404(
        Registration.objects.select_related(
            "event",
            "student",
        ),
        event_id=event_id,
        student=request.user,
        status=Registration.Status.REGISTERED,
    )

    event = registration.event

    if (
        event.status != Event.Status.PUBLISHED
        or event.approval_status
        != Event.ApprovalStatus.APPROVED
    ):
        raise PermissionDenied

    token = generate_attendance_token(
        registration
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )

    qr.add_data(token)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    qr_code = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return render(
        request,
        "registrations/student_qr.html",
        {
            "registration": registration,
            "qr_code": qr_code,
        },
    )


@login_required
def verify_attendance_qr(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related(
            "organizer",
            "category",
        ),
        id=event_id,
    )

    if not can_scan_attendance(
        request.user,
        event,
    ):
        raise PermissionDenied

    if (
        event.status != Event.Status.PUBLISHED
        or event.approval_status
        != Event.ApprovalStatus.APPROVED
    ):
        messages.error(
            request,
            (
                "Attendance is available only for "
                "approved and published events."
            ),
        )

        return redirect(
            "event_detail",
            event_id=event.id,
        )

    context = {
        "event": event,
    }

    if request.method == "POST":
        token = request.POST.get(
            "token",
            "",
        ).strip()

        if not token:
            messages.error(
                request,
                "Please provide a QR token.",
            )

            return redirect(
                "verify_attendance_qr",
                event_id=event.id,
            )

        data = verify_attendance_token(
            token
        )

        if not data:
            messages.error(
                request,
                "Invalid or expired attendance QR code.",
            )

            return redirect(
                "verify_attendance_qr",
                event_id=event.id,
            )

        if data.get("event_id") != event.id:
            messages.error(
                request,
                (
                    "This QR code belongs to a different "
                    "event and cannot be used here."
                ),
            )

            return redirect(
                "verify_attendance_qr",
                event_id=event.id,
            )

        registration = get_object_or_404(
            Registration.objects.select_related(
                "student",
                "student__student_profile",
                "event",
            ),
            id=data.get("registration_id"),
            event=event,
            student_id=data.get("student_id"),
        )

        if (
            registration.status
            != Registration.Status.REGISTERED
        ):
            messages.error(
                request,
                "This registration is not active.",
            )

            return redirect(
                "verify_attendance_qr",
                event_id=event.id,
            )

        now = timezone.now()

        attendance_open_time = (
            event.start_datetime
            - timedelta(minutes=30)
        )

        if now < attendance_open_time:
            messages.error(
                request,
                (
                    "Attendance is not open yet. "
                    "Check-in opens 30 minutes "
                    "before the event starts."
                ),
            )

            return redirect(
                "verify_attendance_qr",
                event_id=event.id,
            )

        if now > event.end_datetime:
            messages.error(
                request,
                "Attendance for this event has closed.",
            )

            return redirect(
                "verify_attendance_qr",
                event_id=event.id,
            )

        attendance, created = Attendance.objects.get_or_create(
            registration=registration,
            defaults={
                "status": Attendance.Status.PRESENT,
                "checked_in_at": now,
                "verified_by": request.user,
            },
        )

        if created:
            messages.success(
                request,
                "Attendance marked successfully.",
            )

        else:
            messages.warning(
                request,
                (
                    "Attendance has already been "
                    "marked for this student."
                ),
            )

        context["attendance"] = attendance
        context["registration"] = registration

    return render(
        request,
        "registrations/verify_qr.html",
        context,
    )
@login_required
def toggle_favorite_event(request, event_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "student_event_detail",
            event_id=event_id,
        )

    event = get_object_or_404(
        Event,
        id=event_id,
        status=Event.Status.PUBLISHED,
        approval_status=Event.ApprovalStatus.APPROVED,
    )

    favorite = FavoriteEvent.objects.filter(
        student=request.user,
        event=event,
    ).first()

    if favorite:
        favorite.delete()

        messages.success(
            request,
            "Event removed from favorites.",
        )
    else:
        FavoriteEvent.objects.create(
            student=request.user,
            event=event,
        )

        messages.success(
            request,
            "Event added to favorites.",
        )

    return redirect(
        "student_event_detail",
        event_id=event.id,
    )
@login_required
def submit_event_feedback(request, event_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    event = get_object_or_404(
        Event,
        id=event_id,
        status=Event.Status.PUBLISHED,
        approval_status=Event.ApprovalStatus.APPROVED,
    )

    registration = Registration.objects.filter(
        event=event,
        student=request.user,
        status=Registration.Status.REGISTERED,
    ).first()

    if registration is None:
        messages.error(
            request,
            "You can only give feedback for events you registered for.",
        )
        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    if timezone.now() < event.end_datetime:
        messages.warning(
            request,
            "Feedback will be available after the event has ended.",
        )
        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    existing_feedback = EventFeedback.objects.filter(
        event=event,
        student=request.user,
    ).first()

    if existing_feedback:
        messages.info(
            request,
            "You have already submitted feedback for this event.",
        )
        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    if request.method == "POST":
        form = EventFeedbackForm(request.POST)

        if form.is_valid():
            feedback = form.save(commit=False)

            feedback.event = event
            feedback.student = request.user

            feedback.save()

            messages.success(
                request,
                "Thank you! Your feedback has been submitted.",
            )

            return redirect(
                "student_event_detail",
                event_id=event.id,
            )

    else:
        form = EventFeedbackForm()

    return render(
        request,
        "registrations/event_feedback.html",
        {
            "event": event,
            "form": form,
        },
    )
@login_required
def student_event_certificate(request, event_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    event = get_object_or_404(
        Event,
        id=event_id,
    )

    registration = get_object_or_404(
        Registration.objects.select_related(
            "student",
            "student__student_profile",
            "event",
        ),
        event=event,
        student=request.user,
        status=Registration.Status.REGISTERED,
    )

    # Certificate is available only after the event ends.
    if timezone.now() < event.end_datetime:
        messages.error(
            request,
            "Certificate will be available after the event is completed.",
        )
        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    try:
        attendance = registration.attendance
    except Attendance.DoesNotExist:
        attendance = None

    # Only students marked PRESENT are eligible.
    if (
        attendance is None
        or attendance.status != Attendance.Status.PRESENT
    ):
        messages.error(
            request,
            "Certificate is available only for students who attended the event.",
        )
        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    certificate, created = Certificate.objects.get_or_create(
        registration=registration,
    )
    # Send certificate email only when the certificate
    # is created for the first time.
    if created and request.user.email:
        send_mail(
            subject=f"Certificate Available - {event.title}",
            message=(
                f"Hello {request.user.username},\n\n"
                f"Your participation certificate for "
                f"{event.title} is now available on CampusX.\n\n"
                f"Certificate ID: {certificate.certificate_id}\n\n"
                f"Log in to CampusX and open the event page "
                f"to view or print your certificate.\n\n"
                f"CampusX Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )
    if not certificate.is_valid:
        messages.error(
            request,
            "This certificate is currently invalid.",
        )
        return redirect(
            "student_event_detail",
            event_id=event.id,
        )

    context = {
        "event": event,
        "registration": registration,
        "certificate": certificate,
        "student_profile": request.user.student_profile,
    }

    return render(
        request,
        "registrations/certificate.html",
        context,
    )
def verify_certificate(request):
    certificate = None
    searched = False
    invalid_id = False

    certificate_id = request.GET.get(
        "certificate_id",
        "",
    ).strip()

    if certificate_id:
        searched = True

        try:
            certificate = (
                Certificate.objects
                .select_related(
                    "registration",
                    "registration__student",
                    "registration__student__student_profile",
                    "registration__event",
                )
                .get(
                    certificate_id=certificate_id,
                    is_valid=True,
                )
            )

        except (
            Certificate.DoesNotExist,
            ValidationError,
            ValueError,
        ):
            invalid_id = True

    context = {
        "certificate": certificate,
        "certificate_id": certificate_id,
        "searched": searched,
        "invalid_id": invalid_id,
    }

    return render(
        request,
        "registrations/verify_certificate.html",
        context,
    )