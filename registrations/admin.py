from django.contrib import admin

from .models import Attendance, EventFeedback, Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_username",
        "event_title",
        "status",
        "registered_at",
    )

    list_filter = (
        "status",
        "event",
        "registered_at",
    )

    search_fields = (
        "student__username",
        "student__email",
        "event__title",
    )

    readonly_fields = (
        "registered_at",
        "updated_at",
    )

    list_select_related = (
        "student",
        "event",
    )

    def student_username(self, obj):
        return obj.student.username

    student_username.short_description = "Student"

    def event_title(self, obj):
        return obj.event.title

    event_title.short_description = "Event"


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_username",
        "event_title",
        "status",
        "checked_in_at",
        "verified_by",
    )

    list_filter = (
        "status",
        "checked_in_at",
        "registration__event",
    )

    search_fields = (
        "registration__student__username",
        "registration__student__email",
        "registration__event__title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "registration",
        "registration__student",
        "registration__event",
        "verified_by",
    )

    def student_username(self, obj):
        return obj.registration.student.username

    student_username.short_description = "Student"

    def event_title(self, obj):
        return obj.registration.event.title

    event_title.short_description = "Event"
@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "student_username",
        "event_title",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
        "event",
        "created_at",
    )

    search_fields = (
        "student__username",
        "student__email",
        "event__title",
        "comment",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "student",
        "event",
    )

    def student_username(self, obj):
        return obj.student.username

    student_username.short_description = "Student"

    def event_title(self, obj):
        return obj.event.title

    event_title.short_description = "Event"