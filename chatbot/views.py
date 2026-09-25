import json
from difflib import SequenceMatcher
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.models import (
    Event,
    EventAnnouncement,
    EventFAQ,
    EventTeamMember,
)

from registrations.models import (
    Attendance,
    Certificate,
    EventResult,
    Registration,
)

@login_required
def chatbot_home(request):
    return JsonResponse(
        {
            "success": True,
            "message": "CampusX AI Assistant backend is working.",
            "user": request.user.username,
            "role": request.user.role,
        }
    )


def format_event(event):
    local_start = timezone.localtime(event.start_datetime)

    return (
        f"{event.title} — "
        f"{local_start.strftime('%d %b %Y, %I:%M %p')} "
        f"at {event.venue}"
    )


def available_events_answer():
    now = timezone.now()

    events = (
        Event.objects.filter(
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
            registration_deadline__gte=now,
            start_datetime__gt=now,
        )
        .order_by("start_datetime")[:5]
    )

    if not events:
        return (
            "There are currently no published events "
            "open for registration."
        )

    event_lines = [
        f"{index}. {format_event(event)}"
        for index, event in enumerate(events, start=1)
    ]

    return (
        "Here are the upcoming events currently open "
        "for registration:\n\n"
        + "\n".join(event_lines)
    )


def student_registrations_answer(user):
    registrations = (
        Registration.objects.filter(
            student=user,
            status=Registration.Status.REGISTERED,
        )
        .select_related("event")
        .order_by("event__start_datetime")[:10]
    )

    if not registrations:
        return "You do not have any active event registrations."

    lines = []

    for index, registration in enumerate(
        registrations,
        start=1,
    ):
        event = registration.event

        lines.append(
            f"{index}. {format_event(event)}"
        )

    return (
        "Your active CampusX registrations are:\n\n"
        + "\n".join(lines)
    )


def organizer_events_answer(user):
    events = (
        Event.objects.filter(
            organizer=user,
        )
        .annotate(
            active_registrations=Count(
                "registrations",
                filter=Q(
                    registrations__status=
                    Registration.Status.REGISTERED
                ),
            )
        )
        .order_by("-start_datetime")[:10]
    )

    if not events:
        return "You have not created any events yet."

    lines = []

    for index, event in enumerate(events, start=1):
        lines.append(
            f"{index}. {event.title} — "
            f"{event.get_status_display()} / "
            f"{event.get_approval_status_display()} — "
            f"{event.active_registrations} registrations"
        )

    return (
        "Here are your CampusX events:\n\n"
        + "\n".join(lines)
    )


def assigned_events_answer(user):
    assignments = (
        EventTeamMember.objects.filter(
            member=user,
        )
        .select_related("event")
        .order_by("event__start_datetime")
    )

    if not assignments.exists():
        return "You currently have no event team assignments."

    lines = []

    for index, assignment in enumerate(
        assignments[:10],
        start=1,
    ):
        lines.append(
            f"{index}. {assignment.event.title} — "
            f"{assignment.get_team_role_display()} — "
            f"{assignment.event.venue}"
        )

    return (
        "Your CampusX event assignments are:\n\n"
        + "\n".join(lines)
    )


def attendance_answer(user):
    registrations = (
        Registration.objects.filter(
            student=user,
            status=Registration.Status.REGISTERED,
        )
        .select_related(
            "event",
            "attendance",
        )
        .order_by("-event__start_datetime")[:10]
    )

    if not registrations:
        return (
            "You do not have active registrations, "
            "so there is no attendance information to show."
        )

    lines = []

    for index, registration in enumerate(
        registrations,
        start=1,
    ):
        try:
            attendance = registration.attendance

            attendance_status = (
                attendance.get_status_display()
            )

        except Attendance.DoesNotExist:
            attendance_status = "Not marked yet"

        lines.append(
            f"{index}. {registration.event.title} — "
            f"{attendance_status}"
        )

    return (
        "Your attendance status:\n\n"
        + "\n".join(lines)
    )
