from django.urls import path

from . import views


urlpatterns = [
    path(
        "student/",
        views.student_dashboard,
        name="student_dashboard",
    ),

    path(
        "organizer/",
        views.organizer_dashboard,
        name="organizer_dashboard",
    ),

    path(
        "teacher/",
        views.teacher_dashboard,
        name="teacher_dashboard",
    ),

    path(
        "committee/",
        views.core_committee_dashboard,
        name="core_committee_dashboard",
    ),
]