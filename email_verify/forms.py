from allauth.account.forms import SignupForm
from django import forms

from user.models import Profile


class AcUkSignupForm(SignupForm):
    address = forms.CharField(
        label="Delivery Address",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 100 University Avenue, Glasgow, G12 8QQ',
        }),
    )

    role = forms.ChoiceField(
        choices=Profile.Role.choices,
        label="I want to register as a:",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()

        self.fields['username'].widget.attrs.setdefault('placeholder', 'Username')
        self.fields['email'].widget.attrs.setdefault('placeholder', 'Email (.ac.uk only)')
        self.fields['password1'].widget.attrs.setdefault('placeholder', 'Password')
        self.fields['password2'].widget.attrs.setdefault('placeholder', 'Confirm Password')
        self.fields['email'].help_text = 'Must be an academic email ending with .ac.uk'

    def save(self, request):
        user = super().save(request)

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = self.cleaned_data['role']
        profile.address = self.cleaned_data['address']
        profile.save()

        return user