def certificate_answer(user):
    registrations = (
        Registration.objects.filter(
            student=user,
            status=Registration.Status.REGISTERED,
        )
        .select_related(
            "event",
            "attendance",
        )
        .order_by("-event__end_datetime")
    )

    if not registrations.exists():
        return (
            "You do not have any active event "
            "registrations yet."
        )

    lines = []

    for registration in registrations[:10]:
        event = registration.event

        if timezone.now() < event.end_datetime:
            status = "Available after the event ends"

        else:
            try:
                attendance = registration.attendance
            except Attendance.DoesNotExist:
                attendance = None

            if (
                attendance is None
                or attendance.status != Attendance.Status.PRESENT
            ):
                status = "Not eligible - attendance not marked Present"

            else:
                certificate = Certificate.objects.filter(
                    registration=registration,
                    is_valid=True,
                ).first()

                if certificate:
                    status = (
                        "Available - open the event page "
                        "to view or print it"
                    )
                else:
                    status = (
                        "Eligible - open the event page "
                        "to generate your certificate"
                    )

        lines.append(
            f"{event.title} - {status}"
        )

    return (
        "Your CampusX certificate status:\n\n"
        + "\n".join(lines)
    )
def event_results_answer(event, user):
    if not event.results_published:
        return (
            f"{event.title}\n\n"
            "Results have not been published yet."
        )

    results = (
        EventResult.objects.filter(event=event)
        .select_related(
            "registration",
            "registration__student",
            "registration__student__student_profile",
        )
        .order_by("position")
    )

    if not results.exists():
        return (
            f"{event.title}\n\n"
            "No winner information is available."
        )

    lines = []

    for result in results:
        student = result.registration.student

        try:
            name = student.student_profile.full_name
        except Exception:
            name = student.get_full_name() or student.username

        line = (
            f"{result.get_position_display()}: {name}"
        )

        if result.prize:
            line += f" - Prize: {result.prize}"

        lines.append(line)

    # Tell a student their personal result too.
    if user.role == "STUDENT":
        personal_result = results.filter(
            registration__student=user
        ).first()

        if personal_result:
            personal_message = (
                "\n\nYour result: "
                f"{personal_result.get_position_display()}"
            )

            if personal_result.prize:
                personal_message += (
                    f" - Prize: {personal_result.prize}"
                )
        else:
            personal_message = (
                "\n\nYou are not listed among the "
                "published winners for this event."
            )
    else:
        personal_message = ""

    return (
        f"{event.title} - Published Results:\n\n"
        + "\n".join(lines)
        + personal_message
    )
def event_announcements_answer(event):
    announcements = (
        EventAnnouncement.objects.filter(
            event=event,
            is_active=True,
        )
        .order_by("-created_at")[:5]
    )

    if not announcements:
        return (
            f"{event.title}\n\n"
            "There are currently no active announcements."
        )

    lines = []

    for index, announcement in enumerate(
        announcements,
        start=1,
    ):
        created_at = timezone.localtime(
            announcement.created_at
        ).strftime("%d %b %Y, %I:%M %p")

        lines.append(
            f"{index}. {announcement.title}\n"
            f"{announcement.message}\n"
            f"Posted: {created_at}"
        )

    return (
        f"{event.title} - Latest Announcements:\n\n"
        + "\n\n".join(lines)
    )
def event_faq_answer(event):
    faqs = (
        EventFAQ.objects.filter(
            event=event,
            is_active=True,
        )
        .order_by("order", "created_at")[:10]
    )

    if not faqs:
        return (
            f"{event.title}\n\n"
            "There are currently no active FAQs "
            "for this event."
        )

    lines = []

    for index, faq in enumerate(
        faqs,
        start=1,
    ):
        lines.append(
            f"{index}. Q: {faq.question}\n"
            f"A: {faq.answer}"
        )

    return (
        f"{event.title} - Frequently Asked Questions:\n\n"
        + "\n\n".join(lines)
    )
def similarity_score(first_text, second_text):
    return SequenceMatcher(
        None,
        first_text.lower(),
        second_text.lower(),
    ).ratio()


def find_matching_event(message, user=None):
    """
    Find a relevant published + approved event from
    a natural-language question.
    """

    text = message.lower().strip()

    events = (
        Event.objects.filter(
            status=Event.Status.PUBLISHED,
            approval_status=Event.ApprovalStatus.APPROVED,
        )
        .select_related("category")
        .order_by("start_datetime")
    )

    # 1. Exact/full title match
    for event in events:
        if event.title.lower() in text:
            return event

    # 2. Partial title-word matching
    ignored_words = {
        "the",
        "event",
        "campusx",
        "2026",
        "college",
    }

    best_event = None
    best_score = 0

    for event in events:
        title_words = {
            word.lower().strip(".,!?")
            for word in event.title.split()
            if len(word) >= 3
        }

        title_words -= ignored_words

        score = sum(
            1
            for word in title_words
            if word in text
        )

        if score > best_score:
            best_score = score
            best_event = event

    if best_score > 0:
        return best_event
    # 3. Fuzzy event-title matching for spelling mistakes.
    message_words = [
        word.strip(".,!?")
        for word in text.split()
        if len(word.strip(".,!?")) >= 4
    ]

    fuzzy_event = None
    fuzzy_score = 0.0

    for event in events:
        title_words = [
            word.lower().strip(".,!?")
            for word in event.title.split()
            if len(word.strip(".,!?")) >= 4
        ]

        for message_word in message_words:
            for title_word in title_words:
                score = similarity_score(
                    message_word,
                    title_word,
                )

                if score > fuzzy_score:
                    fuzzy_score = score
                    fuzzy_event = event

    if fuzzy_event and fuzzy_score >= 0.75:
        return fuzzy_event

    # 3. For a student, phrases such as
    # "mera event" can refer to their registered event.
    if user and user.role == "STUDENT":
        registration = (
            Registration.objects.filter(
                student=user,
                status=Registration.Status.REGISTERED,
            )
            .select_related("event")
            .order_by("event__start_datetime")
            .first()
        )

        personal_phrases = [
            "mera event",
            "meri event",
            "my event",
            "registered event",
        ]

        if (
            registration
            and any(
                phrase in text
                for phrase in personal_phrases
            )
        ):
            return registration.event

    return None


def event_details_answer(event):
    start = timezone.localtime(
        event.start_datetime
    ).strftime("%d %b %Y, %I:%M %p")

    deadline = timezone.localtime(
        event.registration_deadline
    ).strftime("%d %b %Y, %I:%M %p")

    category = (
        event.category.name
        if event.category
        else "General"
    )

    registration_state = (
        "Open"
        if event.registration_open
        else "Closed"
    )

    return (
        f"{event.title}\n\n"
        f"Category: {category}\n"
        f"Venue: {event.venue}\n"
        f"Starts: {start}\n"
        f"Registration deadline: {deadline}\n"
        f"Registration: {registration_state}"
    )


def event_venue_answer(event):
    return (
        f"{event.title}\n\n"
        f"Venue: {event.venue}"
    )


def event_datetime_answer(event):
    start = timezone.localtime(
        event.start_datetime
    ).strftime("%d %b %Y, %I:%M %p")

    end = timezone.localtime(
        event.end_datetime
    ).strftime("%d %b %Y, %I:%M %p")

    return (
        f"{event.title}\n\n"
        f"Starts: {start}\n"
        f"Ends: {end}\n"
        f"Venue: {event.venue}"
    )


def event_deadline_answer(event):
    deadline = timezone.localtime(
        event.registration_deadline
    ).strftime("%d %b %Y, %I:%M %p")

    state = (
        "Open"
        if event.registration_open
        else "Closed"
    )

    return (
        f"{event.title}\n\n"
        f"Registration deadline: {deadline}\n"
        f"Registration status: {state}"
    )


