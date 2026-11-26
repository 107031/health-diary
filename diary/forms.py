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
    weight_kg = forms.DecimalField(label='Вес, кг', min_value=20, max_value=300, decimal_places=1, required=False)
    calories = forms.IntegerField(label='Калории, ккал', min_value=0, max_value=10000, required=False)

    class Meta:
        model = DailyEntry
        fields = ['date', 'sleep_hours', 'weight_kg', 'calories', 'water_ml', 'mood', 'note']


class ActivityForm(forms.Form):
    activity = forms.CharField(label='Вид активности', max_length=50, required=False)
    duration_min = forms.IntegerField(label='Активность, мин', min_value=0, max_value=1440, required=False)
    intensity = forms.TypedChoiceField(label='Интенсивность', choices=[('', '—'), *Workout.Intensity.choices], coerce=int, required=False)

    def clean(self):
        values = super().clean()
        if (values.get('activity') or values.get('intensity')) and 'duration_min' not in self.errors and values.get('duration_min') is None:
            self.add_error('duration_min', 'Укажите длительность в минутах.')
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
