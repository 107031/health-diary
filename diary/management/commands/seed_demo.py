from datetime import timedelta
from decimal import Decimal
from random import Random
from secrets import token_urlsafe

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from diary.models import ActivityType, DailyEntry, Goal, Profile, Workout


class Command(BaseCommand):
    help = 'Создать демопользователя и заполнить дневник за последние 30 дней.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='health_diary_demo')

    @transaction.atomic
    def handle(self, *args, username, **options):
        user, new = get_user_model().objects.get_or_create(username=username)
        if new:
            password = token_urlsafe(12)
            user.set_password(password)
            user.save(update_fields=['password'])
            self.stdout.write(f'Демонстрационный вход: {username}, пароль: {password}')
        Profile.objects.get_or_create(user=user)
        first = timezone.localdate() - timedelta(days=29)
        walk, _ = ActivityType.objects.get_or_create(name='Прогулка')
        count = 0
        for i in range(30):
            day = first + timedelta(days=i)
            rng = Random(day.toordinal())
            sleep = rng.randint(60, 91)
            minutes = max(0, sleep - 45 + rng.randint(-10, 10))
            entry, created = DailyEntry.objects.get_or_create(user=user, date=day, defaults={
                'sleep_hours': Decimal(sleep) / 10, 'weight_kg': Decimal(800 - i + rng.randint(-2, 2)) / 10,
                'calories': 3200 - 14 * sleep + rng.randint(-60, 60), 'mood': rng.randint(2, 5),
                'water_ml': rng.randrange(1200, 2500, 100),
            })
            if created:
                count += 1
                Workout.objects.create(entry=entry, activity_type=walk, duration_min=minutes)
        if count and not user.goals.filter(metric=Goal.Metric.WEIGHT).exists():
            Goal.objects.create(user=user, metric=Goal.Metric.WEIGHT, start_date=first,
                                deadline=first + timedelta(days=60), start_value=80, target_value=75)
        self.stdout.write(f'Добавлено дней: {count}. Уже были: {30 - count}.')
