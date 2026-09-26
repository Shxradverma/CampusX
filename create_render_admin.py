import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "campusx.settings",
)

import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("RENDER_ADMIN_USERNAME")
email = os.getenv("RENDER_ADMIN_EMAIL")
password = os.getenv("RENDER_ADMIN_PASSWORD")

if not all([username, email, password]):
    print("Admin environment variables are missing.")
else:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": "ADMIN",
        },
    )

    user.email = email
    user.role = "ADMIN"
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()

    if created:
        print("Render admin created successfully.")
    else:
        print("Render admin updated successfully.")