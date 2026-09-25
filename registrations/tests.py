from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import StudentProfile
from events.models import Event

from .models import (
    Attendance,
    Certificate,
    EventFeedback,
    EventResult,
    FavoriteEvent,
    Registration,
)
from .utils import generate_attendance_token


User = get_user_model()


class RegistrationModelSecurityTests(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="test_organizer",
            email="organizer@test.com",
            password="TestPass123!",
            role="ORGANIZER",
        )

        self.student = User.objects.create_user(
            username="test_student",
            email="student@test.com",
            password="TestPass123!",
            role="STUDENT",
        )

        self.student_two = User.objects.create_user(
            username="test_student_two",
            email="student2@test.com",
            password="TestPass123!",
            role="STUDENT",
        )

        now = timezone.now()

        self.event = Event.objects.create(
            title="CampusX Security Test Event",
            description="Automated security test event.",
            organizer=self.organizer,
            venue="Test Hall",
            start_datetime=now + timedelta(days=2),
            end_datetime=now + timedelta(days=2, hours=3),
            registration_deadline=now + timedelta(days=1),
            capacity=100,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        self.registration = Registration.objects.create(
            event=self.event,
            student=self.student,
            status=Registration.Status.REGISTERED,
        )

    def test_duplicate_registration_is_blocked(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Registration.objects.create(
                    event=self.event,
                    student=self.student,
                    status=Registration.Status.REGISTERED,
                )

        self.assertEqual(
            Registration.objects.filter(
                event=self.event,
                student=self.student,
            ).count(),
            1,
        )

    def test_only_one_attendance_per_registration(self):
        Attendance.objects.create(
            registration=self.registration,
            status=Attendance.Status.PRESENT,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(
                    registration=self.registration,
                    status=Attendance.Status.ABSENT,
                )

        self.assertEqual(
            Attendance.objects.filter(
                registration=self.registration,
            ).count(),
            1,
        )

    def test_duplicate_favorite_is_blocked(self):
        FavoriteEvent.objects.create(
            student=self.student,
            event=self.event,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FavoriteEvent.objects.create(
                    student=self.student,
                    event=self.event,
                )

        self.assertEqual(
            FavoriteEvent.objects.filter(
                student=self.student,
                event=self.event,
            ).count(),
            1,
        )

    def test_duplicate_feedback_is_blocked(self):
        EventFeedback.objects.create(
            student=self.student,
            event=self.event,
            rating=5,
            comment="Excellent event.",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventFeedback.objects.create(
                    student=self.student,
                    event=self.event,
                    rating=4,
                    comment="Duplicate feedback.",
                )

        self.assertEqual(
            EventFeedback.objects.filter(
                student=self.student,
                event=self.event,
            ).count(),
            1,
        )

    def test_result_rejects_registration_from_another_event(self):
        now = timezone.now()

        second_event = Event.objects.create(
            title="Second Test Event",
            description="Another event.",
            organizer=self.organizer,
            venue="Second Hall",
            start_datetime=now + timedelta(days=4),
            end_datetime=now + timedelta(days=4, hours=2),
            registration_deadline=now + timedelta(days=3),
            capacity=50,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        result = EventResult(
            event=second_event,
            registration=self.registration,
            position=EventResult.Position.FIRST,
        )

        with self.assertRaises(ValidationError):
            result.full_clean()

    def test_cancelled_registration_cannot_be_winner(self):
        self.registration.status = Registration.Status.CANCELLED
        self.registration.save()

        result = EventResult(
            event=self.event,
            registration=self.registration,
            position=EventResult.Position.FIRST,
        )

        with self.assertRaises(ValidationError):
            result.full_clean()

    def test_same_winning_position_cannot_be_used_twice(self):
        EventResult.objects.create(
            event=self.event,
            registration=self.registration,
            position=EventResult.Position.FIRST,
        )

        second_registration = Registration.objects.create(
            event=self.event,
            student=self.student_two,
            status=Registration.Status.REGISTERED,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventResult.objects.create(
                    event=self.event,
                    registration=second_registration,
                    position=EventResult.Position.FIRST,
                )

    def test_participant_cannot_receive_two_positions(self):
        EventResult.objects.create(
            event=self.event,
            registration=self.registration,
            position=EventResult.Position.FIRST,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventResult.objects.create(
                    event=self.event,
                    registration=self.registration,
                    position=EventResult.Position.SECOND,
                )

    def test_only_one_certificate_per_registration(self):
        Certificate.objects.create(
            registration=self.registration,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    registration=self.registration,
                )

        self.assertEqual(
            Certificate.objects.filter(
                registration=self.registration,
            ).count(),
            1,
        )


class RegistrationViewSecurityTests(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="view_organizer",
            email="view_organizer@test.com",
            password="TestPass123!",
            role="ORGANIZER",
        )

        self.student = User.objects.create_user(
            username="view_student",
            email="view_student@test.com",
            password="TestPass123!",
            role="STUDENT",
        )

        self.other_student = User.objects.create_user(
            username="other_student",
            email="other_student@test.com",
            password="TestPass123!",
            role="STUDENT",
        )

        now = timezone.now()

        self.event = Event.objects.create(
            title="QR Security Test Event",
            description="QR permission testing.",
            organizer=self.organizer,
            venue="Security Test Hall",
            start_datetime=now + timedelta(hours=1),
            end_datetime=now + timedelta(hours=4),
            registration_deadline=now - timedelta(hours=1),
            capacity=100,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        self.registration = Registration.objects.create(
            event=self.event,
            student=self.student,
            status=Registration.Status.REGISTERED,
        )

    def test_anonymous_user_cannot_view_student_qr(self):
        response = self.client.get(
            f"/registrations/event/{self.event.id}/qr/"
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_student_can_view_own_qr(self):
        self.client.force_login(self.student)

        response = self.client.get(
            f"/registrations/event/{self.event.id}/qr/"
        )

        self.assertEqual(response.status_code, 200)

    def test_other_student_cannot_view_another_students_qr(self):
        self.client.force_login(self.other_student)

        response = self.client.get(
            f"/registrations/event/{self.event.id}/qr/"
        )

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_access_attendance_scanner(self):
        self.client.force_login(self.student)

        response = self.client.get(
            (
                f"/registrations/event/{self.event.id}/"
                "attendance/verify/"
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_event_organizer_can_access_attendance_scanner(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            (
                f"/registrations/event/{self.event.id}/"
                "attendance/verify/"
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_tampered_qr_token_is_rejected(self):
        self.client.force_login(self.organizer)

        token = generate_attendance_token(
            self.registration
        )

        tampered_token = token + "tampered"

        response = self.client.post(
            (
                f"/registrations/event/{self.event.id}/"
                "attendance/verify/"
            ),
            {
                "token": tampered_token,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Attendance.objects.filter(
                registration=self.registration,
            ).exists()
        )

        self.assertContains(
            response,
            "Invalid or expired attendance QR code.",
        )

    def test_qr_from_different_event_is_rejected(self):
        now = timezone.now()

        second_event = Event.objects.create(
            title="Second QR Security Event",
            description="Wrong event QR test.",
            organizer=self.organizer,
            venue="Second Test Hall",
            start_datetime=now + timedelta(hours=1),
            end_datetime=now + timedelta(hours=4),
            registration_deadline=now - timedelta(hours=1),
            capacity=100,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        token = generate_attendance_token(
            self.registration
        )

        self.client.force_login(self.organizer)

        response = self.client.post(
            (
                f"/registrations/event/{second_event.id}/"
                "attendance/verify/"
            ),
            {
                "token": token,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Attendance.objects.filter(
                registration=self.registration,
            ).exists()
        )

        self.assertContains(
            response,
            (
                "This QR code belongs to a different "
                "event and cannot be used here."
            ),
        )


class CertificateViewSecurityTests(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="certificate_organizer",
            email="certificate_organizer@test.com",
            password="TestPass123!",
            role="ORGANIZER",
        )

        self.student = User.objects.create_user(
            username="certificate_student",
            email="certificate_student@test.com",
            password="TestPass123!",
            role="STUDENT",
        )

        StudentProfile.objects.create(
            user=self.student,
            full_name="Certificate Test Student",
            roll_number="CERT001",
            phone_number="9999999999",
            course="BCA",
            semester="1",
        )

        now = timezone.now()

        self.future_event = Event.objects.create(
            title="Future Certificate Event",
            description="Certificate security test.",
            organizer=self.organizer,
            venue="Test Hall",
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=2),
            registration_deadline=now + timedelta(hours=12),
            capacity=100,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        self.future_registration = Registration.objects.create(
            event=self.future_event,
            student=self.student,
            status=Registration.Status.REGISTERED,
        )

        self.ended_event = Event.objects.create(
            title="Completed Certificate Event",
            description="Certificate eligibility test.",
            organizer=self.organizer,
            venue="Test Hall",
            start_datetime=now - timedelta(days=2),
            end_datetime=now - timedelta(days=1),
            registration_deadline=now - timedelta(days=3),
            capacity=100,
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )

        self.ended_registration = Registration.objects.create(
            event=self.ended_event,
            student=self.student,
            status=Registration.Status.REGISTERED,
        )

    def test_anonymous_user_cannot_access_certificate(self):
        response = self.client.get(
            (
                f"/registrations/event/"
                f"{self.ended_event.id}/certificate/"
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_certificate_not_available_before_event_ends(self):
        Attendance.objects.create(
            registration=self.future_registration,
            status=Attendance.Status.PRESENT,
            checked_in_at=timezone.now(),
            verified_by=self.organizer,
        )

        self.client.force_login(self.student)

        response = self.client.get(
            (
                f"/registrations/event/"
                f"{self.future_event.id}/certificate/"
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Certificate.objects.filter(
                registration=self.future_registration,
            ).exists()
        )

        self.assertContains(
            response,
            (
                "Certificate will be available "
                "after the event is completed."
            ),
        )

    def test_absent_student_cannot_get_certificate(self):
        Attendance.objects.create(
            registration=self.ended_registration,
            status=Attendance.Status.ABSENT,
            verified_by=self.organizer,
        )

        self.client.force_login(self.student)

        response = self.client.get(
            (
                f"/registrations/event/"
                f"{self.ended_event.id}/certificate/"
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Certificate.objects.filter(
                registration=self.ended_registration,
            ).exists()
        )

        self.assertContains(
            response,
            (
                "Certificate is available only for "
                "students who attended the event."
            ),
        )

    def test_present_student_can_receive_certificate(self):
        Attendance.objects.create(
            registration=self.ended_registration,
            status=Attendance.Status.PRESENT,
            checked_in_at=timezone.now(),
            verified_by=self.organizer,
        )

        self.client.force_login(self.student)

        response = self.client.get(
            (
                f"/registrations/event/"
                f"{self.ended_event.id}/certificate/"
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Certificate.objects.filter(
                registration=self.ended_registration,
            ).exists()
        )
    def test_valid_certificate_can_be_verified_publicly(self):
        Attendance.objects.create(
            registration=self.ended_registration,
            status=Attendance.Status.PRESENT,
            checked_in_at=timezone.now(),
            verified_by=self.organizer,
        )

        certificate = Certificate.objects.create(
            registration=self.ended_registration,
        )

        response = self.client.get(
            "/registrations/certificate/verify/",
            {
                "certificate_id": str(
                    certificate.certificate_id
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["certificate"],
            certificate,
        )

        self.assertFalse(
            response.context["invalid_id"]
        )

    def test_invalid_certificate_id_is_rejected(self):
        response = self.client.get(
            "/registrations/certificate/verify/",
            {
                "certificate_id": "invalid-certificate-id",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertIsNone(
            response.context["certificate"]
        )

        self.assertTrue(
            response.context["invalid_id"]
        )