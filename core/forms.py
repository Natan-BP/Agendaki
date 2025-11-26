from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import User, Meeting, TimeSlot


class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.RadioSelect,
        label='Tipo de usuário'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description']
        labels = {
            'title': 'Título da reunião',
            'description': 'Descrição (opcional)',
        }
        

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start', 'end']
        labels = {
            'start': 'Início',
            'end': 'Fim',
        }
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
