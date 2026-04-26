from datetime import date

from django import forms

from .models import Subject


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'input-field'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))


class AttendanceMarkForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.Select(attrs={'class': 'input-field'}),
        empty_label='Select subject',
    )
    attendance_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
    )

    def __init__(self, *args, faculty=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculty is not None:
            self.fields['subject'].queryset = Subject.objects.filter(faculty=faculty)
        else:
            self.fields['subject'].queryset = Subject.objects.all()
