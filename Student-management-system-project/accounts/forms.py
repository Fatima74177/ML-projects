from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm


from .models import Profile


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password',
        }),
    )

    def clean_username(self):
        email = self.cleaned_data['username']
        user = User.objects.filter(email__iexact=email).first()
        return user.username if user else email


class RegistrationForm(UserCreationForm):
    # Public sign-up may only create teacher/student accounts. Administrator
    # accounts must be created via `python manage.py createsuperuser` or
    # promoted from the Django admin site by an existing administrator -
    # letting anyone pick "administrator" here would be a privilege
    # escalation bug.
    role = forms.ChoiceField(
        choices=[c for c in Profile.ROLE_CHOICES if c[0] != 'administrator'],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Choose a username',
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email address',
            'password1': 'Create password',
            'password2': 'Confirm password',
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            field.widget.attrs.setdefault('placeholder', placeholders.get(name, field.label))

class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')