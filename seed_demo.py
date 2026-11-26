"""Запуск: python seed_demo.py имя_тестового_пользователя"""
import argparse
import os
from datetime import timedelta
from decimal import Decimal
from random import Random

import django


def main():
    parser = argparse.ArgumentParser(description='Добавить данные дневника за последние 30 дней.')
    parser.add_argument('username', help='Логин зарегистрированного тестового пользователя')
    args = parser.parse_args()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from django.contrib.auth import get_user_model
    from django.db import transaction
    from django.utils import timezone
    from diary.models import ActivityType, DailyEntry, Goal, Workout

    user = get_user_model().objects.filter(username=args.username).first()
    if user is None:
        parser.error('Сначала зарегистрируйте тестового пользователя.')
    first = timezone.localdate() - timedelta(days=29)
    added = 0
    with transaction.atomic():
        for offset in range(30):
            day = first + timedelta(days=offset)
            rng = Random(day.toordinal())
            entry, created = DailyEntry.objects.get_or_create(user=user, date=day, defaults={
                'sleep_hours': Decimal(rng.randint(60, 87)) / 10,
                'weight_kg': Decimal(800 - offset + rng.randint(-2, 2)) / 10,
                'calories': rng.randint(1800, 2400), 'water_ml': rng.choice([1500, 1750, 2000]),
                'mood': rng.randint(2, 5),
            })
            if created:
                added += 1
                if offset % 4:
                    walk, _ = ActivityType.objects.get_or_create(name='Прогулка')
                    Workout.objects.create(entry=entry, activity_type=walk, duration_min=rng.randint(20, 60))
        if added and not Goal.objects.filter(user=user, metric=Goal.Metric.WEIGHT).exists():
            Goal.objects.create(user=user, metric=Goal.Metric.WEIGHT, start_value=80, target_value=75,
                                start_date=first, deadline=first + timedelta(days=60))
    print(f'Добавлено дней: {added}. Уже были в дневнике: {30 - added}.')


if __name__ == '__main__':
    main()
