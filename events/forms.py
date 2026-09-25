from django import forms

from accounts.models import User

from .models import (
    Event,
    EventAnnouncement,
    EventFAQ,
    EventTeamMember,
)


class EventForm(forms.ModelForm):

    class Meta:
        model = Event

        fields = (
    "title",
    "description",
    "category",
    "venue",
    "start_datetime",
    "end_datetime",
    "registration_deadline",
    "capacity",
    "banner",
)

        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Enter complete event description",
                }
            ),

            "start_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),

            "end_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),

            "registration_deadline": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),

            "capacity": forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "Maximum participants",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "form-control",
                }
            )

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get(
            "start_datetime"
        )

        end = cleaned_data.get(
            "end_datetime"
        )

        deadline = cleaned_data.get(
            "registration_deadline"
        )

        if start and end and end <= start:
            self.add_error(
                "end_datetime",
                "Event end time must be after start time.",
            )

        if (
            deadline
            and start
            and deadline >= start
        ):
            self.add_error(
                "registration_deadline",
                (
                    "Registration deadline must be "
                    "before event start time."
                ),
            )

        return cleaned_data


class EventTeamMemberForm(forms.ModelForm):

    class Meta:
        model = EventTeamMember

        fields = (
            "member",
            "team_role",
            "responsibility",
        )

        widgets = {
            "responsibility": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Enter the member's specific "
                        "responsibility for this event..."
                    ),
                }
            ),
        }

    def __init__(
        self,
        *args,
        event=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.event = event

        self.fields["member"].queryset = (
            User.objects
            .filter(
                role__in=[
                    User.Role.TEACHER,
                    User.Role.CORE_COMMITTEE,
                ],
                is_active=True,
            )
            .order_by(
                "role",
                "username",
            )
        )

        self.fields["member"].empty_label = (
            "Select Teacher or Core Committee Member"
        )

        self.fields["team_role"].empty_label = (
            "Select Team Role"
        )

        self.fields["member"].widget.attrs.update(
            {
                "class": "form-select",
            }
        )

        self.fields["team_role"].widget.attrs.update(
            {
                "class": "form-select",
            }
        )

        self.fields[
            "responsibility"
        ].widget.attrs.update(
            {
                "class": "form-control",
            }
        )

    def clean(self):
        cleaned_data = super().clean()

        member = cleaned_data.get(
            "member"
        )

        team_role = cleaned_data.get(
            "team_role"
        )

        if not member or not team_role:
            return cleaned_data

        if member.role not in [
            User.Role.TEACHER,
            User.Role.CORE_COMMITTEE,
        ]:
            self.add_error(
                "member",
                (
                    "Only Teachers and Core Committee "
                    "members can be assigned."
                ),
            )

        if (
            team_role
            == EventTeamMember.TeamRole.FACULTY_COORDINATOR
            and member.role != User.Role.TEACHER
        ):
            self.add_error(
                "team_role",
                (
                    "Faculty Coordinator can only "
                    "be assigned to a Teacher."
                ),
            )

        if (
            self.event
            and EventTeamMember.objects.filter(
                event=self.event,
                member=member,
                team_role=team_role,
            ).exists()
        ):
            self.add_error(
                "member",
                (
                    "This member already has this "
                    "role for the event."
                ),
            )

        return cleaned_data
class EventAnnouncementForm(forms.ModelForm):

    class Meta:
        model = EventAnnouncement

        fields = (
            "title",
            "message",
        )

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Announcement title",
                }
            ),

            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Write the announcement message..."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["title"].label = "Announcement Title"
        self.fields["message"].label = "Message"

class EventFAQForm(forms.ModelForm):

    class Meta:
        model = EventFAQ

        fields = (
            "question",
            "answer",
            "order",
        )

        widgets = {
            "question": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter a common question",
                }
            ),

            "answer": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter the answer",
                }
            ),

            "order": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["question"].label = "Question"
        self.fields["answer"].label = "Answer"
        self.fields["order"].label = "Display Order"