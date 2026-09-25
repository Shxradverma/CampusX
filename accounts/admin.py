from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CoreCommitteeProfile,
    OrganizerProfile,
    StudentProfile,
    TeacherProfile,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "CampusX Role",
            {
                "fields": ("role",),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "CampusX Information",
            {
                "fields": (
                    "email",
                    "role",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "roll_number",
        "course",
        "semester",
    )

    search_fields = (
        "full_name",
        "roll_number",
        "user__email",
    )


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "department",
        "phone",
    )

    search_fields = (
        "name",
        "department",
        "user__email",
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "employee_id",
        "department",
        "designation",
        "phone_number",
    )

    search_fields = (
        "full_name",
        "employee_id",
        "department",
        "user__username",
        "user__email",
    )

    list_filter = (
        "department",
    )


@admin.register(CoreCommitteeProfile)
class CoreCommitteeProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "member_id",
        "department",
        "position",
        "phone_number",
    )

    search_fields = (
        "full_name",
        "member_id",
        "department",
        "position",
        "user__username",
        "user__email",
    )

    list_filter = (
        "department",
        "position",
    )