def detect_intent(message):
    """
    Detect common CampusX questions in English
    and Hinglish. Database functions provide
    the actual facts.
    """

    text = message.lower().strip()
    faq_phrases = [
        "faq",
        "faqs",
        "frequently asked",
        "frequently asked questions",
        "common questions",
        "event questions",
        "questions about event",
        "event ke questions",
        "event ke faq",
        "event faq",
        "sawal",
        "questions batao",
    ]

    if any(
        phrase in text
        for phrase in faq_phrases
    ):
        return "EVENT_FAQ"
    announcement_phrases = [
        "announcement",
        "announcements",
        "latest announcement",
        "new announcement",
        "latest update",
        "event update",
        "notice",
        "notices",
        "koi announcement",
        "announcement kya hai",
        "update kya hai",
        "latest notice",
    ]

    if any(
        phrase in text
        for phrase in announcement_phrases
    ):
        return "EVENT_ANNOUNCEMENTS"
    result_phrases = [
        "result",
        "results",
        "winner",
        "winners",
        "who won",
        "kaun jeeta",
        "kon jeeta",
        "kaun jita",
        "kon jita",
        "mera result",
        "meri position",
        "my result",
        "my position",
        "first place",
        "1st place",
    ]

    if any(
        phrase in text
        for phrase in result_phrases
    ):
        return "EVENT_RESULTS"
    certificate_phrases = [
        "certificate",
        "my certificate",
        "mera certificate",
        "meri certificate",
        "certificate kaha",
        "certificate kahan",
        "certificate available",
        "certificate mila",
        "certificate download",
        "participation certificate",
    ]

    if any(
        phrase in text
        for phrase in certificate_phrases
    ):
        return "MY_CERTIFICATE"

    deadline_phrases = [
        "deadline",
        "last date",
        "registration close",
        "registration closing",
        "register kab tak",
        "registration kab tak",
        "kab tak register",
    ]

    if any(
        phrase in text
        for phrase in deadline_phrases
    ):
        return "EVENT_DEADLINE"

    registration_phrases = [
        "my registration",
        "my registrations",
        "registered events",
        "show my registered",
        "maine kis event",
        "maine kaunse event",
        "maine konsa event",
        "maine kon sa event",
        "mera registration",
        "meri registration",
        "mere registered event",
        "kis event me register",
        "kis event mein register",
    ]

    if any(
        phrase in text
        for phrase in registration_phrases
    ):
        return "MY_REGISTRATIONS"

    attendance_phrases = [
        "my attendance",
        "attendance status",
        "meri attendance",
        "mera attendance",
        "attendance hui",
        "attendance lagi",
        "attendance mark",
        "present hu",
        "present hoon",
    ]

    if any(
        phrase in text
        for phrase in attendance_phrases
    ):
        return "MY_ATTENDANCE"

    available_phrases = [
        "available event",
        "available events",
        "upcoming event",
        "upcoming events",
        "open events",
        "what events",
        "new events",
        "events available",
        "kaunse event available",
        "konsa event available",
        "aane wale event",
        "upcoming hackathon",
    ]

    if any(
        phrase in text
        for phrase in available_phrases
    ):
        return "AVAILABLE_EVENTS"

    assignment_phrases = [
        "assigned event",
        "assigned events",
        "my assignment",
        "my assignments",
        "mere assigned event",
        "meri duty",
        "my duty",
        "event duty",
    ]

    if any(
        phrase in text
        for phrase in assignment_phrases
    ):
        return "ASSIGNED_EVENTS"

    qr_phrases = [
        "qr",
        "qr code",
        "qr attendance",
        "attendance kaise",
        "attendance kese",
        "attendance work",
        "qr kaise",
        "qr kese",
        "check in",
        "check-in",
    ]

    if any(
        phrase in text
        for phrase in qr_phrases
    ):
        return "QR_HELP"

    approval_phrases = [
        "approval",
        "approve event",
        "event approve",
        "approval status",
        "event approval",
        "publish event",
        "event publish",
    ]

    if any(
        phrase in text
        for phrase in approval_phrases
    ):
        return "EVENT_APPROVAL"

    venue_phrases = [
        "venue",
        "location",
        "where",
        "kaha",
        "kahan",
        "kahaan",
        "kidhar",
    ]

    if any(
        phrase in text
        for phrase in venue_phrases
    ):
        return "EVENT_VENUE"

    datetime_phrases = [
        "when",
        "date",
        "time",
        "kab hai",
        "kab hoga",
        "kab hogi",
        "kitne baje",
        "start time",
        "starting time",
    ]

    if any(
        phrase in text
        for phrase in datetime_phrases
    ):
        return "EVENT_DATETIME"

    organizer_phrases = [
        "my events",
        "show my events",
        "mere events",
        "maine event create",
        "created events",
    ]

    if any(
        phrase in text
        for phrase in organizer_phrases
    ):
        return "MY_EVENTS"
    # Fuzzy intent detection for common spelling mistakes.
    words = [
        word.strip(".,!?")
        for word in text.split()
        if len(word.strip(".,!?")) >= 4
    ]

    fuzzy_keywords = {
        "EVENT_RESULTS": [
            "result",
            "results",
            "winner",
        ],
        "MY_CERTIFICATE": [
            "certificate",
        ],
        "EVENT_ANNOUNCEMENTS": [
            "announcement",
            "announcements",
            "notice",
        ],
        "MY_ATTENDANCE": [
            "attendance",
        ],
        "EVENT_FAQ": [
            "faq",
            "question",
        ],
    }

    best_intent = None
    best_similarity = 0.0

    for intent_name, keywords in fuzzy_keywords.items():
        for word in words:
            for keyword in keywords:
                score = similarity_score(
                    word,
                    keyword,
                )

                if score > best_similarity:
                    best_similarity = score
                    best_intent = intent_name

    if best_intent and best_similarity >= 0.75:
        return best_intent

    return "UNKNOWN"

    return "UNKNOWN"


