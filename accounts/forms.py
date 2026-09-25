from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, StudentProfile


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=150)
    roll_number = forms.CharField(max_length=50)
    phone_number = forms.CharField(max_length=15, required=False)
    course = forms.CharField(max_length=100)
    semester = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "full_name",
            "roll_number",
            "phone_number",
            "course",
            "semester",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                "class": "form-control"
            })

        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm Password"

        self.fields["password1"].widget.attrs.update({
            "placeholder": "Enter password"
        })

        self.fields["password2"].widget.attrs.update({
            "placeholder": "Enter password again"
        })

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_roll_number(self):
        roll_number = self.cleaned_data["roll_number"].strip()

        if StudentProfile.objects.filter(
            roll_number__iexact=roll_number
        ).exists():
            raise forms.ValidationError(
                "This roll number is already registered."
            )

        return roll_number

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]
        user.role = User.Role.STUDENT

        if commit:
            user.save()

            StudentProfile.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                roll_number=self.cleaned_data["roll_number"],
                phone_number=self.cleaned_data["phone_number"],
                course=self.cleaned_data["course"],
                semester=self.cleaned_data["semester"],
            )

        return user
class StudentProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = StudentProfile

        fields = (
            "full_name",
            "phone_number",
            "course",
            "semester",
            "profile_photo",
            "interests",
        )

        widgets = {
            "interests": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Example: Python, AI, Web Development",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["email"].initial = self.user.email

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        users = User.objects.filter(email__iexact=email)

        if self.user:
            users = users.exclude(pk=self.user.pk)

        if users.exists():
            raise forms.ValidationError(
                "This email address is already being used."
            )

        return email

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.email = self.cleaned_data["email"]

            if commit:
                self.user.save()

        if commit:
            profile.save()

        return profile