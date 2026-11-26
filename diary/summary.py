from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import DailyEntry, Goal, Workout


@login_required
@require_GET
def summary(request):
    period = request.GET.get('period', 'week')
    days = {'week': 7, 'month': 30}.get(period)
    if days is None:
        return JsonResponse({'error': 'Выберите week или month.'}, status=400)

    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    diary = DailyEntry.objects.filter(user=request.user)
    entries = diary.filter(date__range=(start, end))
    averages = entries.aggregate(**{
        field: Avg(field) for field in ('weight_kg', 'sleep_hours', 'calories', 'water_ml', 'mood')
    })
    count = entries.count()
    minutes = Workout.objects.filter(entry__in=entries).aggregate(total=Sum('duration_min'))['total'] or 0
    averages['activity_min'] = minutes / count if count else None
    averages = {key: round(float(value), 2) if value is not None else None for key, value in averages.items()}

    goal = Goal.objects.filter(user=request.user, metric=Goal.Metric.WEIGHT, is_active=True,
                               start_date__lte=end).order_by('-start_date', '-pk').first()
    progress = None
    if goal:
        weight = diary.filter(date__range=(goal.start_date, end), weight_kg__isnull=False).values_list('weight_kg', flat=True).first()
        percent = None
        if weight is not None:
            distance = goal.target_value - goal.start_value
            if distance:
                percent = round(float(max(0, min(100, 100 * (weight - goal.start_value) / distance))), 1)
            else:
                percent = 100 if weight == goal.target_value else 0
        progress = {'start_kg': float(goal.start_value), 'target_kg': float(goal.target_value),
                    'current_kg': float(weight) if weight is not None else None, 'percent': percent}
    from .models import Habit, HabitMark
    from .analysis import analyze
    from django.shortcuts import render

    habits = Habit.objects.filter(user=request.user)
    possible = habits.count() * days
    completed = HabitMark.objects.filter(habit__in=habits, entry__in=entries).count()
    context = {'start': start, 'end': end, 'recorded_days': count, 'averages': averages,
               'weight_goal': progress, 'activity_minutes': minutes, 'completed_marks': completed,
               'possible_marks': possible, 'habit_percent': round(100 * completed / possible, 1) if possible else None}
    if request.resolver_match.url_name == 'statistics':
        context.update(analyze(request.user, start, end))
        return render(request, 'diary/statistics.html', context)
    return JsonResponse(context)
