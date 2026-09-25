from .models import EventTeamMember


def is_event_organizer(user, event):
    """
    Returns True if the user is the organizer
    who created/owns this event.
    """
    return (
        user.is_authenticated
        and event.organizer_id == user.id
    )


def is_assigned_teacher(user, event):
    """
    Returns True if the user is a Teacher
    assigned to this event.
    """
    if not user.is_authenticated:
        return False

    if user.role != "TEACHER":
        return False

    return EventTeamMember.objects.filter(
        event=event,
        member=user,
    ).exists()


def is_assigned_committee_member(user, event):
    """
    Returns True if the user is a Core Committee
    member assigned to this event.
    """
    if not user.is_authenticated:
        return False

    if user.role != "CORE_COMMITTEE":
        return False

    return EventTeamMember.objects.filter(
        event=event,
        member=user,
    ).exists()


def can_view_event_management(user, event):
    """
    Organizer, assigned Teacher and assigned
    Core Committee members can view event
    management information.
    """
    return (
        is_event_organizer(user, event)
        or is_assigned_teacher(user, event)
        or is_assigned_committee_member(user, event)
    )


def can_view_participants(user, event):
    """
    Organizer, assigned Teacher and assigned
    Core Committee members can view participants.
    """
    return can_view_event_management(
        user,
        event,
    )


def can_scan_attendance(user, event):
    """
    Organizer can always scan attendance.

    Core Committee members can scan only when
    assigned to Attendance Team or
    Event Coordinator role.
    """
    if is_event_organizer(user, event):
        return True

    if not user.is_authenticated:
        return False

    if user.role != "CORE_COMMITTEE":
        return False

    allowed_roles = [
        EventTeamMember.TeamRole.ATTENDANCE,
        EventTeamMember.TeamRole.EVENT_COORDINATOR,
    ]

    return EventTeamMember.objects.filter(
        event=event,
        member=user,
        team_role__in=allowed_roles,
    ).exists()


def can_edit_event(user, event):
    """
    Only the event owner/Organizer can edit.
    """
    return is_event_organizer(
        user,
        event,
    )


def can_delete_event(user, event):
    """
    Only the event owner/Organizer can delete.
    """
    return is_event_organizer(
        user,
        event,
    )