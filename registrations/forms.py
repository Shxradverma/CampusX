from django import forms

from .models import EventFeedback, EventResult, Registration


class EventFeedbackForm(forms.ModelForm):

    class Meta:
        model = EventFeedback

        fields = (
            "rating",
            "comment",
        )

        widgets = {
            "rating": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Share your experience about this event..."
                    ),
                    "maxlength": 1000,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["rating"].label = "Your Rating"
        self.fields["comment"].label = "Your Feedback"

        self.fields["comment"].required = False
class EventResultForm(forms.ModelForm):

    class Meta:
        model = EventResult

        fields = (
            "registration",
            "position",
            "prize",
            "remarks",
        )

        widgets = {
            "registration": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "position": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "prize": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Trophy + Certificate + ₹5,000"
                    ),
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "maxlength": 1000,
                    "placeholder": (
                        "Optional remarks about the winner..."
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
        super().__init__(*args, **kwargs)

        self.event = event

        self.fields["registration"].label = "Participant"
        self.fields["position"].label = "Winning Position"
        self.fields["prize"].label = "Prize / Award"
        self.fields["remarks"].label = "Remarks"

        self.fields["prize"].required = False
        self.fields["remarks"].required = False

        if event is not None:
            self.fields["registration"].queryset = (
                Registration.objects
                .filter(
                    event=event,
                    status=Registration.Status.REGISTERED,
                )
                .select_related(
                    "student",
                    "student__student_profile",
                )
                .order_by(
                    "student__username",
                )
            )
        else:
            self.fields["registration"].queryset = (
                Registration.objects.none()
            )

    def clean_registration(self):
        registration = self.cleaned_data.get(
            "registration"
        )

        if registration is None:
            return registration

        if self.event is None:
            raise forms.ValidationError(
                "Event information is missing."
            )

        if registration.event_id != self.event.id:
            raise forms.ValidationError(
                "Selected participant does not belong to this event."
            )

        if (
            registration.status
            != Registration.Status.REGISTERED
        ):
            raise forms.ValidationError(
                "Only active registered participants can be selected."
            )

        return registration