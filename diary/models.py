from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    height_cm = models.PositiveSmallIntegerField('рост, см', null=True, blank=True)

    track_sleep = models.BooleanField('сон', default=True)
    track_calories = models.BooleanField('калории', default=True)
    track_water = models.BooleanField('вода', default=True)
    track_activity = models.BooleanField('активность', default=True)
    track_weight = models.BooleanField('вес', default=True)
    track_mood = models.BooleanField('самочувствие', default=True)

    setup_done = models.BooleanField('настройка пройдена', default=False)

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


class Goal(models.Model):
    class Metric(models.TextChoices):
        WEIGHT = 'weight', 'Вес'
        SLEEP = 'sleep', 'Сон'
        WATER = 'water', 'Вода'
        CALORIES = 'calories', 'Калории'
        ACTIVITY = 'activity', 'Активность'
        MOOD = 'mood', 'Самочувствие'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals',
    )
    metric = models.CharField('показатель', max_length=20, choices=Metric.choices)
    start_value = models.DecimalField('начальное значение', max_digits=6, decimal_places=1)
    target_value = models.DecimalField('целевое значение', max_digits=6, decimal_places=1)
    start_date = models.DateField('дата начала')
    deadline = models.DateField('срок')
    is_active = models.BooleanField('активна', default=True)

    class Meta:
        verbose_name = 'цель'
        verbose_name_plural = 'цели'

    def __str__(self):
        return f'{self.get_metric_display()}: {self.target_value} к {self.deadline}'


class DailyEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entries',
    )
    date = models.DateField('дата')

    sleep_hours = models.DecimalField(
        'сон, ч', max_digits=3, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    weight_kg = models.DecimalField(
        'вес, кг', max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(1)],
    )
    calories = models.PositiveIntegerField('калории', null=True, blank=True)
    water_ml = models.PositiveIntegerField('вода, мл', null=True, blank=True)
    mood = models.PositiveSmallIntegerField(
        'самочувствие', null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    note = models.TextField('заметка', blank=True)

    class Meta:
        verbose_name = 'запись дня'
        verbose_name_plural = 'записи дней'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='one_entry_per_day'),
        ]

    def __str__(self):
        return f'{self.user.username} — {self.date}'


class ActivityType(models.Model):
    name = models.CharField('название', max_length=50, unique=True)
    kcal_per_hour = models.PositiveIntegerField('ккал в час', null=True, blank=True)

    class Meta:
        verbose_name = 'вид активности'
        verbose_name_plural = 'виды активности'
        ordering = ['name']

    def __str__(self):
        return self.name


class Workout(models.Model):
    class Intensity(models.IntegerChoices):
        LOW = 1, 'Лёгкая'
        MEDIUM = 2, 'Средняя'
        HIGH = 3, 'Высокая'

    entry = models.ForeignKey(
        DailyEntry,
        on_delete=models.CASCADE,
        related_name='workouts',
    )
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.PROTECT,
        verbose_name='вид',
    )
    duration_min = models.PositiveSmallIntegerField('длительность, мин')
    intensity = models.PositiveSmallIntegerField(
        'интенсивность', choices=Intensity.choices, default=Intensity.MEDIUM,
    )

    class Meta:
        verbose_name = 'тренировка'
        verbose_name_plural = 'тренировки'

    def __str__(self):
        return f'{self.activity_type} {self.duration_min} мин'