@login_required
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(
            request.body.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request.",
            },
            status=400,
        )

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return JsonResponse(
            {
                "success": False,
                "message": "Please enter a question.",
            },
            status=400,
        )

    if len(message) > 500:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Please keep your question "
                    "under 500 characters."
                ),
            },
            status=400,
        )

    normalized = message.lower()

    user = request.user
    role = user.role

    intent = detect_intent(normalized)

    matched_event = find_matching_event(
        normalized,
        user,
    )

    if (
        intent == "EVENT_FAQ"
        and matched_event
    ):
        answer = event_faq_answer(
            matched_event
        )

    elif (
        intent == "EVENT_ANNOUNCEMENTS"
        and matched_event
    ):
        answer = event_announcements_answer(
            matched_event
        )

    elif (
        intent == "EVENT_RESULTS"
        and matched_event
    ):
        answer = event_results_answer(
            matched_event,
            user,
        )

    elif (
        intent == "MY_CERTIFICATE"
        and role == "STUDENT"
    ):
        answer = certificate_answer(user)

    elif (
        intent == "MY_REGISTRATIONS"
        and role == "STUDENT"
    ):
        answer = student_registrations_answer(
            user
        )

    elif (
        intent == "MY_ATTENDANCE"
        and role == "STUDENT"
    ):
        answer = attendance_answer(user)

    elif intent == "AVAILABLE_EVENTS":
        answer = available_events_answer()

    elif (
        intent == "MY_EVENTS"
        and role == "ORGANIZER"
    ):
        answer = organizer_events_answer(user)

    elif (
        intent == "ASSIGNED_EVENTS"
        and role in {
            "TEACHER",
            "CORE_COMMITTEE",
        }
    ):
        answer = assigned_events_answer(user) 
    elif intent == "QR_HELP":
        answer = (
            "For QR attendance, a registered student "
            "opens the QR for their event. Authorized "
            "CampusX staff scan that QR during the "
            "event attendance window. The system "
            "verifies the registration and records "
            "attendance."
        )

    elif (
        intent == "EVENT_APPROVAL"
        and role == "ORGANIZER"
    ):
        answer = (
            "CampusX event approval works in stages: "
            "create the event as a draft, submit it "
            "for administrator approval, wait for "
            "review, and after approval publish the "
            "event from the Event Management page."
        )

    elif (
        intent == "EVENT_VENUE"
        and matched_event
    ):
        answer = event_venue_answer(
            matched_event
        )

    elif (
        intent == "EVENT_DATETIME"
        and matched_event
    ):
        answer = event_datetime_answer(
            matched_event
        )

    elif (
        intent == "EVENT_DEADLINE"
        and matched_event
    ):
        answer = event_deadline_answer(
            matched_event
        )

    elif matched_event:
        answer = event_details_answer(
            matched_event
        )

    elif (
        role == "TEACHER"
        and "teacher" in normalized
    ):
        answer = (
            "Teachers can view events assigned to "
            "them, review participant information "
            "for those events, and perform duties "
            "according to their event-team assignment. "
            "Event editing remains controlled by "
            "the organizer."
        )

    elif (
        role == "CORE_COMMITTEE"
        and "scan attendance" in normalized
    ):
        answer = (
            "QR scanning is available only when you "
            "are assigned to the event as Attendance "
            "Team or Event Coordinator."
        )

    else:
        answer = (
            "I can help with CampusX events, "
            "registrations, attendance, QR check-in, "
            "event dates, venues, registration "
            "deadlines, assignments and approvals.\n\n"
            "For example, ask:\n"
            "• Hackathon kab hai?\n"
            "• Hackathon kaha hai?\n"
            "• Registration kab tak hai?\n"
            "• Meri attendance hui hai?\n"
            "• Maine kis event me register kiya hai?"
        )

    return JsonResponse(
        {
            "success": True,
            "reply": answer,
            "intent": intent,
        }
    )
