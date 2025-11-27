from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Meeting, TimeSlot

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar']

class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.RadioSelect,
        label='Tipo de usuário'
    )

    class Meta:
        model = User
        # REMOVIDOS 'password1' e 'password2' DAQUI
        # O UserCreationForm já cuida deles automaticamente.
        fields = ('username', 'email', 'role') 

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

class GenerateSlotsForm(forms.Form):
    date = forms.DateField(
        label="Dia",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        label="Hora Inicial",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        label="Hora Final",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    interval = forms.IntegerField(
        label="Duração (minutos)",
        initial=30,
        min_value=15,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )