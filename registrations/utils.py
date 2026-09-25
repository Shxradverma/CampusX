from django.core import signing


QR_SALT = "campusx-attendance-qr"


def generate_attendance_token(registration):
    data = {
        "registration_id": registration.id,
        "event_id": registration.event_id,
        "student_id": registration.student_id,
    }

    return signing.dumps(
        data,
        salt=QR_SALT,
        compress=True,
    )


def verify_attendance_token(token, max_age=86400):
    try:
        data = signing.loads(
            token,
            salt=QR_SALT,
            max_age=max_age,
        )

        return data

    except (
        signing.BadSignature,
        signing.SignatureExpired,
    ):
        return None