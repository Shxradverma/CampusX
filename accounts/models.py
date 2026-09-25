from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        CORE_COMMITTEE = "CORE_COMMITTEE", "Core Committee Member"
        ORGANIZER = "ORGANIZER", "Organizer"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    full_name = models.CharField(max_length=150)

    roll_number = models.CharField(
        max_length=50,
        unique=True,
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
    )

    course = models.CharField(
        max_length=100,
        blank=True,
    )

    semester = models.CharField(
        max_length=30,
        blank=True,
    )

    profile_photo = models.ImageField(
        upload_to="profiles/students/",
        blank=True,
        null=True,
    )

    interests = models.TextField(
        blank=True,
        help_text="Example: Python, AI, Machine Learning",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.full_name


class OrganizerProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="organizer_profile",
    )

    name = models.CharField(
        max_length=150,
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
    )

    profile_image = models.ImageField(
        upload_to="profiles/organizers/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name
class TeacherProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )

    full_name = models.CharField(max_length=150)

    employee_id = models.CharField(
        max_length=50,
        unique=True,
    )

    department = models.CharField(
        max_length=100,
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
    )

    profile_photo = models.ImageField(
        upload_to="profiles/teachers/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.full_name


class CoreCommitteeProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="core_committee_profile",
    )

    full_name = models.CharField(max_length=150)

    member_id = models.CharField(
        max_length=50,
        unique=True,
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
    )

    position = models.CharField(
        max_length=100,
        blank=True,
        help_text="Example: Technical Head, Registration Head",
    )

    profile_photo = models.ImageField(
        upload_to="profiles/core_committee/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.full_name