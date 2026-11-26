from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ActivityForm, DayForm, EntryForm, HabitForm, HabitSelectionForm, RegisterForm
from .models import ActivityType, DailyEntry, Habit, Profile, Workout


@login_required
def index(request):
    return render(request, "diary/index.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect("index")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
@require_POST
def save_day(request):
    form = EntryForm(request.POST)
    activity = ActivityForm(request.POST)
    errors = {**form.errors, **activity.errors}
    if errors:
        return JsonResponse({'errors': errors}, status=400)
    values = form.cleaned_data.copy()
    day = values.pop('date')
    supplied = {name: value for name, value in values.items() if name in request.POST}
    with transaction.atomic():
        entry, created = DailyEntry.objects.update_or_create(user=request.user, date=day, defaults=supplied)
        workout = activity.cleaned_data
        if workout['activity']:
            kind, _ = ActivityType.objects.get_or_create(name=workout['activity'])
            session = entry.workouts.filter(activity_type=kind).order_by('pk').first() or Workout(entry=entry, activity_type=kind)
            session.duration_min = workout['duration_min']
            if workout['intensity']:
                session.intensity = workout['intensity']
            session.save()
    return JsonResponse({'id': entry.pk, 'date': day}, status=201 if created else 200)


@login_required
def habits(request):
    today = timezone.localdate()
    selector = DayForm(request.GET if request.GET else None, initial={'date': today})
    day = selector.cleaned_data['date'] if selector.is_valid() else today
    personal = Habit.objects.filter(user=request.user)
    adding = request.method == 'POST' and request.POST.get('action') == 'add'
    marking = request.method == 'POST' and request.POST.get('action') == 'mark'
    new_habit = HabitForm(request.POST if adding else None)
    marks = HabitSelectionForm(request.POST if marking else None, user=request.user, initial={
        'date': day, 'habits': personal.filter(completed_days__date=day),
    })
    if adding and new_habit.is_valid():
        _, created = personal.get_or_create(user=request.user, name=new_habit.cleaned_data['name'])
        if created:
            return redirect(request.get_full_path())
        new_habit.add_error('name', 'Такая привычка уже есть.')
    if marking and marks.is_valid():
        day = marks.cleaned_data['date']
        with transaction.atomic():
            entry, _ = DailyEntry.objects.select_for_update().get_or_create(user=request.user, date=day)
            entry.completed_habits.set(marks.cleaned_data['habits'])
        return redirect(f"{reverse('habits')}?date={day.isoformat()}")
    return render(request, 'diary/habits.html', {'selector': selector, 'new_habit': new_habit, 'marks': marks})
