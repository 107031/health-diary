from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import DailyEntry, Habit, Workout


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта")

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже зарегистрирован.")
        return email


class DayForm(forms.Form):
    date = forms.DateField(label='Дата', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))

    def clean_date(self):
        day = self.cleaned_data['date']
        if day > timezone.localdate():
            raise forms.ValidationError('Выберите сегодня или дату в прошлом.')
        return day


class EntryForm(DayForm, forms.ModelForm):
    class Meta:
        model = DailyEntry
        fields = ['date', 'sleep_hours', 'weight_kg', 'calories', 'water_ml', 'mood', 'note']


class ActivityForm(forms.Form):
    activity = forms.CharField(max_length=50, required=False)
    duration_min = forms.IntegerField(min_value=1, max_value=1440, required=False)
    intensity = forms.TypedChoiceField(choices=Workout.Intensity.choices, coerce=int, required=False)

    def clean(self):
        values = super().clean()
        if any(self.data.get(key) for key in self.fields):
            for key in ('activity', 'duration_min'):
                if not values.get(key) and key not in self.errors:
                    self.add_error(key, 'Укажите вид активности и длительность.')
        return values


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name']


class HabitSelectionForm(DayForm):
    habits = forms.ModelMultipleChoiceField(label='Выполненные привычки', queryset=Habit.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['habits'].queryset = Habit.objects.filter(user=user)
