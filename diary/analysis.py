from datetime import timedelta
from itertools import combinations
from statistics import correlation, mean

from django.db.models import Sum

from .models import DailyEntry


METRICS = {'sleep_hours': 'Сон', 'activity': 'Активность', 'calories': 'Калории', 'delta': 'Изменение веса'}


def analyze(user, start, end):
    rows = list(DailyEntry.objects.filter(user=user, date__range=(start - timedelta(days=1), end))
                .annotate(activity=Sum('workouts__duration_min', default=0))
                .values('date', 'weight_kg', 'sleep_hours', 'activity', 'calories').order_by('date'))
    weights = {r['date']: r['weight_kg'] for r in rows}
    rows = [r for r in rows if r['date'] >= start]
    for row in rows:
        previous = weights.get(row['date'] - timedelta(days=1))
        row['delta'] = row['weight_kg'] - previous if previous is not None and row['weight_kg'] is not None else None
    pairs, notes = [], []
    best_count = 0
    for a, b in combinations(METRICS, 2):
        values = [(float(r[a]), float(r[b])) for r in rows if r[a] is not None and r[b] is not None]
        best_count = max(best_count, len(values))
        if len(values) < 7:
            continue
        x, y = zip(*values)
        if len(set(x)) == 1 or len(set(y)) == 1:
            continue
        coef = correlation(x, y)
        pairs.append({'first': METRICS[a], 'second': METRICS[b], 'r': coef, 'count': len(x)})
        if abs(coef) < 0.3:
            continue
        strength = 'Сильная' if abs(coef) > 0.5 else 'Заметная'
        direction = 'прямая' if coef > 0 else 'обратная'
        note = f'{strength} {direction} связь между показателями «{METRICS[a]}» и «{METRICS[b]}» ({len(x)} дн.).'
        if (a, b) == ('sleep_hours', 'calories'):
            long = [v for h, v in values if h >= 8]
            short = [v for h, v in values if h < 8]
            if long and short:
                diff = mean(long) - mean(short)
                side = 'меньше' if diff < 0 else 'больше'
                note += f' В дни со сном от 8 часов вы съедали в среднем на {abs(diff):.0f} ккал {side}, чем при сне меньше 8 часов.'
        notes.append((abs(coef), note))
    notes.sort(key=lambda item: item[0], reverse=True)
    return {'pairs': pairs, 'notes': [note for _, note in notes[:3]], 'missing': max(0, 7 - best_count)}
