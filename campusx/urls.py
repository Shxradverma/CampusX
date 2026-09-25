from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("events/", include("events.urls")),
    path("registrations/", include("registrations.urls")),
    path("chatbot/", include("chatbot.urls")),
    path(
        "notifications/",
        include("notifications.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )