from django.urls import path

from . import views


urlpatterns = [
    path(
        "event/<int:event_id>/register/",
        views.register_for_event,
        name="register_for_event",
    ),

    path(
        "event/<int:event_id>/cancel/",
        views.cancel_registration,
        name="cancel_registration",
    ),

    path(
        "event/<int:event_id>/qr/",
        views.student_event_qr,
        name="student_event_qr",
    ),

    path(
        "event/<int:event_id>/attendance/verify/",
        views.verify_attendance_qr,
        name="verify_attendance_qr",
    ),
    path(
        "event/<int:event_id>/favorite/",
        views.toggle_favorite_event,
        name="toggle_favorite_event",
    ),
path(
    "event/<int:event_id>/feedback/",
    views.submit_event_feedback,
    name="submit_event_feedback",
),
path(
    "event/<int:event_id>/certificate/",
    views.student_event_certificate,
    name="student_event_certificate",
),
path(
    "certificate/verify/",
    views.verify_certificate,
    name="verify_certificate",
),
]