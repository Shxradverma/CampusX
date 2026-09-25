from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import (
    StudentProfileUpdateForm,
    StudentRegistrationForm,
)
from .models import User
def home_view(request):
    return render(
        request,
        "home.html",
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Account created successfully. Welcome to CampusX!",
            )

            return redirect("student_dashboard")

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_redirect")

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.username}!",
            )

            return redirect("dashboard_redirect")

    else:
        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


@login_required
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("login")


@login_required
def dashboard_redirect(request):

    if (
        request.user.is_superuser
        or request.user.role == User.Role.ADMIN
    ):
        return redirect("/admin/")

    if request.user.role == User.Role.ORGANIZER:
        return redirect("organizer_dashboard")

    if request.user.role == User.Role.TEACHER:
        return redirect("teacher_dashboard")

    if request.user.role == User.Role.CORE_COMMITTEE:
        return redirect("core_committee_dashboard")

    if request.user.role == User.Role.STUDENT:
        return redirect("student_dashboard")

    raise PermissionDenied


@login_required
def student_profile_view(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    profile = request.user.student_profile

    if request.method == "POST":
        form = StudentProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Profile updated successfully.",
            )

            return redirect("student_profile")

    else:
        form = StudentProfileUpdateForm(
            instance=profile,
            user=request.user,
        )

    return render(
        request,
        "accounts/student_profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )