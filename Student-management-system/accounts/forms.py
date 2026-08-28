from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import Profile


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email address',
        initial='admin@example.com',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'admin@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Password',
        initial='admin12345',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password',
        }, render_value=True),
    )

    def clean_username(self):
        email = self.cleaned_data['username']
        user = User.objects.filter(email__iexact=email).first()
        return user.username if user else email


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
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
