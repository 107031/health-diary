from datetime import timedelta
from itertools import combinations
from statistics import correlation, mean

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from .models import DailyEntry


METRICS = {
    'sleep_hours': 'Сон',
    'activity': 'Записанная активность',
    'calories': 'Калории',
    'weight_kg': 'Вес',
}
MIN_DAYS = 5


def analyze(rows):
    pairs = []
    notes = []
    for first, second in combinations(METRICS, 2):
        samples = [(float(row[first]), float(row[second])) for row in rows
                   if row[first] is not None and row[second] is not None]
        result = {'first': METRICS[first], 'second': METRICS[second], 'count': len(samples)}
        if len(samples) < MIN_DAYS:
            result['reason'] = 'Мало записей'
        else:
            x, y = zip(*samples)
            if len(set(x)) == 1 or len(set(y)) == 1:
                result['reason'] = 'Один из показателей не менялся'
            else:
                r = correlation(x, y)
                result['r'] = f'{r:.2f}'.replace('.', ',')
                if abs(r) >= 0.5:
                    direction = 'выше' if r > 0 else 'ниже'
                    notes.append((abs(r), f'{METRICS[first]} и {METRICS[second].lower()}: когда первый показатель был выше, второй обычно был {direction}. Дней для сравнения — {len(samples)}.'))
        pairs.append(result)
    notes.sort(key=lambda item: item[0], reverse=True)
    observations = [note for _, note in notes[:2]]
    sleep_mood = [(row['sleep_hours'], row['mood']) for row in rows
                 if row['sleep_hours'] is not None and row['mood'] is not None]
    longer = [mood for sleep, mood in sleep_mood if sleep >= 8]
    shorter = [mood for sleep, mood in sleep_mood if sleep < 8]
    if min(len(longer), len(shorter)) >= 3:
        text = (f'В дни со сном от 8 часов средняя оценка самочувствия — {mean(longer):.1f} из 5 '
                f'({len(longer)} дн.), а при сне меньше 8 часов — {mean(shorter):.1f} из 5 ({len(shorter)} дн.).')
        observations.insert(0, text.replace('.', ',', 1).replace(f'{mean(shorter):.1f}', f'{mean(shorter):.1f}'.replace('.', ',')))
    return pairs, observations


@login_required
def observations(request):
    end = timezone.localdate()
    start = end - timedelta(days=29)
    rows = list(DailyEntry.objects.filter(user=request.user, date__range=(start, end))
                .annotate(activity=Sum('workouts__duration_min', default=0))
                .values('sleep_hours', 'activity', 'calories', 'weight_kg', 'mood'))
    pairs, notes = analyze(rows)
    return render(request, 'diary/observations.html', {
        'start': start, 'end': end, 'pairs': pairs, 'notes': notes, 'count': len(rows),
    })
