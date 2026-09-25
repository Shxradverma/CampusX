from django.urls import path

from . import views


urlpatterns = [
    path(
        "create/",
        views.create_event,
        name="create_event",
    ),

    # Student event discovery
    path(
        "explore/",
        views.student_event_list,
        name="student_event_list",
    ),

    path(
        "explore/<int:event_id>/",
        views.student_event_detail,
        name="student_event_detail",
    ),

    # Event management
    path(
        "<int:event_id>/participants/",
        views.event_participants,
        name="event_participants",
    ),
path(
    "<int:event_id>/participants/export/csv/",
    views.export_event_participants_csv,
    name="export_event_participants_csv",
),
    path(
        "<int:event_id>/results/",
        views.manage_event_results,
        name="manage_event_results",
    ),
    path(
        "<int:event_id>/results/<int:result_id>/remove/",
        views.remove_event_result,
        name="remove_event_result",
    ),
    path(
        "<int:event_id>/results/publish/",
        views.publish_event_results,
        name="publish_event_results",
    ),

    path(
        "<int:event_id>/feedback/",
        views.event_feedback_dashboard,
        name="event_feedback_dashboard",
    ),

    path(
        "<int:event_id>/team/",
        views.manage_event_team,
        name="manage_event_team",
    ),

    path(
        "<int:event_id>/team/<int:assignment_id>/remove/",
        views.remove_event_team_member,
        name="remove_event_team_member",
    ),

    # Approval workflow
    path(
        "<int:event_id>/submit-for-approval/",
        views.submit_event_for_approval,
        name="submit_event_for_approval",
    ),

    path(
        "<int:event_id>/publish/",
        views.publish_event,
        name="publish_event",
    ),

    # Announcements and FAQs
    path(
        "<int:event_id>/announcements/create/",
        views.create_event_announcement,
        name="create_event_announcement",
    ),

    path(
        "<int:event_id>/faqs/create/",
        views.create_event_faq,
        name="create_event_faq",
    ),

    # Event CRUD
    path(
        "<int:event_id>/edit/",
        views.edit_event,
        name="edit_event",
    ),

    path(
        "<int:event_id>/delete/",
        views.delete_event,
        name="delete_event",
    ),

    # Keep this near the bottom so specific
    # event routes above are matched first.
    path(
        "<int:event_id>/",
        views.event_detail,
        name="event_detail",
    ),
]