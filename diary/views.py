from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

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
@require_http_methods(['GET', 'POST'])
def save_day(request):
    html = request.method == 'GET' or 'browser_form' in request.POST
    data = request.POST if request.method == 'POST' else None
    day_picker = DayForm(request.GET or None, initial={'date': timezone.localdate()})
    day = day_picker.cleaned_data['date'] if day_picker.is_valid() else timezone.localdate()
    entry = DailyEntry.objects.filter(user=request.user, date=day).first()
    form = EntryForm(data, instance=entry, initial={'date': day})
    activity = ActivityForm(data)
    marks = HabitSelectionForm(data, user=request.user, initial={
        'date': day, 'habits': entry.completed_habits.all() if entry else [],
    })
    update_marks = html or 'habits' in request.POST
    if data is not None:
        errors = {**form.errors, **activity.errors}
        if update_marks:
            errors.update(marks.errors)
        if not errors:
            day = form.cleaned_data['date']
            defaults = {k: v for k, v in form.cleaned_data.items() if k != 'date' and k in data}
            with transaction.atomic():
                entry, created = DailyEntry.objects.update_or_create(user=request.user, date=day, defaults=defaults)
                minutes = activity.cleaned_data['duration_min']
                if minutes is not None:
                    name = activity.cleaned_data['activity'] or 'Активность'
                    session = entry.workouts.filter(activity_type__name=name).order_by('pk').first()
                    others = entry.workouts.exclude(pk=session.pk if session else None)
                    if minutes + sum(others.values_list('duration_min', flat=True)) > 1440:
                        activity.add_error('duration_min', 'Суммарная активность за день превышает 1440 минут.')
                        transaction.set_rollback(True)
                    else:
                        kind, _ = ActivityType.objects.get_or_create(name=name)
                        session = session or Workout(entry=entry, activity_type=kind)
                        session.duration_min = minutes
                        if activity.cleaned_data['intensity']:
                            session.intensity = activity.cleaned_data['intensity']
                        session.save()
                if not activity.errors and update_marks:
                    entry.completed_habits.set(marks.cleaned_data['habits'])
            if not activity.errors:
                if html:
                    return redirect(f"{reverse('save_day')}?date={day.isoformat()}&saved=1")
                return JsonResponse({'id': entry.pk, 'date': day}, status=201 if created else 200)
            errors.update(activity.errors)
        if not html:
            return JsonResponse({'errors': errors}, status=400)
    return render(request, 'diary/day.html', {'form': form, 'activity': activity, 'marks': marks,
                  'picker': day_picker, 'entry': entry, 'saved': request.GET.get('saved') and not data})


@login_required
def habits(request):
    today = timezone.localdate()
    selector = DayForm(request.GET if request.GET else None, initial={'date': today})
    day = selector.cleaned_data['date'] if selector.is_valid() else today
    personal = Habit.objects.filter(user=request.user)
    action = request.POST.get('action')
    if action == 'delete':
        from django.shortcuts import get_object_or_404
        get_object_or_404(personal, pk=request.POST.get('habit_id')).delete()
        return redirect('habits')
    new_habit = HabitForm(request.POST if action == 'add' else None)
    marks = HabitSelectionForm(request.POST if action == 'mark' else None, user=request.user, initial={
        'date': day, 'habits': personal.filter(completed_days__date=day),
    })
    if new_habit.is_valid():
        _, created = personal.get_or_create(user=request.user, name=new_habit.cleaned_data['name'])
        if created:
            return redirect(request.get_full_path())
        new_habit.add_error('name', 'Такая привычка уже есть.')
    if marks.is_valid():
        day = marks.cleaned_data['date']
        with transaction.atomic():
            entry, _ = DailyEntry.objects.select_for_update().get_or_create(user=request.user, date=day)
            entry.completed_habits.set(marks.cleaned_data['habits'])
        return redirect(f"{reverse('habits')}?date={day.isoformat()}")
    return render(request, 'diary/habits.html', {'selector': selector, 'new_habit': new_habit,
                  'marks': marks, 'personal': personal})
