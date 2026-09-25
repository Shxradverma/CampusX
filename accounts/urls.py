from django.urls import path

from . import views


urlpatterns = [

    # Public landing page
    path(
        "",
        views.home_view,
        name="home",
    ),

    # Authentication
    path(
        "register/",
        views.register_view,
        name="register",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    # Role-based dashboard redirect
    path(
        "dashboard/",
        views.dashboard_redirect,
        name="dashboard_redirect",
    ),

    # Student profile
    path(
        "profile/",
        views.student_profile_view,
        name="student_profile",
    ),
]